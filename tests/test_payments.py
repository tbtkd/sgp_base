import re
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import text

from app import create_app
from app import db_orm as db
from app.core.validators import ValidationError, money_centavos, payment_payload
from app.models.bitacora import AuditLog
from app.models.cita import Cita
from app.models.paciente import Paciente
from app.models.pago import Pago
from app.models.usuario import Usuario
from tests.conftest import csrf_from


def _patient(phone="5512345678", name="Ángela"):
    patient = Paciente(
        nombre=name,
        apellido_paterno="García",
        apellido_materno="López",
        genero="mujer",
        fecha_nacimiento=date(1990, 5, 10),
        telefono=phone,
        correo=f"{phone}@example.test",
        ciudad="Ciudad de México",
        status="activo",
    )
    db.session.add(patient)
    db.session.flush()
    return patient


def _user(username, role):
    user = Usuario(
        username=username,
        nombre=username.title(),
        apellido_paterno="Pagos",
        email=f"{username}@example.test",
        rol=role,
        status="activo",
    )
    user.set_password("PaymentPass!2026")
    db.session.add(user)
    db.session.flush()
    return user


def _login(client, username, password="PaymentPass!2026"):
    page = client.get("/login")
    return client.post(
        "/login",
        data={"username": username, "password": password, "csrf_token": csrf_from(page)},
    )


def _operation_key(response):
    match = re.search(rb'name="operation_key" value="([^"]+)"', response.data)
    assert match
    return match.group(1).decode()


def _create_payment(patient, user, *, cents=50000, concept="Consulta", method="efectivo", days=0):
    payment = Pago.crear(
        patient.id,
        {
            "fecha_pago": date.today() - timedelta(days=days),
            "monto_centavos": cents,
            "concepto": concept,
            "metodo_pago": method,
            "operation_key": str(uuid4()),
        },
        usuario_id=user.id,
    )
    db.session.flush()
    return payment


def test_money_validator_uses_exact_cents_and_rejects_ambiguous_values():
    assert money_centavos("1250.05") == 125005
    assert money_centavos("88,50") == 8850
    payload = payment_payload(
        {
            "fecha_pago": date.today().isoformat(),
            "monto": "0.10",
            "concepto": "Consulta",
            "metodo_pago": "tarjeta",
            "operation_key": str(uuid4()),
        }
    )
    assert payload["monto_centavos"] == 10
    for invalid in ("0", "-1", "1.001", "1e3", "NaN", "10000000.01"):
        with pytest.raises(ValidationError):
            money_centavos(invalid)


def test_register_payment_assigns_folio_user_appointment_and_blocks_double_submit(app, client, login):
    login()
    with app.app_context():
        patient = _patient()
        appointment = Cita(
            paciente_id=patient.id,
            fecha=date.today() + timedelta(days=1),
            hora=Cita.HORARIOS_ATENCION[0],
            motivo="Seguimiento",
            estado="pendiente",
            estatus="Programada",
        )
        db.session.add(appointment)
        db.session.commit()
        patient_id, appointment_id = patient.id, appointment.id

    page = client.get(f"/pacientes/{patient_id}")
    token = csrf_from(page)
    operation = _operation_key(page)
    form = {
        "csrf_token": token,
        "operation_key": operation,
        "fecha_pago": date.today().isoformat(),
        "monto": "1234.56",
        "concepto": "Consulta de seguimiento",
        "metodo_pago": "transferencia",
        "cita_id": str(appointment_id),
    }
    first = client.post(f"/pacientes/{patient_id}/pago", data=form)
    second = client.post(f"/pacientes/{patient_id}/pago", data=form)
    assert first.status_code == second.status_code == 302

    with app.app_context():
        payments = Pago.query.all()
        assert len(payments) == 1
        payment = payments[0]
        assert payment.monto_centavos == 123456
        assert payment.monto == 1234.56
        assert payment.moneda == "MXN"
        assert payment.folio.startswith(f"PAG-{date.today():%Y%m%d}-")
        assert payment.usuario_registro.username == "administrator"
        assert payment.cita_id == appointment_id
        assert AuditLog.query.filter_by(action="REGISTRAR_PAGO", entity_id=payment.id).one()
        assert AuditLog.query.filter_by(action="RECHAZAR_PAGO_DUPLICADO", entity_id=payment.id).one()


