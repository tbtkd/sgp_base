import re
from datetime import date, time, timedelta
from pathlib import Path

from app import db_orm as db
from app.core.audit import AuditLog
from app.models.cita import Cita
from app.models.paciente import Paciente
from tests.conftest import csrf_from


def _patient(name="Paciente", phone="5512345678"):
    patient = Paciente(
        nombre=name,
        apellido_paterno="Pruebas",
        apellido_materno="Citas",
        genero="prefiero_no_decir",
        fecha_nacimiento=date(1990, 1, 1),
        telefono=phone,
        correo=f"{name.lower()}@example.test",
        ciudad="Ciudad de México",
        status="activo",
    )
    db.session.add(patient)
    db.session.commit()
    return patient


def _future_day(offset=3):
    return date.today() + timedelta(days=offset)


def test_appointment_modal_is_closed_and_hours_have_literal_labels(app, client, login):
    login()
    with app.app_context():
        patient_id = _patient().id

    response = client.get(f"/pacientes/{patient_id}")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert re.search(r'id="modalCita"[\s\S]*?\shidden>', page)
    assert re.search(r'id="modalAdvertenciaCita"[\s\S]*?\shidden>', page)
    assert "open-cita-modal" not in page
    assert "citaForm(" not in page
    assert page.count("data-hora-base=") == 21
    assert '>09:00</option>' in page
    assert '>09:30</option>' in page
    assert '>19:00</option>' in page
    assert 'id="btnCerrarModalCita"' in page
    assert 'id="btnCancelarModalCita"' in page


def test_appointment_modal_uses_local_close_and_loading_guards():
    project_root = Path(__file__).parents[1]
    script = (project_root / "app" / "static" / "js" / "detalle_paciente.js").read_text(encoding="utf-8")
    styles = (project_root / "app" / "static" / "css" / "style.css").read_text(encoding="utf-8")

    assert "inicializarModalCita" in script
    assert "btnCancelarModalCita" in script
    assert "btnCerrarModalCita" in script
    assert "evento.key !== 'Escape'" in script
    assert "window.addEventListener('pageshow'" in script
    assert "AbortController" in script
    assert "hora.disabled = false" in script
    assert "aria-busy" in script
    assert "open-cita-modal" not in script
    assert ".appointment-time-select option" in styles
    assert "color: #0f172a" in styles
    assert "[hidden]" in styles


def test_availability_requires_login(client):
    response = client.get(f"/pacientes/disponibilidad_horas?fecha={_future_day().isoformat()}")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_availability_is_sorted_and_can_exclude_current_appointment(app, client, login):
    login()
    target = _future_day()
    with app.app_context():
        first_patient = _patient("Primera", "5512345601")
        second_patient = _patient("Segunda", "5512345602")
        first = Cita(
            paciente_id=first_patient.id,
            fecha=target,
            hora=time(11, 30),
            motivo="Primera",
            estatus="Programada",
            estado="pendiente",
        )
        second = Cita(
            paciente_id=second_patient.id,
            fecha=target,
            hora=time(9, 0),
            motivo="Segunda",
            estatus="Programada",
            estado="pendiente",
        )
        db.session.add_all([first, second])
        db.session.commit()
        excluded_id = first.id

    response = client.get(f"/pacientes/disponibilidad_horas?fecha={target.isoformat()}")
    assert response.status_code == 200
    assert response.get_json() == ["09:00", "11:30"]
    assert response.headers["Cache-Control"] == "no-store"

    excluded = client.get(
        f"/pacientes/disponibilidad_horas?fecha={target.isoformat()}&excluir_cita_id={excluded_id}"
    )
    assert excluded.get_json() == ["09:00"]


