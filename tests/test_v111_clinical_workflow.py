from datetime import date, timedelta
from uuid import uuid4

from app import db_orm as db
from app.core.audit import AuditLog
from app.models.historial_clinico import HistorialClinico
from app.models.nota_clinica import AclaracionNotaClinica, NotaCierreClinico
from app.models.paciente import Paciente
from app.models.usuario import Usuario
from app.models.valoracion_antropometrica import ValoracionAntropometrica
from tests.conftest import csrf_from


def _patient(name, paternal, phone, email=None):
    patient = Paciente(
        nombre=name,
        apellido_paterno=paternal,
        apellido_materno="Pruebas",
        genero="mujer",
        fecha_nacimiento=date(1990, 1, 1),
        telefono=phone,
        correo=email or f"{phone}@example.test",
        ciudad="Ciudad de México",
        status="activo",
    )
    db.session.add(patient)
    db.session.flush()
    return patient


def _assessment(patient, professional_id, when=None, reason="Consulta de control"):
    assessment = ValoracionAntropometrica(
        paciente_id=patient.id,
        profesional_id=professional_id,
        profesional_nombre="Admin Pruebas Sistema",
        numero_cita=1,
        fecha=when or date.today(),
        motivo_consulta=reason,
        impresion_diagnostica="Evolución favorable",
        plan_tratamiento="Continuar seguimiento",
    )
    db.session.add(assessment)
    db.session.commit()
    return assessment.id


def _doctor(username):
    user = Usuario(
        username=username,
        nombre="Médico",
        apellido_paterno=username,
        email=f"{username}@example.test",
        rol="medico",
        perfil_profesional="medico_general",
        status="activo",
    )
    user.set_password("StrongPass!2026")
    db.session.add(user)
    db.session.commit()
    return user.id


def _login(client, username):
    page = client.get("/login")
    return client.post(
        "/login",
        data={"username": username, "password": "StrongPass!2026", "csrf_token": csrf_from(page)},
    )


def test_clinical_note_close_is_immutable_audited_and_idempotent(app, client, login):
    login()
    with app.app_context():
        admin_id = Usuario.find_by_username("administrator").id
        assessment_id = _assessment(_patient("Laura", "Cierre", "5511000001"), admin_id)

    detail = client.get(f"/valoraciones/valoraciones/{assessment_id}")
    assert "Nota en borrador" in detail.get_data(as_text=True)
    operation = str(uuid4())
    response = client.post(
        f"/valoraciones/valoraciones/{assessment_id}/cerrar",
        data={
            "csrf_token": csrf_from(detail),
            "operation_key": operation,
            "confirmar_cierre": "si",
        },
        follow_redirects=True,
    )
    page = response.get_data(as_text=True)
    assert "Nota cerrada" in page
    assert "Editar" not in page

    second = client.post(
        f"/valoraciones/valoraciones/{assessment_id}/cerrar",
        data={
            "csrf_token": csrf_from(response),
            "operation_key": operation,
            "confirmar_cierre": "si",
        },
        follow_redirects=True,
    )
    assert second.status_code == 200
    with app.app_context():
        assert NotaCierreClinico.query.filter_by(valoracion_id=assessment_id).count() == 1
        assert AuditLog.query.filter_by(action="CERRAR_NOTA_CLINICA", entity_id=assessment_id).count() == 1

    edit = client.post(
        f"/valoraciones/valoraciones/{assessment_id}/editar",
        data={"csrf_token": csrf_from(response), "motivo_consulta": "Intento de cambio"},
        follow_redirects=True,
    )
    assert "no puede modificarse" in edit.get_data(as_text=True)
    delete = client.post(
        f"/valoraciones/valoraciones/{assessment_id}/eliminar",
        data={"csrf_token": csrf_from(edit)},
        follow_redirects=True,
    )
    assert "No es posible eliminarla" in delete.get_data(as_text=True)
    with app.app_context():
        assessment = db.session.get(ValoracionAntropometrica, assessment_id)
        assert assessment.motivo_consulta == "Consulta de control"
        assert assessment is not None
        denied = AuditLog.query.filter_by(entity_id=assessment_id, outcome="denied").all()
        assert {entry.action for entry in denied} >= {"ACTUALIZAR_CONSULTA", "ELIMINAR_CONSULTA"}


