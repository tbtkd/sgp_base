"""Persistencia SQLite portable, respaldos y migraciones aditivas seguras."""

import os
import re
import sqlite3
import sys
from contextlib import suppress
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from threading import Lock
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import String, cast, literal

from app.core.backup_crypto import (
    BackupSecurityError,
    decrypt_file,
    encrypt_file,
    load_or_create_backup_key,
    temporary_decrypted_path,
)

DATABASE_NAME = "pacientes.db"
BACKUP_GLOBS = ("pacientes_backup_*.sgpnbak", "pacientes_backup_*.db")
BACKUP_NAME_RE = re.compile(r"^pacientes_backup_\d{8}_\d{6}_\d{6}\.(?:sgpnbak|db)$")
REQUIRED_RESTORE_TABLES = {"usuarios", "pacientes", "audit_logs"}
_BACKUP_LOCK = Lock()

# Sólo se permiten sustituciones explícitas, reconocibles y no clínicas. Estas
# estrategias mantienen operativas cuentas de versiones muy antiguas sin
# inventar correos reales ni modificar credenciales.
_REQUIRED_COLUMN_MIGRATIONS = {
    ("usuarios", "nombre"): {
        "default": "'Usuario migrado'",
    },
    ("usuarios", "email"): {
        "default": "'usuario-migrado@local.invalid'",
        "backfill": "unique_user_email",
        "unique_index": "ix_usuarios_email",
    },
    ("usuarios", "apellido_paterno"): {
        "default": "'Por actualizar'",
    },
}


def application_directory() -> Path:
    """Directorio estable de la aplicación; nunca apunta a ``_MEIPASS``."""
    configured = os.environ.get("SGPN_DATA_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def data_directory() -> Path:
    directory = application_directory() / "instance"
    directory.mkdir(parents=True, exist_ok=True)
    with suppress(OSError):
        directory.chmod(0o700)
    return directory


def get_database_path() -> Path:
    directory = data_directory()
    target = directory / DATABASE_NAME
    legacy = directory / "sgpn.db"
    if not target.exists() and legacy.exists() and legacy.stat().st_size > 0:
        temporary = directory / ".pacientes_migration.tmp"
        try:
            source_connection = sqlite3.connect(f"file:{legacy.as_posix()}?mode=ro", uri=True)
            destination_connection = sqlite3.connect(temporary)
            try:
                source_connection.backup(destination_connection)
                integrity = destination_connection.execute("PRAGMA integrity_check").fetchone()
                if not integrity or integrity[0] != "ok":
                    raise sqlite3.DatabaseError("La base legada no superó la comprobación de integridad.")
            finally:
                destination_connection.close()
                source_connection.close()
            temporary.replace(target)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
    return target


def get_backup_directory(database_path=None) -> Path:
    source = Path(database_path or get_database_path()).resolve()
    return (source.parent.parent / "backups").resolve()


def resolve_internal_backup(filename, *, database_path=None, backup_directory=None) -> Path:
    """Resuelve únicamente respaldos con nombre interno dentro de ``backups``."""
    name = str(filename or "")
    if not BACKUP_NAME_RE.fullmatch(name):
        raise ValueError("Nombre de respaldo inválido.")
    directory = Path(backup_directory or get_backup_directory(database_path)).resolve()
    candidate = (directory / name).resolve()
    if candidate.parent != directory or not candidate.is_file():
        raise FileNotFoundError(name)
    return candidate


def verify_sqlite_database(path, *, require_application_tables=True) -> dict:
    """Abre una SQLite en modo lectura y valida integridad y esquema mínimo."""
    source = Path(path).resolve()
    if not source.is_file() or source.stat().st_size == 0:
        raise sqlite3.DatabaseError("El archivo está vacío o no existe.")
    connection = sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True)
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        if not integrity or integrity[0] != "ok":
            raise sqlite3.DatabaseError("La base no superó la comprobación de integridad.")
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        missing = REQUIRED_RESTORE_TABLES - tables if require_application_tables else set()
        if missing:
            raise sqlite3.DatabaseError("El archivo no contiene el esquema mínimo de SGPN.")
        return {"integrity": "ok", "tables": len(tables), "size": source.stat().st_size}
    finally:
        connection.close()


