import re
from datetime import timedelta

import pytest

from app import db_orm as db
from app.core.audit import AuditLog
from app.core.password_recovery import reset_password_offline
from app.core.time import utcnow_naive
from app.core.validators import ValidationError
from app.models.usuario import Usuario
from tests.conftest import csrf_from


def test_clinical_routes_require_authentication(client):
    for path in ["/", "/pacientes/activos", "/historial-clinico/", "/valoraciones/", "/plantillas-mensajes/"]:
        response = client.get(path)
        assert response.status_code == 302
        assert "/login" in response.location


def test_csrf_rejects_unsafe_request(client):
    response = client.post("/login", data={"username": "administrator", "password": "StrongPass!2026"})
    assert response.status_code == 400
    assert b"contrase" not in response.data.lower()


def test_security_headers_are_present(client):
    response = client.get("/login")
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert response.headers["Cache-Control"].startswith("no-store")
    assert response.headers["X-Request-ID"]


def test_login_logout_and_audit(app, client, login):
    response = login()
    assert response.status_code == 302
    assert response.location.endswith("/")
    with app.app_context():
        assert AuditLog.query.filter_by(action="LOGIN", outcome="success").count() == 1
    token = csrf_from(client.get("/"))
    response = client.post("/logout", data={"csrf_token": token})
    assert response.status_code == 302
    assert response.location.endswith("/login")


def test_temporary_migration_email_displays_update_warning(app, client, login):
    with app.app_context():
        user = Usuario.find_by_username("administrator")
        user.email = "usuario-migrado-1@local.invalid"
        db.session.commit()
    assert login().status_code == 302
    response = client.get("/", follow_redirects=True)
    assert b"correo temporal de migraci" in response.data


def test_inactive_user_cannot_login(app, client):
    with app.app_context():
        user = Usuario.find_by_username("administrator")
        user.status = "inactivo"
        db.session.commit()
    token = csrf_from(client.get("/login"))
    response = client.post(
        "/login",
        data={"username": "administrator", "password": "StrongPass!2026", "csrf_token": token},
        follow_redirects=True,
    )
    assert b"incorrectos" in response.data


def test_account_is_locked_after_five_failures(app, client):
    token = csrf_from(client.get("/login"))
    for _ in range(5):
        response = client.post(
            "/login",
            data={"username": "administrator", "password": "WrongPass!000", "csrf_token": token},
        )
        assert response.status_code == 200
    blocked = client.post(
        "/login",
        data={"username": "administrator", "password": "WrongPass!000", "csrf_token": token},
    )
    assert blocked.status_code == 429
    with app.app_context():
        user = Usuario.find_by_username("administrator")
        assert user.locked_until is not None
        assert user.locked_until > utcnow_naive()
        user.locked_until = utcnow_naive() - timedelta(seconds=1)
        db.session.commit()


def test_setup_is_disabled_after_first_user(client):
    response = client.get("/setup")
    assert response.status_code == 302
    assert response.location.endswith("/login")


def test_assistant_role_cannot_access_clinical_or_user_admin(app, client, login):
    with app.app_context():
        assistant = Usuario(
            username="assistant",
            nombre="Ana",
            apellido_paterno="Apoyo",
            email="assistant@example.test",
            rol="recepcion",
            status="activo",
        )
        assistant.set_password("AssistantPass!2026")
        db.session.add(assistant)
        db.session.commit()
    assert login("assistant", "AssistantPass!2026").status_code == 302
    assert client.get("/pacientes/activos").status_code == 200
    dashboard = client.get("/").get_data(as_text=True)
    assert 'data-kpi="consultas-pendientes">—</strong>' in dashboard
    assert "Acceso clínico restringido" in dashboard
    assert "Sin consulta reciente" not in dashboard
    assert "Expedientes pendientes" not in dashboard
    assert "Iniciar consulta" not in dashboard
    assert 'aria-label="Registrar una nueva consulta"' not in dashboard
    assert dashboard.count('class="dashboard-kpi-action"') == 2
    assert client.get("/valoraciones/").status_code == 403
    assert client.get("/historial-clinico/").status_code == 403
    assert client.get("/usuarios").status_code == 403


def test_recovery_help_is_public_and_does_not_enumerate_accounts(client):
    response = client.get("/recuperar-acceso")
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "python run.py --reset-password NOMBRE_USUARIO" in page
    assert "name=\"username\"" not in page