def test_addendum_requires_closed_note_valid_data_and_is_idempotent(app, client, login):
    login()
    with app.app_context():
        admin_id = Usuario.find_by_username("administrator").id
        assessment_id = _assessment(_patient("Rosa", "Aclaración", "5511000002"), admin_id)

    detail = client.get(f"/valoraciones/valoraciones/{assessment_id}")
    denied = client.post(
        f"/valoraciones/valoraciones/{assessment_id}/aclaraciones",
        data={"csrf_token": csrf_from(detail), "operation_key": str(uuid4()), "motivo": "Dato nuevo", "contenido": "Resultado posterior"},
        follow_redirects=True,
    )
    assert "Primero debes cerrar la nota" in denied.get_data(as_text=True)

    close_page = client.get(f"/valoraciones/valoraciones/{assessment_id}")
    client.post(
        f"/valoraciones/valoraciones/{assessment_id}/cerrar",
        data={"csrf_token": csrf_from(close_page), "operation_key": str(uuid4()), "confirmar_cierre": "si"},
    )
    closed = client.get(f"/valoraciones/valoraciones/{assessment_id}")
    invalid = client.post(
        f"/valoraciones/valoraciones/{assessment_id}/aclaraciones",
        data={"csrf_token": csrf_from(closed), "operation_key": "invalida", "motivo": "x", "contenido": "y"},
        follow_redirects=True,
    )
    assert "Motivo de la aclaración es obligatorio" in invalid.get_data(as_text=True)
    invalid_operation = client.post(
        f"/valoraciones/valoraciones/{assessment_id}/aclaraciones",
        data={
            "csrf_token": csrf_from(invalid),
            "operation_key": "invalida",
            "motivo": "Resultado recibido",
            "contenido": "Contenido válido para comprobar la solicitud.",
        },
        follow_redirects=True,
    )
    assert "La página dejó de ser válida" in invalid_operation.get_data(as_text=True)

    operation = str(uuid4())
    valid = client.post(
        f"/valoraciones/valoraciones/{assessment_id}/aclaraciones",
        data={"csrf_token": csrf_from(invalid_operation), "operation_key": operation, "motivo": "Resultado recibido", "contenido": "Se recibió un resultado posterior sin datos de alarma."},
        follow_redirects=True,
    )
    assert "Aclaración 1" in valid.get_data(as_text=True)
    assert "Resultado recibido" in valid.get_data(as_text=True)
    client.post(
        f"/valoraciones/valoraciones/{assessment_id}/aclaraciones",
        data={"csrf_token": csrf_from(valid), "operation_key": operation, "motivo": "Resultado recibido", "contenido": "Duplicado"},
    )
    with app.app_context():
        assert AclaracionNotaClinica.query.count() == 1
        assert AuditLog.query.filter_by(
            action="AGREGAR_ACLARACION_NOTA", entity_id=assessment_id, outcome="success"
        ).count() == 1
    printed = client.get(f"/valoraciones/valoraciones/{assessment_id}/imprimir").get_data(as_text=True)
    assert "Cierre de la nota" in printed
    assert "Resultado recibido" in printed