def test_availability_rejects_invalid_date(client, login):
    login()
    response = client.get("/pacientes/disponibilidad_horas?fecha=no-es-fecha")
    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_kpi_opens_dedicated_scheduler_without_replacing_patient_modal(app, client, login):
    login()
    with app.app_context():
        patient_id = _patient().id

    dashboard = client.get("/").get_data(as_text=True)
    scheduler = client.get("/pacientes/agendar-cita").get_data(as_text=True)
    patient_detail = client.get(f"/pacientes/{patient_id}").get_data(as_text=True)
    sidebar = (Path(__file__).parents[1] / "app" / "templates" / "components" / "_sidebar.html").read_text(
        encoding="utf-8"
    )

    assert 'href="/pacientes/agendar-cita"' in dashboard
    assert "Agendar una cita" in scheduler
    assert scheduler.count("data-calendar-date=") == 21
    assert 'data-availability-url="/pacientes/disponibilidad_citas"' in scheduler
    assert 'data-patient-search' in scheduler
    assert 'data-patient-select' in scheduler
    assert "EXP-0001" in scheduler
    assert 'id="modalCita"' in patient_detail
    assert "agendar_cita_rapida" not in sidebar


def test_visual_availability_returns_every_slot_with_explicit_state(app, client, login):
    login()
    target = _future_day()
    with app.app_context():
        patient = _patient()
        db.session.add(
            Cita(
                paciente_id=patient.id,
                fecha=target,
                hora=time(10, 30),
                motivo="Horario ocupado",
                estatus="Programada",
                estado="pendiente",
            )
        )
        db.session.commit()

    response = client.get(f"/pacientes/disponibilidad_citas?fecha={target.isoformat()}")
    payload = response.get_json()
    slots = {slot["hora"]: slot for slot in payload["horarios"]}

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert payload["success"] is True
    assert payload["fecha"] == target.isoformat()
    assert len(payload["horarios"]) == 21
    assert slots["09:00"] == {"hora": "09:00", "disponible": True, "estado": "disponible"}
    assert slots["10:30"] == {"hora": "10:30", "disponible": False, "estado": "ocupado"}
    assert client.get("/pacientes/disponibilidad_citas?fecha=2000-01-01").status_code == 400