def _backup_paths(directory: Path) -> list[Path]:
    backups = {path.resolve() for pattern in BACKUP_GLOBS for path in directory.glob(pattern)}
    return sorted(backups, key=lambda item: item.stat().st_mtime, reverse=True)


def prune_backups(backup_directory, *, retention=10) -> None:
    """Aplica la retención a copias cifradas y anteriores dentro del directorio autorizado."""
    directory = Path(backup_directory).resolve()
    for old_backup in _backup_paths(directory)[max(1, int(retention)) :]:
        old_backup.unlink(missing_ok=True)


def _decrypt_backup(source: Path, *, database_path, key_path=None) -> Path:
    key, _ = load_or_create_backup_key(database_path=database_path, key_path=key_path)
    temporary = temporary_decrypted_path(source.parent)
    try:
        decrypt_file(source, temporary, key)
        return temporary
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def verify_backup(
    path,
    *,
    database_path=None,
    key_path=None,
    require_application_tables=True,
) -> dict:
    """Comprueba autenticidad criptográfica e integridad SQLite de una copia."""
    source = Path(path).resolve()
    if source.suffix == ".db":
        result = verify_sqlite_database(source, require_application_tables=require_application_tables)
        return {**result, "encrypted": False}
    if source.suffix != ".sgpnbak":
        raise BackupSecurityError("La copia no tiene un formato compatible.")
    target_database = Path(database_path or get_database_path()).resolve()
    temporary = _decrypt_backup(source, database_path=target_database, key_path=key_path)
    try:
        result = verify_sqlite_database(temporary, require_application_tables=require_application_tables)
        return {**result, "encrypted": True}
    finally:
        temporary.unlink(missing_ok=True)


def respaldar_db(database_path=None, *, retention=10, backup_directory=None, key_path=None) -> Path | None:
    """Crea una copia SQLite consistente, la cifra y rota las copias anteriores."""
    source = Path(database_path or get_database_path()).resolve()
    if not source.exists() or source.stat().st_size == 0:
        return None

    target_dir = Path(backup_directory or get_backup_directory(source)).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    with suppress(OSError):
        target_dir.chmod(0o700)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    destination = target_dir / f"pacientes_backup_{timestamp}.sgpnbak"
    temporary = target_dir / f".pacientes_backup_{timestamp}.db.tmp"
    with _BACKUP_LOCK:
        try:
            source_connection = sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True)
            backup_connection = sqlite3.connect(temporary)
            try:
                source_connection.backup(backup_connection)
                backup_connection.commit()
            finally:
                backup_connection.close()
                source_connection.close()
            verify_sqlite_database(temporary, require_application_tables=False)
            key, _ = load_or_create_backup_key(database_path=source, key_path=key_path)
            encrypt_file(temporary, destination, key)
            verify_backup(
                destination,
                database_path=source,
                key_path=key_path,
                require_application_tables=False,
            )
        except Exception:
            destination.unlink(missing_ok=True)
            temporary.unlink(missing_ok=True)
            raise
        finally:
            temporary.unlink(missing_ok=True)

    prune_backups(target_dir, retention=retention)
    return destination