def test_user_can_change_password_and_other_credentials_stop_working(app, client, login):
    assert login().status_code == 302
    page = client.get("/mi-cuenta/cambiar-contrasena")
    token = csrf_from(page)
    rejected = client.post(
        "/mi-cuenta/cambiar-contrasena",
        data={
            "csrf_token": token,
            "current_password": "WrongPass!2026",
            "new_password": "N3w-Secure!Pass2026",
            "confirm_password": "N3w-Secure!Pass2026",
        },
    )
    assert rejected.status_code == 422

    page = client.get("/mi-cuenta/cambiar-contrasena")
    changed = client.post(
        "/mi-cuenta/cambiar-contrasena",
        data={
            "csrf_token": csrf_from(page),
            "current_password": "StrongPass!2026",
            "new_password": "N3w-Secure!Pass2026",
            "confirm_password": "N3w-Secure!Pass2026",
        },
    )
    assert changed.status_code == 302
    assert client.get("/").status_code == 200
    with app.app_context():
        user = Usuario.find_by_username("administrator")
        assert user.check_password("N3w-Secure!Pass2026")
        assert not user.check_password("StrongPass!2026")
        assert user.auth_version == 1
        assert AuditLog.query.filter_by(action="CAMBIAR_CONTRASENA", outcome="success").count() == 1


def test_admin_reset_uses_one_time_password_forces_change_and_invalidates_sessions(app):
    with app.app_context():
        target = Usuario(
            username="doctor-reset",
            nombre="Diego",
            apellido_paterno="Recuperacion",
            email="doctor-reset@example.test",
            rol="medico",
            perfil_profesional="medico_general",
            status="activo",
        )
        target.set_password("DoctorOldPass!2026")
        db.session.add(target)
        db.session.commit()
        target_id = target.id

    target_client = app.test_client()
    token = csrf_from(target_client.get("/login"))
    assert target_client.post(
        "/login",
        data={"username": "doctor-reset", "password": "DoctorOldPass!2026", "csrf_token": token},
    ).status_code == 302

    admin_client = app.test_client()
    token = csrf_from(admin_client.get("/login"))
    assert admin_client.post(
        "/login",
        data={"username": "administrator", "password": "StrongPass!2026", "csrf_token": token},
    ).status_code == 302
    reset_page = admin_client.get(f"/usuarios/{target_id}/restablecer-contrasena")
    denied = admin_client.post(
        f"/usuarios/{target_id}/restablecer-contrasena",
        data={"csrf_token": csrf_from(reset_page), "admin_password": "WrongAdmin!2026"},
    )
    assert denied.status_code == 422

    reset_page = admin_client.get(f"/usuarios/{target_id}/restablecer-contrasena")
    completed = admin_client.post(
        f"/usuarios/{target_id}/restablecer-contrasena",
        data={"csrf_token": csrf_from(reset_page), "admin_password": "StrongPass!2026"},
    )
    assert completed.status_code == 200
    match = re.search(r'id="temporary-password"[^>]*>([^<]+)</code>', completed.get_data(as_text=True))
    assert match
    temporary_password = match.group(1)
    assert len(temporary_password) >= 12

    stale = target_client.get("/")
    assert stale.status_code == 302
    assert stale.headers["Location"].endswith("/login")
    with app.app_context():
        target = db.session.get(Usuario, target_id)
        assert target.must_change_password is True
        assert target.auth_version == 1
        assert target.check_password(temporary_password)
        event = AuditLog.query.filter_by(action="RESTABLECER_CONTRASENA", outcome="success").one()
        assert temporary_password not in (event.metadata_json or "")
        assert temporary_password not in target.password_hash

    token = csrf_from(target_client.get("/login"))
    signed_in = target_client.post(
        "/login",
        data={"username": "doctor-reset", "password": temporary_password, "csrf_token": token},
    )
    assert signed_in.status_code == 302
    assert signed_in.headers["Location"].endswith("/mi-cuenta/cambiar-contrasena")
    forced_page = target_client.get("/mi-cuenta/cambiar-contrasena")
    final = target_client.post(
        "/mi-cuenta/cambiar-contrasena",
        data={
            "csrf_token": csrf_from(forced_page),
            "current_password": temporary_password,
            "new_password": "DoctorFinal!Pass2026",
            "confirm_password": "DoctorFinal!Pass2026",
        },
    )
    assert final.status_code == 302
    with app.app_context():
        assert db.session.get(Usuario, target_id).must_change_password is False


def test_offline_recovery_is_limited_to_admin_and_audited(app):
    with app.app_context():
        assistant = Usuario(
            username="offline-assistant",
            nombre="Ana",
            apellido_paterno="Apoyo",
            email="offline-assistant@example.test",
            rol="recepcion",
            status="activo",
        )
        assistant.set_password("AssistantPass!2026")
        db.session.add(assistant)
        db.session.commit()
        with pytest.raises(ValidationError, match="sólo puede restablecer una cuenta administradora"):
            reset_password_offline("offline-assistant", "Offline!Pass2026Z")
        user = reset_password_offline("administrator", "Offline!Pass2026Z")
        assert user.status == "activo"
        assert user.must_change_password is True
        assert user.auth_version == 1
        assert user.check_password("Offline!Pass2026Z")
        event = AuditLog.query.filter_by(action="RESTABLECER_CONTRASENA_LOCAL").one()
        assert "Offline!Pass2026Z" not in (event.metadata_json or "")
