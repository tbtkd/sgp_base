import re
import sqlite3
from pathlib import Path

import pytest

from app import create_app
from app import db_orm as db
from app.db import restore_sqlite_database, verify_sqlite_database
from app.models.usuario import Usuario
from tests.conftest import csrf_from


@pytest.fixture()
def continuity_app(tmp_path):
    database = tmp_path / "instance" / "pacientes.db"
    backups = tmp_path / "backups"
    database.parent.mkdir()
    application = create_app(
        "testing",
        {
            "SERVER_NAME": "localhost",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database}",
            "BACKUP_DATABASE_PATH": database,
            "BACKUP_DIRECTORY": backups,
            "BACKUP_AFTER_CRITICAL_MUTATION": True,
            "AUTO_BACKUP_DATABASE": False,
            "WTF_CSRF_ENABLED": True,
        },
    )
    with application.app_context():
        db.drop_all()
        db.create_all()
        admin = Usuario(
            username="administrator", nombre="Admin", apellido_paterno="Continuidad",
            email="admin-continuity@example.test", rol="admin", status="activo",
        )
        admin.set_password("StrongPass!2026")
        reception = Usuario(
            username="reception", nombre="Recepcion", apellido_paterno="Pruebas",
            email="reception-continuity@example.test", rol="recepcion", status="activo",
        )
        reception.set_password("ReceptionPass!2026")
        db.session.add_all([admin, reception])
        db.session.commit()
    yield application
    with application.app_context():
        db.session.remove()
        db.engine.dispose()


def _login(client, username="administrator", password="StrongPass!2026"):
    token = csrf_from(client.get("/login"))
    return client.post("/login", data={"username": username, "password": password, "csrf_token": token})


def _backup_names(app):
    directory = Path(app.config["BACKUP_DIRECTORY"])
    return {path.name for path in directory.glob("pacientes_backup_*.db")}


def test_csp_is_local_nonce_based_and_templates_have_no_executable_attributes(app, client, login):
    response = client.get("/login")
    csp = response.headers["Content-Security-Policy"]
    nonce_match = re.search(r"script-src 'self' 'nonce-([^']+)'", csp)
    assert nonce_match
    assert "unsafe-inline" not in csp
    assert "http:" not in csp and "https:" not in csp
    assert "script-src-attr 'none'" in csp
    assert "style-src-attr 'none'" in csp
    login()
    authenticated = client.get("/")
    authenticated_csp = authenticated.headers["Content-Security-Policy"]
    authenticated_nonce = re.search(r"script-src 'self' 'nonce-([^']+)'", authenticated_csp).group(1)
    assert authenticated_nonce != nonce_match.group(1)
    inline_tags = re.findall(
        r"<(?:script|style)(?![^>]*\bsrc=)[^>]*>", authenticated.get_data(as_text=True), flags=re.IGNORECASE
    )
    assert inline_tags
    assert all(f'nonce="{authenticated_nonce}"' in tag for tag in inline_tags)

    root = Path(__file__).parents[1]
    template_paths = sorted((root / "app/templates").rglob("*.html"))
    template_sources = []
    unsafe_attributes = []
    attribute_pattern = re.compile(
        r"\b(?:onclick|onchange|onsubmit|onmouseover|onmouseout|style)\s*=",
        flags=re.IGNORECASE,
    )
    for path in template_paths:
        source = path.read_text(encoding="utf-8")
        template_sources.append(source)
        for match in attribute_pattern.finditer(source):
            line = source.count("\n", 0, match.start()) + 1
            attribute = match.group(0).split("=", maxsplit=1)[0].strip()
            unsafe_attributes.append(f"{path.relative_to(root)}:{line} ({attribute})")
    assert not unsafe_attributes, (
        "Se encontraron atributos que la política de seguridad no permite:\n"
        + "\n".join(unsafe_attributes)
        + "\nSi actualizaste sobre una carpeta anterior, extrae la entrega completa en una carpeta nueva y vacía."
    )
    templates = "\n".join(template_sources)
    assert not re.search(r"(?:src|href)=[\"']https?://", templates)
    assert (root / "app/static/css/utilities.css").stat().st_size > 5_000
    assert (root / "app/static/css/icons.css").stat().st_size > 1_000
    assert "window.Swal = localSwal" in (root / "app/static/js/alertas.js").read_text(encoding="utf-8")
    utilities = (root / "app/static/css/utilities.css").read_text(encoding="utf-8")
    for selector in (".bg-opacity-50", ".max-h-36", ".mx-auto", ".sm\\:w-auto", ".text-\\[11px\\]"):
        assert selector in utilities

    user_surface_paths = [
        *template_paths,
        *(root / "app/static/js").rglob("*.js"),
        *(root / "app/controllers").rglob("*.py"),
        *(root / "app/core").rglob("*.py"),
    ]
    user_surface = "\n".join(path.read_text(encoding="utf-8") for path in user_surface_paths)
    technical_messages_replaced = (
        "mantener la trazabilidad",
        "movimientos íntegros",
        "Registros legados no sumados",
        "Registro migrado",
        "Error interno del servidor",
        "El servidor volverá a validar",
        "validan fisiológicamente en el servidor",
        "Respaldo íntegro",
        "base activa",
        "vuelve a autenticarte",
        "identificador de la operación",
        "relación de compresión",
        "contenido descomprimido",
        "recetas emitidas e inmutables",
    )
    for old_message in technical_messages_replaced:
        assert old_message not in user_surface