def test_payment_rejects_foreign_appointment(app, client, login):
    login()
    with app.app_context():
        patient = _patient()
        other = _patient(phone="5512345679", name="Beatriz")
        appointment = Cita(
            paciente_id=other.id,
            fecha=date.today() + timedelta(days=1),
            hora=Cita.HORARIOS_ATENCION[1],
            estado="pendiente",
            estatus="Programada",
        )
        db.session.add(appointment)
        db.session.commit()
        patient_id, appointment_id = patient.id, appointment.id
    page = client.get(f"/pacientes/{patient_id}")
    response = client.post(
        f"/pacientes/{patient_id}/pago",
        data={
            "csrf_token": csrf_from(page),
            "operation_key": _operation_key(page),
            "fecha_pago": date.today().isoformat(),
            "monto": "500.00",
            "concepto": "Consulta",
            "metodo_pago": "efectivo",
            "cita_id": str(appointment_id),
        },
        follow_redirects=True,
    )
    assert "La cita seleccionada no pertenece al paciente" in response.get_data(as_text=True)
    with app.app_context():
        assert Pago.query.count() == 0


def test_patient_history_shows_amount_folio_and_cancellation_without_deleting_original(app, client, login):
    login()
    with app.app_context():
        patient = _patient()
        admin = Usuario.find_by_username("administrator")
        older = _create_payment(patient, admin, cents=40000, concept="Anterior", days=5)
        latest = _create_payment(patient, admin, cents=65025, concept="Actual")
        db.session.commit()
        patient_id, older_id, latest_id, latest_folio = patient.id, older.id, latest.id, latest.folio

    page = client.get(f"/pacientes/{patient_id}")
    html = page.get_data(as_text=True)
    assert "Historial de pagos" in html
    assert "$650.25 MXN" in html
    assert latest_folio in html
    response = client.post(
        f"/pagos/{latest_id}/cancelar",
        data={
            "csrf_token": csrf_from(page),
            "return_to": f"/pacientes/{patient_id}",
            "motivo_cancelacion": "Captura duplicada comprobada",
        },
        follow_redirects=True,
    )
    html = response.get_data(as_text=True)
    assert "Cancelado" in html
    assert "Captura duplicada comprobada" in html
    assert "$400.00 MXN" in html
    with app.app_context():
        assert Pago.query.count() == 2
        assert Pago.obtener_ultimo_pago(patient_id).id == older_id
        cancelled = db.session.get(Pago, latest_id)
        assert cancelled.monto_centavos == 65025
        assert cancelled.cancelado_por_id is not None
        assert AuditLog.query.filter_by(action="CANCELAR_PAGO", entity_id=latest_id).one()


def test_global_payment_module_roles_filters_and_totals(app, client):
    with app.app_context():
        patient = _patient()
        admin = Usuario.find_by_username("administrator")
        receptionist = _user("reception-pay", "recepcion")
        _user("doctor-pay", "medico")
        cash = _create_payment(patient, admin, cents=10010, concept="Consulta Ágil", method="efectivo")
        card = _create_payment(patient, receptionist, cents=25020, concept="Control", method="tarjeta")
        cancelled = _create_payment(patient, admin, cents=50000, concept="Duplicado", method="efectivo")
        formula = _create_payment(patient, admin, cents=101, concept="=2+3", method="otro")
        cancelled.cancelar(usuario_id=admin.id, motivo="Movimiento duplicado de prueba")
        db.session.commit()
        card_id = card.id
        patient_id = patient.id
        cash_folio, card_folio, formula_folio = cash.folio, card.folio, formula.folio

    _login(client, "administrator", "StrongPass!2026")
    report = client.get(
        f"/pagos/?desde={date.today():%Y-%m-%d}&hasta={date.today():%Y-%m-%d}&agrupacion=mes"
    )
    report_html = report.get_data(as_text=True)
    assert report.status_code == 200
    assert "Resumen por mes" in report_html
    assert "Exportar filtro CSV" in report_html
    full_name_result = client.get(
        "/pagos/",
        query_string={
            "desde": date.today().isoformat(),
            "hasta": date.today().isoformat(),
            "q": patient.nombre_completo,
        },
    )
    full_name_html = full_name_result.get_data(as_text=True)
    assert full_name_result.status_code == 200
    assert cash_folio in full_name_html
    assert card_folio in full_name_html
    exported = client.get(
        f"/pagos/exportar.csv?desde={date.today():%Y-%m-%d}&hasta={date.today():%Y-%m-%d}"
    )
    assert exported.status_code == 200
    assert exported.headers["Content-Type"].startswith("text/csv")
    exported_text = exported.data.decode("utf-8-sig")
    assert formula_folio in exported_text
    assert "'=2+3" in exported_text
    patient_export = client.get(f"/pagos/paciente/{patient_id}/historial.csv")
    assert patient_export.status_code == 200
    assert "historial_pagos_EXP-" in patient_export.headers["Content-Disposition"]
    with app.app_context():
        assert AuditLog.query.filter_by(action="EXPORTAR_PAGOS").count() == 2
    client.post("/logout", data={"csrf_token": csrf_from(report)})

    _login(client, "reception-pay")
    response = client.get(
        f"/pagos/?desde={date.today():%Y-%m-%d}&hasta={date.today():%Y-%m-%d}&q=agil"
    )
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert cash_folio in html
    assert card_folio not in html
    assert "$100.10 MXN" in html
    assert "Conservar original y cancelar" not in html
    assert "Exportar filtro CSV" not in html
    assert client.get("/pagos/exportar.csv").status_code == 403
    client.post("/logout", data={"csrf_token": csrf_from(response)})

    _login(client, "doctor-pay")
    assert client.get("/pagos/").status_code == 403
    client.get("/logout")

    anonymous = app.test_client()
    assert anonymous.get("/pagos/").status_code == 302

    with app.app_context():
        assert db.session.get(Pago, card_id).estatus == "vigente"


