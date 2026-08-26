import re
from datetime import date, time, timedelta
from pathlib import Path

from app import db_orm as db
from app.core.audit import AuditLog
from app.models.cita import Cita
from app.models.paciente import Paciente
from app.models.usuario import Usuario
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


def _change_status(client, appointment_id, status, reason="", *, page="/agenda"):
    token = csrf_from(client.get(page))
    return client.post(
        f"/pacientes/citas/{appointment_id}/cambiar-estatus",
        json={"estatus": status, "motivo": reason},
        headers={"X-CSRFToken": token},
    )


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
    assert 'data-patient-search-url="/pacientes/buscar_para_cita"' in scheduler
    assert 'data-patient-search' in scheduler
    assert 'role="combobox"' in scheduler
    assert 'role="listbox"' in scheduler
    assert 'data-patient-id' in scheduler
    assert 'data-patient-select' not in scheduler
    assert "<option" not in scheduler
    assert "Paciente Pruebas Citas" not in scheduler
    assert 'id="modalCita"' in patient_detail
    assert "agendar_cita_rapida" not in sidebar


def test_scheduler_patient_search_is_private_limited_and_returns_only_matches(app, client, login):
    anonymous = client.get("/pacientes/buscar_para_cita?busqueda=Laura")
    assert anonymous.status_code == 302
    assert "/login" in anonymous.headers["Location"]

    login()
    target = _future_day()
    with app.app_context():
        selected = _patient("Laura", "5512345601")
        unrelated = _patient("Mario", "5512345602")
        accented = _patient("Sofía", "5512345604")
        inactive = _patient("LauraOculta", "5512345603")
        inactive.status = "inactivo"
        db.session.add(
            Cita(
                paciente_id=selected.id,
                fecha=target,
                hora=time(14, 30),
                motivo="Dato que no debe exponerse en la búsqueda",
                estatus="Programada",
                estado="pendiente",
            )
        )
        for index in range(10):
            _patient(f"Coincide{index}", f"55200000{index:02d}")
        db.session.commit()
        selected_id = selected.id
        accented_id = accented.id
        unrelated_name = unrelated.nombre_completo

    response = client.get("/pacientes/buscar_para_cita?busqueda=Laura")
    payload = response.get_json()
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert payload["success"] is True
    assert len(payload["resultados"]) == 1
    assert payload["resultados"][0] == {
        "id": selected_id,
        "nombre": "Laura Pruebas Citas",
        "expediente": f"EXP-{selected_id:04d}",
        "telefono": "5512345601",
        "detalle_url": f"/pacientes/{selected_id}",
        "cita_programada": {
            "fecha": target.isoformat(),
            "hora": "14:30",
            "etiqueta": f"{target.strftime('%d/%m/%Y')} · 14:30",
        },
    }
    assert unrelated_name not in response.get_data(as_text=True)
    assert "LauraOculta" not in response.get_data(as_text=True)
    assert "Dato que no debe exponerse" not in response.get_data(as_text=True)

    by_record = client.get(f"/pacientes/buscar_para_cita?busqueda=EXP-{selected_id:04d}").get_json()
    assert [item["id"] for item in by_record["resultados"]] == [selected_id]
    by_partial_name = client.get("/pacientes/buscar_para_cita?busqueda=sofi+prue").get_json()
    assert [item["id"] for item in by_partial_name["resultados"]] == [accented_id]
    assert len(client.get("/pacientes/buscar_para_cita?busqueda=Coincide").get_json()["resultados"]) == 8
    assert client.get("/pacientes/buscar_para_cita?busqueda=L").get_json()["resultados"] == []
    assert client.get("/pacientes/buscar_para_cita?busqueda=%25").get_json()["resultados"] == []
    assert client.get(f"/pacientes/buscar_para_cita?busqueda={'x' * 101}").status_code == 400

    selected_page = client.get(f"/pacientes/agendar-cita?paciente_id={selected_id}").get_data(as_text=True)
    assert "Laura Pruebas Citas" in selected_page
    assert unrelated_name not in selected_page


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
    assert "ArrowDown" in script
    assert "ArrowUp" in script
    assert "Escape" in script
    assert "window.setTimeout(() =>" in script
    assert "query !== selectedPatient.name" in script
    assert "X-Requested-With" in script
    assert "submitting" in script
    assert 'html[data-theme="dark"] .appointment-time' in styles
    assert ".appointment-selected-patient" in styles
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