def protect_legacy_backups(database_path=None, *, backup_directory=None, key_path=None) -> dict:
    """Cifra copias SQLite anteriores y elimina cada original sólo tras verificarla."""
    database = Path(database_path or get_database_path()).resolve()
    directory = Path(backup_directory or get_backup_directory(database)).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    key, _ = load_or_create_backup_key(database_path=database, key_path=key_path)
    result = {"protected": 0, "failed": 0, "skipped": 0}
    with _BACKUP_LOCK:
        for source in sorted(directory.glob("pacientes_backup_*.db")):
            destination = source.with_suffix(".sgpnbak")
            if destination.exists():
                result["skipped"] += 1
                continue
            try:
                verify_sqlite_database(source, require_application_tables=False)
                encrypt_file(source, destination, key)
                verify_backup(
                    destination,
                    database_path=database,
                    key_path=key_path,
                    require_application_tables=False,
                )
                source.unlink()
                result["protected"] += 1
            except (OSError, sqlite3.DatabaseError, BackupSecurityError):
                destination.unlink(missing_ok=True)
                result["failed"] += 1
    return result


def restore_sqlite_database(source_backup, destination_database, *, key_path=None) -> None:
    """Restaura atómicamente una copia validada; conserva intacto el destino ante error."""
    source = Path(source_backup).resolve()
    destination = Path(destination_database).resolve()
    decrypted_source = None
    if source.suffix == ".sgpnbak":
        decrypted_source = _decrypt_backup(source, database_path=destination, key_path=key_path)
        source_for_restore = decrypted_source
    elif source.suffix == ".db":
        source_for_restore = source
    else:
        raise BackupSecurityError("La copia no tiene un formato compatible.")
    try:
        verify_sqlite_database(source_for_restore)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(".restore.tmp")
        temporary.unlink(missing_ok=True)
        with _BACKUP_LOCK:
            try:
                source_connection = sqlite3.connect(f"file:{source_for_restore.as_posix()}?mode=ro", uri=True)
                restored_connection = sqlite3.connect(temporary)
                try:
                    source_connection.backup(restored_connection)
                    restored_connection.commit()
                finally:
                    restored_connection.close()
                    source_connection.close()
                verify_sqlite_database(temporary)
                temporary.replace(destination)
            except Exception:
                temporary.unlink(missing_ok=True)
                raise
    finally:
        if decrypted_source is not None:
            decrypted_source.unlink(missing_ok=True)


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _required_column_migration(column):
    return _REQUIRED_COLUMN_MIGRATIONS.get((column.table.name, column.name))


def _apply_required_column_migration(connection, table, column, migration):
    if migration.get("backfill") == "unique_user_email":
        temporary_email = literal("usuario-migrado-") + cast(table.c.id, String) + literal("@local.invalid")
        connection.execute(table.update().values({column.name: temporary_email}))
    index_name = migration.get("unique_index")
    if index_name:
        index = next((candidate for candidate in table.indexes if candidate.name == index_name), None)
        if index is None:
            raise RuntimeError(f"No se encontró la definición del índice requerido {index_name}.")
        index.create(bind=connection, checkfirst=True)


def _sqlite_column_definition(column, dialect) -> str:
    """Genera únicamente definiciones compatibles con ALTER TABLE ADD COLUMN."""
    if column.primary_key:
        raise RuntimeError(f"No es posible agregar dinámicamente la llave primaria {column.name}.")
    column_type = column.type.compile(dialect=dialect)
    definition = f"{_quote_identifier(column.name)} {column_type}"
    if column.server_default is not None:
        default = str(column.server_default.arg)
        normalized = default.strip().strip("()").upper()
        # SQLite no admite valores no constantes (por ejemplo CURRENT_TIMESTAMP)
        # al agregar una columna a una tabla existente. Se fija el instante de
        # migración; los registros posteriores siguen usando el default ORM.
        if normalized == "CURRENT_TIMESTAMP":
            instant = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S.%f")
            default = f"'{instant}'"
        elif normalized == "CURRENT_DATE":
            default = f"'{datetime.now(timezone.utc).date().isoformat()}'"
        elif normalized == "CURRENT_TIME":
            default = f"'{datetime.now(timezone.utc).time().strftime('%H:%M:%S')}'"
        if not column.nullable:
            definition += " NOT NULL"
        definition += f" DEFAULT {default}"
    elif not column.nullable:
        migration = _required_column_migration(column)
        if migration is None:
            raise RuntimeError(
                f"La columna nueva {column.table.name}.{column.name} debe ser nullable, tener DEFAULT "
                "o contar con una estrategia de migración explícita para conservar los datos."
            )
        definition += f" NOT NULL DEFAULT {migration['default']}"
    return definition