def test_quick_scheduler_creates_one_appointment_and_audits_origin(app, client, login):
    login()
    target = _future_day()
    with app.app_context():
        patient_id = _patient().id

    page = client.get("/pacientes/agendar-cita")
    response = client.post(
        "/pacientes/agendar-cita",
        data={
            "csrf_token": csrf_from(page),
            "paciente_id": str(patient_id),
            "proxima_cita_fecha": target.isoformat(),
            "proxima_cita_hora": "12:30",
            "motivo": "Consulta desde agenda rápida",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/#agenda-hoy")
    with app.app_context():
        appointment = Cita.query.one()
        assert appointment.paciente_id == patient_id
        assert appointment.fecha == target
        assert appointment.hora == time(12, 30)
        audit = AuditLog.query.filter_by(action="CREAR_CITA", entity_id=appointment.id).one()
        assert '"origen":"kpi_dashboard"' in audit.metadata_json


def test_quick_scheduler_rejects_existing_appointment_and_stale_slot(app, client, login):
    login()
    target = _future_day()
    with app.app_context():
        first = _patient("Primera", "5512345601")
        second = _patient("Segunda", "5512345602")
        db.session.add(
            Cita(
                paciente_id=first.id,
                fecha=target,
                hora=time(15, 0),
                motivo="Cita existente",
                estatus="Programada",
                estado="pendiente",
            )
        )
        db.session.commit()
        first_id, second_id = first.id, second.id

    first_page = client.get(f"/pacientes/agendar-cita?paciente_id={first_id}")
    existing = client.post(
        "/pacientes/agendar-cita",
        data={
            "csrf_token": csrf_from(first_page),
            "paciente_id": str(first_id),
            "proxima_cita_fecha": _future_day(4).isoformat(),
            "proxima_cita_hora": "11:00",
            "motivo": "No debe reemplazarla",
        },
    )
    assert existing.status_code == 400
    assert "ya tiene una cita programada" in existing.get_data(as_text=True)

    second_page = client.get(f"/pacientes/agendar-cita?paciente_id={second_id}")
    occupied = client.post(
        "/pacientes/agendar-cita",
        data={
            "csrf_token": csrf_from(second_page),
            "paciente_id": str(second_id),
            "proxima_cita_fecha": target.isoformat(),
            "proxima_cita_hora": "15:00",
            "motivo": "Conflicto",
        },
    )
    assert occupied.status_code == 400
    assert "ya no está disponible" in occupied.get_data(as_text=True)
    with app.app_context():
        assert Cita.query.count() == 1
        assert Cita.query.filter_by(paciente_id=second_id).count() == 0


def test_quick_scheduler_uses_safe_local_interactions():
    root = Path(__file__).parents[1]
    script = (root / "app" / "static" / "js" / "agendar_cita.js").read_text(encoding="utf-8")
    styles = (root / "app" / "static" / "css" / "appointment_scheduler.css").read_text(encoding="utf-8")

    assert "AbortController" in script
    assert "replaceChildren" in script
    assert "textContent" in script
    assert ".innerHTML" not in script
    assert "aria-pressed" in script
    assert "submitting" in script
    assert 'html[data-theme="dark"] .appointment-time' in styles
    assert ".appointment-day.is-selected" in styles


def test_create_appointment_persists_and_audits(app, client, login):
    login()
    target = _future_day()
    with app.app_context():
        patient_id = _patient().id

    token = csrf_from(client.get(f"/pacientes/{patient_id}"))
    response = client.post(
        f"/pacientes/{patient_id}/registrar_proxima_cita",
        data={
            "csrf_token": token,
            "proxima_cita_fecha": target.isoformat(),
            "proxima_cita_hora": "10:30",
            "motivo": "Control clínico",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Cita guardada exitosamente" in response.get_data(as_text=True)
    with app.app_context():
        appointment = Cita.query.one()
        assert appointment.paciente_id == patient_id
        assert appointment.fecha == target
        assert appointment.hora == time(10, 30)
        assert appointment.motivo == "Control clínico"
        assert AuditLog.query.filter_by(action="CREAR_CITA", entity_id=appointment.id).count() == 1


def test_reschedule_updates_same_record_and_audits(app, client, login):
    login()
    original_day = _future_day(2)
    new_day = _future_day(4)
    with app.app_context():
        patient = _patient()
        appointment = Cita(
            paciente_id=patient.id,
            fecha=original_day,
            hora=time(9, 0),
            motivo="Original",
            estatus="Programada",
            estado="pendiente",
        )
        db.session.add(appointment)
        db.session.commit()
        patient_id = patient.id
        appointment_id = appointment.id

    token = csrf_from(client.get(f"/pacientes/{patient_id}"))
    response = client.post(
        f"/pacientes/{patient_id}/registrar_proxima_cita",
        data={
            "csrf_token": token,
            "proxima_cita_fecha": new_day.isoformat(),
            "proxima_cita_hora": "12:00",
            "motivo": "Reagendada",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    with app.app_context():
        assert Cita.query.count() == 1
        updated = db.session.get(Cita, appointment_id)
        assert updated.fecha == new_day
        assert updated.hora == time(12, 0)
        assert updated.motivo == "Reagendada"
        assert AuditLog.query.filter_by(action="ACTUALIZAR_CITA", entity_id=appointment_id).count() == 1


def test_occupied_or_past_slot_is_not_persisted(app, client, login):
    login()
    target = _future_day()
    with app.app_context():
        first = _patient("Primera", "5512345601")
        second = _patient("Segunda", "5512345602")
        db.session.add(
            Cita(
                paciente_id=first.id,
                fecha=target,
                hora=time(16, 30),
                motivo="Ocupada",
                estatus="Programada",
                estado="pendiente",
            )
        )
        db.session.commit()
        second_id = second.id

    token = csrf_from(client.get(f"/pacientes/{second_id}"))
    occupied = client.post(
        f"/pacientes/{second_id}/registrar_proxima_cita",
        data={
            "csrf_token": token,
            "proxima_cita_fecha": target.isoformat(),
            "proxima_cita_hora": "16:30",
            "motivo": "Conflicto",
        },
        follow_redirects=True,
    )
    assert "ya no está disponible" in occupied.get_data(as_text=True)

    token = csrf_from(client.get(f"/pacientes/{second_id}"))
    past = client.post(
        f"/pacientes/{second_id}/registrar_proxima_cita",
        data={
            "csrf_token": token,
            "proxima_cita_fecha": (date.today() - timedelta(days=1)).isoformat(),
            "proxima_cita_hora": "10:00",
            "motivo": "Pasada",
        },
        follow_redirects=True,
    )
    assert "no puede estar en el pasado" in past.get_data(as_text=True)

    with app.app_context():
        assert Cita.query.count() == 1
        assert Cita.query.filter_by(paciente_id=second_id).count() == 0
