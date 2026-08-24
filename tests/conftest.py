import re

import pytest

from app import create_app
from app import db_orm as db
from app.core.security import reset_rate_limiter
from app.models.usuario import Usuario


@pytest.fixture()
def app():
    reset_rate_limiter()
    application = create_app(
        "testing",
        {
            "SERVER_NAME": "localhost",
            "WTF_CSRF_ENABLED": True,
        },
    )
    with application.app_context():
        db.drop_all()
        db.create_all()
        admin = Usuario(
            username="administrator",
            nombre="Admin",
            apellido_paterno="Pruebas",
            apellido_materno="Sistema",
            email="admin@example.test",
            rol="admin",
            perfil_profesional="nutricion",
            cedula_profesional="12345678",
            status="activo",
        )
        admin.set_password("StrongPass!2026")
        db.session.add(admin)
        db.session.commit()
    yield application
    with application.app_context():
        db.session.remove()
        with db.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
            db.metadata.drop_all(bind=connection)
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")


@pytest.fixture()
def client(app):
    return app.test_client()


def csrf_from(response):
    match = re.search(rb'(?:name="csrf_token" value="|name="csrf-token" content=")([^"\s]+)', response.data)
    assert match, "No se encontró un token CSRF en la respuesta"
    return match.group(1).decode("utf-8")


@pytest.fixture()
def login(client):
    def perform(username="administrator", password="StrongPass!2026"):
        token = csrf_from(client.get("/login"))
        return client.post(
            "/login",
            data={"username": username, "password": password, "csrf_token": token},
            follow_redirects=False,
        )

    return perform