def test_database_verification_accepts_sgpn_and_rejects_corrupt_file(continuity_app, tmp_path):
    result = verify_sqlite_database(continuity_app.config["BACKUP_DATABASE_PATH"])
    assert result["integrity"] == "ok"
    corrupt = tmp_path / "corrupt.db"
    corrupt.write_bytes(b"not-a-sqlite-database")
    with pytest.raises(sqlite3.DatabaseError):
        verify_sqlite_database(corrupt)


def test_atomic_restore_rejects_corrupt_source_without_changing_destination(continuity_app, tmp_path):
    destination = Path(continuity_app.config["BACKUP_DATABASE_PATH"])
    before = destination.read_bytes()
    corrupt = tmp_path / "corrupt.db"
    corrupt.write_bytes(b"invalid")
    with pytest.raises(sqlite3.DatabaseError):
        restore_sqlite_database(corrupt, destination)
    assert destination.read_bytes() == before


def test_successful_critical_mutation_creates_backup_but_rejected_one_does_not(continuity_app):
    client = continuity_app.test_client()
    assert _login(client).status_code == 302
    with continuity_app.app_context():
        target_id = Usuario.find_by_username("reception").id
        own_id = Usuario.find_by_username("administrator").id
    before = _backup_names(continuity_app)
    page = client.get("/usuarios")
    changed = client.post(
        f"/usuarios/{target_id}/cambiar-estatus",
        headers={"X-CSRFToken": csrf_from(page)},
    )
    assert changed.status_code == 200
    assert changed.headers["X-SGPN-Backup"] == "created"
    with continuity_app.app_context():
        updated = db.session.get(Usuario, target_id)
        assert updated.status == "inactivo"
        assert updated.auth_version == 1
    after_success = _backup_names(continuity_app)
    assert len(after_success - before) == 1
    rejected = client.post(
        f"/usuarios/{own_id}/cambiar-estatus",
        headers={"X-CSRFToken": csrf_from(client.get('/usuarios'))},
    )
    assert rejected.status_code == 400
    assert _backup_names(continuity_app) == after_success


def test_backup_failure_does_not_rollback_successful_mutation(continuity_app, tmp_path):
    client = continuity_app.test_client()
    _login(client)
    with continuity_app.app_context():
        target_id = Usuario.find_by_username("reception").id
    invalid_directory = tmp_path / "not-a-directory"
    invalid_directory.write_text("blocked", encoding="utf-8")
    continuity_app.config["BACKUP_DIRECTORY"] = invalid_directory
    response = client.post(
        f"/usuarios/{target_id}/cambiar-estatus",
        headers={"X-CSRFToken": csrf_from(client.get('/usuarios'))},
    )
    assert response.status_code == 200
    assert response.headers["X-SGPN-Backup"] == "failed"
    with continuity_app.app_context():
        assert Usuario.find_by_username("reception").status == "inactivo"


