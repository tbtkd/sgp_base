"""Persistencia SQLite portable, respaldos y migraciones aditivas seguras."""

import os
import sqlite3
import sys
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import String, cast, literal

DATABASE_NAME = "pacientes.db"
BACKUP_GLOB = "pacientes_backup_*.db"

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


def respaldar_db(database_path=None, *, retention=10, backup_directory=None) -> Path | None:
    """Crea un respaldo consistente con la API nativa de SQLite y rota copias."""
    source = Path(database_path or get_database_path()).resolve()
    if not source.exists() or source.stat().st_size == 0:
        return None

    target_dir = Path(backup_directory or (source.parent.parent / "backups")).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    with suppress(OSError):
        target_dir.chmod(0o700)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    destination = target_dir / f"pacientes_backup_{timestamp}.db"
    temporary = destination.with_suffix(".tmp")
    try:
        source_connection = sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True)
        backup_connection = sqlite3.connect(temporary)
        try:
            source_connection.backup(backup_connection)
            integrity = backup_connection.execute("PRAGMA integrity_check").fetchone()
            if not integrity or integrity[0] != "ok":
                raise sqlite3.DatabaseError("El respaldo no superó la comprobación de integridad.")
            backup_connection.commit()
        finally:
            backup_connection.close()
            source_connection.close()
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise

    backups = sorted(target_dir.glob(BACKUP_GLOB), key=lambda item: item.stat().st_mtime, reverse=True)
    for old_backup in backups[max(1, int(retention)) :]:
        old_backup.unlink(missing_ok=True)
    return destination


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