def test_dedicated_agenda_requires_login_and_supports_day_week_navigation(app, client, login):
    anonymous = client.get("/agenda")
    assert anonymous.status_code == 302
    assert "/login" in anonymous.headers["Location"]

    login()
    target = _future_day()
    with app.app_context():
        patient = _patient("Agenda", "5512345690")
        db.session.add(
            Cita(
                paciente_id=patient.id,
                fecha=target,
                hora=time(10, 0),
                motivo="Revisión programada",
                estatus="Programada",
                estado="pendiente",
            )
        )
        db.session.commit()

    day = client.get(f"/agenda?fecha={target.isoformat()}&vista=dia")
    day_page = day.get_data(as_text=True)
    assert day.status_code == 200
    assert "Agenda y citas" in day_page
    assert "Agenda Pruebas Citas" in day_page
    assert 'href="/agenda"' in day_page
    assert 'aria-current="page"' in day_page
    assert "#agenda-hoy" not in day_page

    week_page = client.get(f"/agenda?fecha={target.isoformat()}&vista=semana").get_data(as_text=True)
    assert week_page.count('class="agenda-day-panel') == 7
    assert "Revisión programada" in week_page

    invalid = client.get("/agenda?fecha=no-es-fecha&vista=desconocida").get_data(as_text=True)
    assert "Revisa Fecha de agenda; la fecha no es válida" in invalid
    assert "La vista solicitada no es válida" in invalid


def test_agenda_hides_clinical_reason_from_reception_and_limits_start_action(app, client, login):
    with app.app_context():
        receptionist = Usuario(
            username="reception-agenda",
            nombre="Recepción",
            apellido_paterno="Agenda",
            email="reception-agenda@example.test",
            rol="recepcion",
            status="activo",
        )
        receptionist.set_password("StrongPass!2026")
        db.session.add(receptionist)
        patient = _patient("Privada", "5512345691")
        db.session.add(
            Cita(
                paciente_id=patient.id,
                fecha=date.today(),
                hora=time(19, 0),
                motivo="Motivo clínico reservado",
                estatus="Programada",
                estado="pendiente",
            )
        )
        db.session.commit()

    login("reception-agenda")
    reception_page = client.get(f"/agenda?fecha={date.today().isoformat()}").get_data(as_text=True)
    assert "Privada Pruebas Citas" in reception_page
    assert "Motivo clínico reservado" not in reception_page
    assert "Iniciar consulta" not in reception_page
    assert "Cita programada" in reception_page

    clinical_client = app.test_client()
    token = csrf_from(clinical_client.get("/login"))
    clinical_client.post(
        "/login",
        data={
            "username": "administrator",
            "password": "StrongPass!2026",
            "csrf_token": token,
        },
    )
    clinical_page = clinical_client.get(f"/agenda?fecha={date.today().isoformat()}").get_data(as_text=True)
    assert "Motivo clínico reservado" in clinical_page
    assert "Iniciar consulta" in clinical_page


def test_agenda_creation_returns_to_agenda_and_records_origin(app, client, login):
    login()
    target = _future_day()
    with app.app_context():
        patient_id = _patient("Origen", "5512345692").id

    page = client.get(f"/pacientes/agendar-cita?origen=agenda&fecha={target.isoformat()}")
    content = page.get_data(as_text=True)
    assert 'name="origen" value="agenda"' in content
    assert "Volver a Agenda" in content
    response = client.post(
        "/pacientes/agendar-cita",
        data={
            "csrf_token": csrf_from(page),
            "origen": "agenda",
            "paciente_id": str(patient_id),
            "proxima_cita_fecha": target.isoformat(),
            "proxima_cita_hora": "13:30",
            "motivo": "Alta desde módulo operativo",
        },
    )
    assert response.status_code == 302
    assert response.headers["Location"].startswith(f"/agenda?fecha={target.isoformat()}")
    with app.app_context():
        appointment = Cita.query.one()
        audit = AuditLog.query.filter_by(action="CREAR_CITA", entity_id=appointment.id).one()
        assert '"origen":"agenda"' in audit.metadata_json