def test_backup_admin_requires_auth_role_and_csrf(continuity_app):
    anonymous = continuity_app.test_client()
    assert anonymous.get("/administracion/respaldos").status_code == 302
    reception = continuity_app.test_client()
    _login(reception, "reception", "ReceptionPass!2026")
    assert reception.get("/administracion/respaldos").status_code == 403
    admin = continuity_app.test_client()
    _login(admin)
    assert admin.get("/administracion/respaldos").status_code == 200
    assert admin.post("/administracion/respaldos/crear").status_code == 400


def test_backup_create_verify_download_and_invalid_filename(continuity_app):
    client = continuity_app.test_client()
    _login(client)
    token = csrf_from(client.get("/administracion/respaldos"))
    assert client.post("/administracion/respaldos/crear", data={"csrf_token": token}).status_code == 302
    names = _backup_names(continuity_app)
    assert len(names) == 1
    filename = names.pop()
    page = client.get("/administracion/respaldos")
    verified = client.post(
        f"/administracion/respaldos/{filename}/verificar",
        data={"csrf_token": csrf_from(page)},
    )
    assert verified.status_code == 302
    downloaded = client.get(f"/administracion/respaldos/{filename}/descargar")
    assert downloaded.status_code == 200
    assert downloaded.headers["Content-Disposition"].startswith("attachment")
    assert downloaded.headers["Cache-Control"].startswith("no-store")
    assert client.get("/administracion/respaldos/not-a-backup.db/descargar").status_code == 404


def test_corrupt_backup_and_invalid_restore_confirmations_are_rejected(continuity_app):
    client = continuity_app.test_client()
    _login(client)
    directory = Path(continuity_app.config["BACKUP_DIRECTORY"])
    directory.mkdir(exist_ok=True)
    corrupt = directory / "pacientes_backup_20260825_120000_000001.db"
    corrupt.write_bytes(b"corrupt")
    page = client.get("/administracion/respaldos")
    token = csrf_from(page)
    assert client.post(
        f"/administracion/respaldos/{corrupt.name}/verificar", data={"csrf_token": token}
    ).status_code == 422
    for password, phrase in [("WrongPass!2026", "RESTAURAR"), ("StrongPass!2026", "restaurar")]:
        page = client.get("/administracion/respaldos")
        response = client.post(
            f"/administracion/respaldos/{corrupt.name}/restaurar",
            data={"csrf_token": csrf_from(page), "admin_password": password, "confirmation_phrase": phrase},
        )
        assert response.status_code == 422
    page = client.get("/administracion/respaldos")
    damaged = client.post(
        f"/administracion/respaldos/{corrupt.name}/restaurar",
        data={"csrf_token": csrf_from(page), "admin_password": "StrongPass!2026", "confirmation_phrase": "RESTAURAR"},
    )
    assert damaged.status_code == 422


def test_valid_restore_reverts_data_creates_safety_copy_and_logs_out(continuity_app):
    client = continuity_app.test_client()
    _login(client)
    token = csrf_from(client.get("/administracion/respaldos"))
    client.post("/administracion/respaldos/crear", data={"csrf_token": token})
    source = next(iter(_backup_names(continuity_app)))
    with continuity_app.app_context():
        admin = Usuario.find_by_username("administrator")
        admin.nombre = "Nombre posterior"
        db.session.commit()
    before = _backup_names(continuity_app)
    page = client.get("/administracion/respaldos")
    restored = client.post(
        f"/administracion/respaldos/{source}/restaurar",
        data={
            "csrf_token": csrf_from(page),
            "admin_password": "StrongPass!2026",
            "confirmation_phrase": "RESTAURAR",
        },
    )
    assert restored.status_code == 302
    assert restored.headers["Location"].endswith("/login")
    assert client.get("/").status_code == 302
    assert len(_backup_names(continuity_app) - before) == 1
    with continuity_app.app_context():
        db.session.expire_all()
        assert Usuario.find_by_username("administrator").nombre == "Admin"