def test_reception_cannot_cancel_and_admin_cannot_cancel_twice(app, client):
    with app.app_context():
        patient = _patient()
        admin = Usuario.find_by_username("administrator")
        _user("reception-cancel", "recepcion")
        payment = _create_payment(patient, admin)
        db.session.commit()
        patient_id, payment_id, payment_folio = patient.id, payment.id, payment.folio
    _login(client, "reception-cancel")
    page = client.get(f"/pacientes/{patient_id}")
    assert client.post(
        f"/pagos/{payment_id}/cancelar",
        data={"csrf_token": csrf_from(page), "motivo_cancelacion": "No autorizado"},
    ).status_code == 403

    client = app.test_client()
    _login(client, "administrator", "StrongPass!2026")
    page = client.get(f"/pacientes/{patient_id}")
    token = csrf_from(page)
    first = client.post(
        f"/pagos/{payment_id}/cancelar",
        data={
            "csrf_token": token,
            "motivo_cancelacion": "Cancelación administrativa válida",
            "return_to": (
                f"/pagos/?desde={date.today().isoformat()}&hasta={date.today().isoformat()}"
                "&estatus=vigente&page=2"
            ),
        },
    )
    second_page = client.get(f"/pacientes/{patient_id}")
    second = client.post(
        f"/pagos/{payment_id}/cancelar",
        data={
            "csrf_token": csrf_from(second_page),
            "motivo_cancelacion": "Segundo intento inválido",
            "return_to": "https://evil.example/robo",
        },
    )
    assert first.status_code == second.status_code == 302
    assert f"q={payment_folio}" in first.headers["Location"]
    assert "estatus=vigente" not in first.headers["Location"]
    assert "page=2" not in first.headers["Location"]
    assert first.headers["Location"].endswith(f"#pago-{payment_id}")
    assert second.headers["Location"] == f"/pagos/#pago-{payment_id}"
    with app.app_context():
        payment = db.session.get(Pago, payment_id)
        assert payment.motivo_cancelacion == "Cancelación administrativa válida"
        assert AuditLog.query.filter_by(action="CANCELAR_PAGO", entity_id=payment_id, outcome="denied").one()


def test_payment_filters_reject_excessive_or_inverted_ranges(client, login):
    login()
    inverted = client.get("/pagos/?desde=2026-08-10&hasta=2026-08-01", follow_redirects=True)
    assert "La fecha final no puede ser anterior" in inverted.get_data(as_text=True)
    excessive = client.get("/pagos/?desde=2020-01-01&hasta=2026-01-01", follow_redirects=True)
    assert "no puede exceder 366 días" in excessive.get_data(as_text=True)