def _payments_schema_is_current(db) -> bool:
    with db.engine.connect() as connection:
        tables = set(connection.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'").scalars())
        if "pagos" not in tables:
            return True
        columns = {
            row["name"]: row
            for row in connection.exec_driver_sql("PRAGMA table_info('pagos')").mappings().all()
        }
        required = {
            "monto_centavos",
            "moneda",
            "folio",
            "operation_key",
            "usuario_registro_id",
            "cita_id",
            "estatus",
            "cancelado_at",
            "cancelado_por_id",
            "motivo_cancelacion",
        }
        if not required <= set(columns) or not columns["monto_centavos"]["notnull"]:
            return False
        foreign_keys = connection.exec_driver_sql("PRAGMA foreign_key_list('pagos')").mappings().all()
        on_delete = {row["from"]: str(row["on_delete"]).upper() for row in foreign_keys}
        unique_columns = set()
        for index in connection.exec_driver_sql("PRAGMA index_list('pagos')").mappings().all():
            if not index["unique"]:
                continue
            indexed = connection.exec_driver_sql(
                f"PRAGMA index_info({_quote_identifier(index['name'])})"
            ).mappings().all()
            if len(indexed) == 1:
                unique_columns.add(indexed[0]["name"])
        return (
            on_delete.get("paciente_id") == "RESTRICT"
            and on_delete.get("usuario_registro_id") == "SET NULL"
            and on_delete.get("cita_id") == "SET NULL"
            and on_delete.get("cancelado_por_id") == "SET NULL"
            and {"folio", "operation_key"} <= unique_columns
        )


def _legacy_payment_amount(value):
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        return 0, False
    if amount <= 0 or amount > Decimal("10000000"):
        return 0, False
    return int(amount * 100), True


def _migrate_payments_v110(db, *, logger=None) -> bool:
    """Convierte pagos legados a movimientos monetarios íntegros y trazables."""
    if _payments_schema_is_current(db):
        return False

    connection = db.engine.raw_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.execute("PRAGMA legacy_alter_table=OFF")
        cursor.execute("BEGIN IMMEDIATE")
        cursor.execute("DROP TABLE IF EXISTS pagos_migration_v110")
        cursor.execute(
            """
            CREATE TABLE pagos_migration_v110 (
                id INTEGER NOT NULL PRIMARY KEY,
                paciente_id INTEGER NOT NULL,
                fecha_pago DATE NOT NULL,
                monto FLOAT,
                monto_centavos INTEGER NOT NULL,
                moneda VARCHAR(3) NOT NULL DEFAULT 'MXN',
                concepto VARCHAR(200) NOT NULL,
                metodo_pago VARCHAR(30) NOT NULL,
                folio VARCHAR(40) NOT NULL UNIQUE,
                operation_key VARCHAR(36) NOT NULL UNIQUE,
                usuario_registro_id INTEGER,
                cita_id INTEGER,
                estatus VARCHAR(30) NOT NULL DEFAULT 'vigente',
                cancelado_at DATETIME,
                cancelado_por_id INTEGER,
                motivo_cancelacion VARCHAR(500),
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT ck_pagos_estatus
                    CHECK (estatus IN ('vigente','cancelado','requiere_revision')),
                CONSTRAINT ck_pagos_monto_centavos CHECK (monto_centavos >= 0),
                CONSTRAINT ck_pagos_vigente_monto_positivo
                    CHECK (estatus != 'vigente' OR monto_centavos > 0),
                CONSTRAINT ck_pagos_moneda CHECK (moneda = 'MXN'),
                FOREIGN KEY(paciente_id) REFERENCES pacientes(id) ON DELETE RESTRICT,
                FOREIGN KEY(usuario_registro_id) REFERENCES usuarios(id) ON DELETE SET NULL,
                FOREIGN KEY(cita_id) REFERENCES citas(id) ON DELETE SET NULL,
                FOREIGN KEY(cancelado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL
            )
            """
        )

        cursor.execute("SELECT * FROM pagos ORDER BY id")
        column_names = [item[0] for item in cursor.description]
        rows = [dict(zip(column_names, values, strict=True)) for values in cursor.fetchall()]
        user_ids = {row[0] for row in cursor.execute("SELECT id FROM usuarios").fetchall()}
        appointment_rows = cursor.execute("SELECT id, paciente_id FROM citas").fetchall()
        appointments = {row[0]: row[1] for row in appointment_rows}
        used_folios = set()
        used_operations = set()

        for row in rows:
            payment_id = int(row["id"])
            patient_id = int(row["paciente_id"])
            payment_date = str(row.get("fecha_pago") or datetime.now(timezone.utc).date().isoformat())[:10]
            cents, valid_amount = _legacy_payment_amount(
                row.get("monto_centavos") / 100
                if row.get("monto_centavos") is not None
                else row.get("monto")
            )
            concept = " ".join(str(row.get("concepto") or "").split())[:200]
            raw_method = str(row.get("metodo_pago") or "").strip()
            method = raw_method if raw_method in {"efectivo", "tarjeta", "transferencia", "otro"} else "otro"
            currency = str(row.get("moneda") or "MXN").upper()
            requires_review = not valid_amount or not concept or raw_method != method or currency != "MXN"
            if not concept:
                concept = "Pago legado sin concepto"

            raw_status = str(row.get("estatus") or "vigente")
            if raw_status == "cancelado":
                status = "cancelado"
            elif raw_status == "requiere_revision" or requires_review:
                status = "requiere_revision"
            else:
                status = "vigente"

            compact_date = "".join(character for character in payment_date if character.isdigit())[:8]
            folio = str(row.get("folio") or "").strip()[:40]
            if not folio or folio in used_folios:
                folio = f"PAG-{compact_date or 'LEGADO'}-{payment_id:06d}"
            used_folios.add(folio)

            operation = str(row.get("operation_key") or "").strip()[:36]
            if not operation or operation in used_operations:
                operation = str(uuid5(NAMESPACE_URL, f"sgpn-pago-{payment_id}-{payment_date}"))
            used_operations.add(operation)

            registered_by = row.get("usuario_registro_id")
            registered_by = registered_by if registered_by in user_ids else None
            cancelled_by = row.get("cancelado_por_id")
            cancelled_by = cancelled_by if cancelled_by in user_ids else None
            appointment_id = row.get("cita_id")
            appointment_id = appointment_id if appointments.get(appointment_id) == patient_id else None
            cancelled_at = row.get("cancelado_at") if status == "cancelado" else None
            cancellation_reason = (
                " ".join(str(row.get("motivo_cancelacion") or "").split())[:500]
                if status == "cancelado"
                else None
            )
            if status == "cancelado" and not cancellation_reason:
                cancellation_reason = "Cancelación legada sin motivo registrado"
            created_at = row.get("created_at") or datetime.now(timezone.utc).replace(tzinfo=None).isoformat(" ")

            cursor.execute(
                """
                INSERT INTO pagos_migration_v110 (
                    id, paciente_id, fecha_pago, monto, monto_centavos, moneda, concepto,
                    metodo_pago, folio, operation_key, usuario_registro_id, cita_id, estatus,
                    cancelado_at, cancelado_por_id, motivo_cancelacion, created_at
                ) VALUES (?, ?, ?, ?, ?, 'MXN', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payment_id,
                    patient_id,
                    payment_date,
                    cents / 100,
                    cents,
                    concept,
                    method,
                    folio,
                    operation,
                    registered_by,
                    appointment_id,
                    status,
                    cancelled_at,
                    cancelled_by,
                    cancellation_reason,
                    created_at,
                ),
            )

        cursor.execute("DROP TABLE pagos")
        cursor.execute("ALTER TABLE pagos_migration_v110 RENAME TO pagos")
        for index_name, column_name in (
            ("ix_pagos_paciente_id", "paciente_id"),
            ("ix_pagos_fecha_pago", "fecha_pago"),
            ("ix_pagos_metodo_pago", "metodo_pago"),
            ("ix_pagos_folio", "folio"),
            ("ix_pagos_operation_key", "operation_key"),
            ("ix_pagos_usuario_registro_id", "usuario_registro_id"),
            ("ix_pagos_cita_id", "cita_id"),
            ("ix_pagos_estatus", "estatus"),
            ("ix_pagos_cancelado_por_id", "cancelado_por_id"),
        ):
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON pagos ({column_name})")
        foreign_key_errors = cursor.execute("PRAGMA foreign_key_check").fetchall()
        if foreign_key_errors:
            raise sqlite3.DatabaseError("La migración de pagos produjo llaves foráneas inválidas.")
        integrity = cursor.execute("PRAGMA integrity_check").fetchone()
        if not integrity or integrity[0] != "ok":
            raise sqlite3.DatabaseError("La migración de pagos no superó la comprobación de integridad.")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        # La conexión DBAPI puede volver al pool. Reactivar la validación aquí
        # evita que un checkout posterior reutilice la conexión con FK apagadas.
        with suppress(Exception):
            cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        connection.close()
    if logger:
        logger.info("Migración controlada aplicada; schema=payments_v110")
    return True


def _has_legacy_single_prescription_constraint(db) -> bool:
    with db.engine.connect() as connection:
        indexes = connection.exec_driver_sql("PRAGMA index_list('recetas')").mappings().all()
        for index in indexes:
            if not index["unique"]:
                continue
            columns = connection.exec_driver_sql(
                f"PRAGMA index_info({_quote_identifier(index['name'])})"
            ).mappings().all()
            if [column["name"] for column in columns] == ["valoracion_id"]:
                return True
    return False


def _migrate_prescription_versions(db, *, logger=None) -> bool:
    """Retira la unicidad legada por consulta con una reconstrucción transaccional verificable."""
    if "recetas" not in db.metadata.tables or not _has_legacy_single_prescription_constraint(db):
        return False

    connection = db.engine.raw_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.execute("PRAGMA legacy_alter_table=OFF")
        cursor.execute("BEGIN IMMEDIATE")
        cursor.execute("DROP TABLE IF EXISTS recetas_migration_v16")
        cursor.execute(
            """
            CREATE TABLE recetas_migration_v16 (
                id INTEGER NOT NULL PRIMARY KEY,
                folio VARCHAR(40) NOT NULL UNIQUE,
                valoracion_id INTEGER NOT NULL,
                paciente_id INTEGER NOT NULL,
                profesional_id INTEGER,
                fecha_emision DATE NOT NULL DEFAULT CURRENT_DATE,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                tipo VARCHAR(20) NOT NULL DEFAULT 'original',
                version INTEGER NOT NULL DEFAULT 1,
                estado VARCHAR(20) NOT NULL DEFAULT 'vigente',
                receta_sustituida_id INTEGER,
                motivo_cambio VARCHAR(500),
                sustituida_at DATETIME,
                sustituida_por_id INTEGER,
                paciente_nombre VARCHAR(200) NOT NULL,
                paciente_fecha_nacimiento DATE NOT NULL,
                paciente_genero VARCHAR(30),
                alergias_conocidas TEXT,
                profesional_nombre VARCHAR(200) NOT NULL,
                profesional_cedula VARCHAR(30) NOT NULL,
                profesional_perfil VARCHAR(30) NOT NULL,
                domicilio_profesional VARCHAR(300) NOT NULL,
                nombre_establecimiento VARCHAR(160),
                observaciones TEXT,
                CONSTRAINT uq_recetas_valoracion_version UNIQUE (valoracion_id, version),
                CONSTRAINT uq_recetas_receta_sustituida UNIQUE (receta_sustituida_id),
                CONSTRAINT ck_recetas_tipo CHECK (tipo IN ('original','adicional','sustitucion')),
                CONSTRAINT ck_recetas_estado CHECK (estado IN ('vigente','sustituida')),
                CONSTRAINT ck_recetas_version CHECK (version >= 1),
                FOREIGN KEY(valoracion_id) REFERENCES valoracion_antropometrica (id) ON DELETE RESTRICT,
                FOREIGN KEY(paciente_id) REFERENCES pacientes (id) ON DELETE RESTRICT,
                FOREIGN KEY(profesional_id) REFERENCES usuarios (id) ON DELETE SET NULL,
                FOREIGN KEY(receta_sustituida_id) REFERENCES recetas_migration_v16 (id) ON DELETE RESTRICT,
                FOREIGN KEY(sustituida_por_id) REFERENCES usuarios (id) ON DELETE SET NULL
            )
            """
        )
        cursor.execute(
            """
            INSERT INTO recetas_migration_v16 (
                id, folio, valoracion_id, paciente_id, profesional_id, fecha_emision, created_at,
                tipo, version, estado, receta_sustituida_id, motivo_cambio, sustituida_at,
                sustituida_por_id, paciente_nombre, paciente_fecha_nacimiento, paciente_genero,
                alergias_conocidas, profesional_nombre, profesional_cedula, profesional_perfil,
                domicilio_profesional, nombre_establecimiento, observaciones
            ) SELECT
                id, folio, valoracion_id, paciente_id, profesional_id, fecha_emision, created_at,
                tipo, version, estado, receta_sustituida_id, motivo_cambio, sustituida_at,
                sustituida_por_id, paciente_nombre, paciente_fecha_nacimiento, paciente_genero,
                alergias_conocidas, profesional_nombre, profesional_cedula, profesional_perfil,
                domicilio_profesional, nombre_establecimiento, observaciones
            FROM recetas
            """
        )
        cursor.execute("DROP TABLE recetas")
        cursor.execute("ALTER TABLE recetas_migration_v16 RENAME TO recetas")
        for name, column in (
            ("ix_recetas_folio", "folio"),
            ("ix_recetas_valoracion_id", "valoracion_id"),
            ("ix_recetas_paciente_id", "paciente_id"),
            ("ix_recetas_profesional_id", "profesional_id"),
            ("ix_recetas_fecha_emision", "fecha_emision"),
            ("ix_recetas_receta_sustituida_id", "receta_sustituida_id"),
        ):
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {name} ON recetas ({column})")
        if cursor.execute("PRAGMA foreign_key_check").fetchone():
            raise sqlite3.IntegrityError("La migración de recetas produjo referencias inválidas.")
        integrity = cursor.execute("PRAGMA integrity_check").fetchone()
        if not integrity or integrity[0] != "ok":
            raise sqlite3.DatabaseError("La migración de recetas no superó la comprobación de integridad.")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        with suppress(Exception):
            cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        connection.close()
    if logger:
        logger.info("Migración controlada aplicada; constraint=recetas_multiple_versions")
    return True


def _has_daily_consultation_sequence(db) -> bool:
    """Comprueba la unicidad global de ``(fecha, numero_cita)`` en SQLite."""
    with db.engine.connect() as connection:
        tables = set(
            connection.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'").scalars()
        )
        if "valoracion_antropometrica" not in tables:
            return False
        indexes = connection.exec_driver_sql(
            "PRAGMA index_list('valoracion_antropometrica')"
        ).mappings().all()
        for index in indexes:
            if not index["unique"]:
                continue
            columns = connection.exec_driver_sql(
                f"PRAGMA index_info({_quote_identifier(index['name'])})"
            ).mappings().all()
            if [column["name"] for column in columns] == ["fecha", "numero_cita"]:
                return True
    return False


def _migrate_daily_consultation_sequence(db, *, logger=None) -> bool:
    """Normaliza turnos legados y garantiza un consecutivo único para cada fecha.

    El orden histórico se determina por fecha, momento de creación e identificador.
    No se elimina ninguna consulta ni se modifica su fecha.
    """
    if _has_daily_consultation_sequence(db):
        return False

    connection = db.engine.raw_connection()
    cursor = connection.cursor()
    try:
        table = cursor.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='valoracion_antropometrica'"
        ).fetchone()
        if not table:
            return False
        cursor.execute("BEGIN IMMEDIATE")
        rows = cursor.execute(
            """
            SELECT id, fecha
            FROM valoracion_antropometrica
            ORDER BY fecha ASC, COALESCE(created_at, '') ASC, id ASC
            """
        ).fetchall()
        # Los valores temporales negativos evitan colisiones con la restricción
        # legada por paciente mientras se reconstruye cada secuencia diaria.
        cursor.execute("UPDATE valoracion_antropometrica SET numero_cita = -(ABS(id) + 1)")
        counters = {}
        for assessment_id, assessment_date in rows:
            counters[assessment_date] = counters.get(assessment_date, 0) + 1
            cursor.execute(
                "UPDATE valoracion_antropometrica SET numero_cita=? WHERE id=?",
                (counters[assessment_date], assessment_id),
            )
        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uq_valoracion_fecha_numero_cita
            ON valoracion_antropometrica (fecha, numero_cita)
            """
        )
        integrity = cursor.execute("PRAGMA integrity_check").fetchone()
        if not integrity or integrity[0] != "ok":
            raise sqlite3.DatabaseError("La migración de turnos diarios no superó la comprobación de integridad.")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()
    if logger:
        logger.info("Migración controlada aplicada; constraint=consultation_daily_sequence")
    return True


def init_db(db, *, logger=None) -> list[str]:
    """Crea tablas, añade columnas y ejecuta migraciones de restricciones versionadas."""
    db.create_all()
    applied = []
    if _migrate_payments_v110(db, logger=logger):
        applied.append("pagos.schema.v110")
    with db.engine.begin() as connection:
        dialect = connection.dialect
        existing_tables = set(connection.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'").scalars())
        for table in db.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue
            pragma = connection.exec_driver_sql(f"PRAGMA table_info({_quote_identifier(table.name)})").mappings()
            existing_columns = {row["name"] for row in pragma}
            if "id" in table.c and "id" not in existing_columns:
                raise RuntimeError(f"Esquema incompatible: {table.name} no contiene su identificador primario.")
            for column in table.columns:
                if column.name in existing_columns:
                    continue
                definition = _sqlite_column_definition(column, dialect)
                connection.exec_driver_sql(
                    f"ALTER TABLE {_quote_identifier(table.name)} ADD COLUMN {definition}"
                )
                migration = _required_column_migration(column)
                if migration:
                    _apply_required_column_migration(connection, table, column, migration)
                existing_columns.add(column.name)
                applied.append(f"{table.name}.{column.name}")
    if logger and applied:
        logger.info("Migración aditiva aplicada; columns=%s", ",".join(applied))
    if _migrate_prescription_versions(db, logger=logger):
        applied.append("recetas.constraint.multiple_versions")
    if _migrate_daily_consultation_sequence(db, logger=logger):
        applied.append("valoracion.constraint.daily_sequence")
    return applied