def test_agenda_reschedule_reuses_availability_and_preserves_record(app, client, login):
    login()
    original_day = _future_day(2)
    new_day = _future_day(5)
    with app.app_context():
        patient = _patient("Reagenda", "5512345693")
        appointment = Cita(
            paciente_id=patient.id,
            fecha=original_day,
            hora=time(11, 0),
            motivo="Cita original",
            estatus="Programada",
            estado="pendiente",
        )
        db.session.add(appointment)
        db.session.commit()
        appointment_id = appointment.id

    page = client.get(f"/agenda/citas/{appointment_id}/reagendar")
    content = page.get_data(as_text=True)
    assert page.status_code == 200
    assert "Reagendar cita" in content
    assert f'data-editing-appointment="{appointment_id}"' in content
    assert 'role="combobox"' not in content
    assert 'value="11:00" data-selected-time' in content
    assert "Reagenda Pruebas Citas" in content

    availability = client.get(
        f"/pacientes/disponibilidad_citas?fecha={original_day.isoformat()}&excluir_cita_id={appointment_id}"
    ).get_json()
    old_slot = next(slot for slot in availability["horarios"] if slot["hora"] == "11:00")
    assert old_slot["disponible"] is True

    response = client.post(
        f"/agenda/citas/{appointment_id}/reagendar",
        data={
            "csrf_token": csrf_from(page),
            "proxima_cita_fecha": new_day.isoformat(),
            "proxima_cita_hora": "14:00",
            "motivo": "Cita reagendada",
        },
    )
    assert response.status_code == 302
    assert response.headers["Location"].startswith(f"/agenda?fecha={new_day.isoformat()}")
    with app.app_context():
        assert Cita.query.count() == 1
        updated = db.session.get(Cita, appointment_id)
        assert updated.fecha == new_day
        assert updated.hora == time(14, 0)
        assert updated.motivo == "Cita reagendada"
        audit = AuditLog.query.filter_by(action="ACTUALIZAR_CITA", entity_id=appointment_id).one()
        assert '"origen":"agenda"' in audit.metadata_json


def test_agenda_reschedule_rejects_conflict_and_closed_appointment(app, client, login):
    login()
    target = _future_day()
    with app.app_context():
        first = _patient("PrimeraAgenda", "5512345694")
        second = _patient("SegundaAgenda", "5512345695")
        first_appointment = Cita(
            paciente_id=first.id,
            fecha=target,
            hora=time(10, 0),
            estatus="Programada",
            estado="pendiente",
        )
        occupied = Cita(
            paciente_id=second.id,
            fecha=target,
            hora=time(10, 30),
            estatus="Programada",
            estado="pendiente",
        )
        db.session.add_all([first_appointment, occupied])
        db.session.commit()
        appointment_id = first_appointment.id

    page = client.get(f"/agenda/citas/{appointment_id}/reagendar")
    conflict = client.post(
        f"/agenda/citas/{appointment_id}/reagendar",
        data={
            "csrf_token": csrf_from(page),
            "proxima_cita_fecha": target.isoformat(),
            "proxima_cita_hora": "10:30",
            "motivo": "No debe persistirse",
        },
    )
    assert conflict.status_code == 400
    assert "ya no está disponible" in conflict.get_data(as_text=True)
    with app.app_context():
        unchanged = db.session.get(Cita, appointment_id)
        assert unchanged.hora == time(10, 0)
        denied = AuditLog.query.filter_by(
            action="ACTUALIZAR_CITA", entity_id=appointment_id, outcome="denied"
        ).one()
        assert '"origen":"agenda"' in denied.metadata_json
        unchanged.estatus = "Cancelada"
        unchanged.estado = "completada"
        past_patient = _patient("PasadaAgenda", "5512345698")
        past_appointment = Cita(
            paciente_id=past_patient.id,
            fecha=date.today() - timedelta(days=1),
            hora=time(9, 0),
            estatus="Programada",
            estado="pendiente",
        )
        db.session.add(past_appointment)
        db.session.commit()
        past_appointment_id = past_appointment.id

    closed = client.get(f"/agenda/citas/{appointment_id}/reagendar", follow_redirects=True)
    assert "Sólo las citas programadas pueden reagendarse" in closed.get_data(as_text=True)
    elapsed = client.get(f"/agenda/citas/{past_appointment_id}/reagendar", follow_redirects=True)
    assert "horario ya transcurrió" in elapsed.get_data(as_text=True)