def test_clinical_note_rejects_unauthorized_professional_and_missing_csrf(app, client, login):
    login()
    with app.app_context():
        owner_id = _doctor("owner-v111")
        _doctor("other-v111")
        assessment_id = _assessment(_patient("Elena", "Permisos", "5511000003"), owner_id)

    other = app.test_client()
    _login(other, "other-v111")
    detail = other.get(f"/valoraciones/valoraciones/{assessment_id}")
    forbidden = other.post(
        f"/valoraciones/valoraciones/{assessment_id}/cerrar",
        data={"csrf_token": csrf_from(detail), "operation_key": str(uuid4()), "confirmar_cierre": "si"},
    )
    assert forbidden.status_code == 403
    no_csrf = other.post(
        f"/valoraciones/valoraciones/{assessment_id}/cerrar",
        data={"operation_key": str(uuid4()), "confirmar_cierre": "si"},
    )
    assert no_csrf.status_code == 400
    with app.app_context():
        assert NotaCierreClinico.query.count() == 0
        denied = AuditLog.query.filter_by(action="CERRAR_NOTA_CLINICA", outcome="denied").one()
        assert denied.entity_id == assessment_id


def test_appointment_search_does_not_match_hidden_email(app, client, login):
    login()
    with app.app_context():
        _patient("Sofía", "Ramírez", "5511000004", email="demo.sofia@example.test")
        db.session.commit()
    assert client.get("/pacientes/buscar_para_cita?busqueda=em").get_json()["resultados"] == []
    result = client.get("/pacientes/buscar_para_cita?busqueda=sofi").get_json()["resultados"]
    assert len(result) == 1
    assert result[0]["nombre"].startswith("Sofía")


def test_histories_and_recipe_consultations_filter_sort_and_show_new_conditions(app, client, login):
    login()
    with app.app_context():
        admin_id = Usuario.find_by_username("administrator").id
        ana = _patient("Ana", "Zúñiga", "5511000005")
        bea = _patient("Beatriz", "Álvarez", "5511000006")
        db.session.add_all([
            HistorialClinico(paciente_id=ana.id, enfermedades_previas="Asma persistente", actividad_fisica="Caminata", antecedente_asma_epoc=True, antecedente_enfermedad_renal=True),
            HistorialClinico(paciente_id=bea.id, enfermedades_previas="Hipertensión", actividad_fisica="Yoga", antecedente_tiroides=True),
        ])
        ana_id = ana.id
        _assessment(ana, admin_id, date.today() - timedelta(days=1), "Control respiratorio")
        _assessment(bea, admin_id, date.today(), "Revisión tiroidea")

    history_page = client.get("/historial-clinico/").get_data(as_text=True)
    assert "Asma o enfermedad pulmonar" in history_page
    assert history_page.index("Ana Zúñiga") < history_page.index("Beatriz Álvarez")
    filtered_history = client.get("/historial-clinico/?q=asma").get_data(as_text=True)
    assert "Ana Zúñiga" in filtered_history and "Beatriz Álvarez" not in filtered_history
    renal_history = client.get("/historial-clinico/?q=renal").get_data(as_text=True)
    assert "Ana Zúñiga" in renal_history and "Beatriz Álvarez" not in renal_history
    form = client.get(f"/historial-clinico/paciente/{ana_id}").get_data(as_text=True)
    assert "Asma o enfermedad pulmonar" in form
    assert "Enfermedad renal" in form
    assert "Colesterol o triglicéridos altos" in form

    recipes = client.get("/valoraciones/?origen=recetas&q=tiroidea").get_data(as_text=True)
    assert "Beatriz Álvarez" in recipes and "Ana Zúñiga" not in recipes
    ordered = client.get("/valoraciones/?origen=recetas&orden=paciente_asc").get_data(as_text=True)
    assert ordered.index("Ana Zúñiga") < ordered.index("Beatriz Álvarez")
    assert 'aria-sort="ascending"' in ordered


def test_user_management_is_clear_and_status_change_still_requires_csrf(client, login):
    login()
    page = client.get("/usuarios")
    body = page.get_data(as_text=True)
    assert "Con acceso" in body
    assert "Sin acceso" in body
    assert "Cuentas inhabilitadas" in body
    assert "Acciones Rápidas" not in body
    assert "user_management.js" in body
    assert client.post("/usuarios/1/cambiar-estatus").status_code == 400