def test_payment_migration_preserves_valid_rows_and_quarantines_incomplete_legacy_data(tmp_path):
    database = Path(tmp_path) / "legacy-payments.db"
    connection = sqlite3.connect(database)
    connection.executescript(
        """
        PRAGMA foreign_keys=ON;
        CREATE TABLE pacientes (
            id INTEGER PRIMARY KEY, nombre VARCHAR(60) NOT NULL,
            apellido_paterno VARCHAR(60) NOT NULL, apellido_materno VARCHAR(60),
            genero VARCHAR(30) NOT NULL, fecha_nacimiento DATE NOT NULL,
            telefono VARCHAR(10) NOT NULL, correo VARCHAR(254), ciudad VARCHAR(100) NOT NULL,
            fecha_registro DATETIME, status VARCHAR(20)
        );
        INSERT INTO pacientes VALUES
            (1,'Ana','Prueba',NULL,'mujer','1990-01-01','5512345678',NULL,'México','2026-01-01','activo'),
            (2,'Beto','Prueba',NULL,'hombre','1991-01-01','5512345679',NULL,'México','2026-01-01','activo');
        CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY, username VARCHAR(50) NOT NULL,
            password_hash VARCHAR(256) NOT NULL, nombre VARCHAR(50),
            cedula_profesional VARCHAR(30), rol VARCHAR(20), apellido_paterno VARCHAR(50),
            apellido_materno VARCHAR(50), status VARCHAR(20)
        );
        INSERT INTO usuarios VALUES (1,'legacy','hash','Usuario',NULL,'Admin','Prueba',NULL,'activo');
        CREATE TABLE pagos (
            id INTEGER PRIMARY KEY, paciente_id INTEGER NOT NULL, fecha_pago DATE NOT NULL,
            monto FLOAT, concepto VARCHAR(200), metodo_pago VARCHAR(30),
            FOREIGN KEY(paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
        );
        INSERT INTO pagos VALUES (1,1,'2026-01-10',125.55,'Consulta','tarjeta');
        INSERT INTO pagos VALUES (2,2,'2026-01-11',NULL,NULL,NULL);
        """
    )
    connection.commit()
    connection.close()

    migration_app = create_app(
        "testing",
        {"SQLALCHEMY_DATABASE_URI": f"sqlite:///{database.as_posix()}", "AUTO_BACKUP_DATABASE": False},
    )
    with migration_app.app_context():
        assert db.session.execute(text("PRAGMA foreign_keys")).scalar() == 1
        db.session.remove()
        db.engine.dispose()

    connection = sqlite3.connect(database)
    connection.execute("PRAGMA foreign_keys=ON")
    rows = connection.execute(
        "SELECT id, monto_centavos, estatus, folio, concepto FROM pagos ORDER BY id"
    ).fetchall()
    foreign_keys = connection.execute("PRAGMA foreign_key_list('pagos')").fetchall()
    assert rows[0][1:3] == (12555, "vigente")
    assert rows[0][3].startswith("PAG-20260110-")
    assert rows[1][1:3] == (0, "requiere_revision")
    assert rows[1][4] == "Pago legado sin concepto"
    assert next(row for row in foreign_keys if row[3] == "paciente_id")[6] == "RESTRICT"
    assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("DELETE FROM pacientes WHERE id=1")
    connection.close()


def test_payment_ui_is_integrated_and_has_dark_theme_contract(app, client, login):
    login()
    with app.app_context():
        patient = _patient()
        db.session.commit()
        patient_id = patient.id
    page = client.get(f"/pacientes/{patient_id}").get_data(as_text=True)
    global_page = client.get("/pagos/").get_data(as_text=True)
    css = (Path(__file__).parents[1] / "app" / "static" / "css" / "payments.css").read_text(encoding="utf-8")
    script = (Path(__file__).parents[1] / "app" / "static" / "js" / "payments.js").read_text(encoding="utf-8")
    assert "Historial de pagos" in page
    assert 'min="0.01"' in page
    assert 'name="operation_key"' in page
    assert "Una cita existente no se enlaza automáticamente" in page
    assert "no determina si debe emitirse factura" in page
    assert "Ver en Pagos" in page
    assert "Total vigente" in global_page
    assert "Resumen por día" in global_page
    assert "Exportar filtro CSV" in global_page
    assert "No constituye facturación CFDI" in global_page
    assert 'html[data-theme="dark"]' in css
    assert ".payment-table tbody tr:target" in css
    assert ".payment-cancel-menu form { position: static" in css
    assert "data-payment-form" in script
    assert "window.confirm" in script