def test_agenda_status_transitions_close_past_appointment_and_block_reopening(app, client, login):
    login()
    past_day = date.today() - timedelta(days=1)
    with app.app_context():
        patient = _patient("Inasistencia", "5512345696")
        appointment = Cita(
            paciente_id=patient.id,
            fecha=past_day,
            hora=time(9, 0),
            motivo="Seguimiento",
            estatus="Programada",
            estado="pendiente",
        )
        db.session.add(appointment)
        db.session.commit()
        appointment_id = appointment.id

    changed = _change_status(
        client,
        appointment_id,
        "No Asistió",
        "No se presentó",
        page=f"/agenda?fecha={past_day.isoformat()}",
    )
    assert changed.status_code == 200
    assert changed.get_json()["nuevo_estatus"] == "No Asistió"
    reopened = _change_status(client, appointment_id, "Programada", page=f"/agenda?fecha={past_day.isoformat()}")
    assert reopened.status_code == 400
    assert "ya está cerrada" in reopened.get_json()["error"]
    with app.app_context():
        appointment = db.session.get(Cita, appointment_id)
        assert appointment.estatus == "No Asistió"
        assert appointment.estado == "completada"
        assert appointment.motivo_cancelacion == "No se presentó"
        logs = AuditLog.query.filter_by(action="CAMBIAR_ESTADO_CITA", entity_id=appointment_id).all()
        assert {log.outcome for log in logs} == {"success", "denied"}


def test_agenda_blocks_future_closure_and_requires_cancellation_reason(app, client, login):
    login()
    target = _future_day()
    with app.app_context():
        patient = _patient("Futura", "5512345697")
        appointment = Cita(
            paciente_id=patient.id,
            fecha=target,
            hora=time(17, 0),
            estatus="Programada",
            estado="pendiente",
        )
        db.session.add(appointment)
        db.session.commit()
        appointment_id = appointment.id

    for status in ("Atendida", "No Asistió"):
        response = _change_status(client, appointment_id, status)
        assert response.status_code == 400
        assert "cita futura" in response.get_json()["error"]
    missing_reason = _change_status(client, appointment_id, "Cancelada")
    assert missing_reason.status_code == 400
    assert "motivo de cancelación" in missing_reason.get_json()["error"]
    invalid = _change_status(client, appointment_id, "Eliminada")
    assert invalid.status_code == 400
    assert "Selecciona una opción válida en Estatus" in invalid.get_json()["error"]

    cancelled = _change_status(client, appointment_id, "Cancelada", "Solicitud del paciente")
    assert cancelled.status_code == 200
    with app.app_context():
        appointment = db.session.get(Cita, appointment_id)
        assert appointment.estatus == "Cancelada"
        assert appointment.estado == "completada"
        assert appointment.motivo_cancelacion == "Solicitud del paciente"


def test_agenda_frontend_uses_local_safe_state_controls():
    root = Path(__file__).parents[1]
    script = (root / "app" / "static" / "js" / "agenda.js").read_text(encoding="utf-8")
    styles = (root / "app" / "static" / "css" / "agenda.css").read_text(encoding="utf-8")
    template = (root / "app" / "templates" / "agenda" / "index.html").read_text(encoding="utf-8")

    assert "allowedStatuses" in script
    assert "pendingRequests" in script
    assert "textContent" in script
    assert "replaceAll" in script
    assert ".innerHTML" not in script
    assert "data-appointment-status-action" in template
    assert 'aria-live="polite"' in template
    assert 'vista_agenda == \'semana\'' in template
    assert 'html[data-theme="dark"] .agenda-workspace' in styles
    assert ".agenda-days--semana" in styles
