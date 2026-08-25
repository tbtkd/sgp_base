"""Pruebas de navegador real; requieren Playwright y Chromium instalados."""

import threading

import pytest
from werkzeug.serving import make_server

from app import create_app
from app import db_orm as db
from app.models.usuario import Usuario

playwright = pytest.importorskip("playwright.sync_api")


@pytest.fixture()
def browser_app(tmp_path):
    database = tmp_path / "instance" / "pacientes.db"
    database.parent.mkdir()
    application = create_app(
        "testing",
        {
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database}",
            "BACKUP_DATABASE_PATH": database,
            "BACKUP_DIRECTORY": tmp_path / "backups",
            "WTF_CSRF_ENABLED": True,
        },
    )
    with application.app_context():
        db.create_all()
        admin = Usuario(
            username="administrator", nombre="Admin", apellido_paterno="Navegador",
            email="browser-admin@example.test", rol="admin", status="activo",
        )
        admin.set_password("StrongPass!2026")
        db.session.add(admin)
        db.session.commit()
    yield application
    with application.app_context():
        db.session.remove()
        db.engine.dispose()


@pytest.mark.browser
def test_local_assets_csp_login_and_local_confirmation(browser_app):
    server = make_server("127.0.0.1", 0, browser_app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    errors = []
    try:
        with playwright.sync_playwright() as runtime:
            try:
                browser = runtime.chromium.launch(headless=True)
            except playwright.Error as error:
                pytest.skip(f"Chromium de Playwright no está instalado: {error}")
            page = browser.new_page()
            page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
            page.on("request", lambda request: errors.append(f"Solicitud externa: {request.url}") if not request.url.startswith(f"http://127.0.0.1:{server.server_port}") else None)
            page.goto(f"http://127.0.0.1:{server.server_port}/login")
            page.fill("#username", "administrator")
            page.fill("#password", "StrongPass!2026")
            page.click('button[type="submit"]')
            page.wait_for_url(f"http://127.0.0.1:{server.server_port}/")
            page.evaluate(
                "window.__dialogResult = null; confirmarAccion({titulo: 'Prueba local', mensaje: 'Confirmar'}).then((result) => { window.__dialogResult = result.isConfirmed; });"
            )
            page.locator(".sgpn-dialog-confirm").click()
            page.wait_for_function("window.__dialogResult === true")
            assert not [message for message in errors if "favicon" not in message.lower()]
            browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=5)
