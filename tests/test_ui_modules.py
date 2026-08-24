from datetime import date, time
from pathlib import Path

from app import db_orm as db
from app.models.cita import Cita
from app.models.historial_clinico import HistorialClinico
from app.models.paciente import Paciente
from app.models.plantilla import PlantillaMensaje
from app.models.valoracion_antropometrica import ValoracionAntropometrica


def _patient(name="Marina", phone="5512345678"):
    patient = Paciente(
        nombre=name,
        apellido_paterno="García",
        apellido_materno="López",
        genero="mujer",
        fecha_nacimiento=date(1990, 5, 10),
        telefono=phone,
        correo=f"{name.lower()}@example.test",
        ciudad="Ciudad de México",
        status="activo",
    )
    db.session.add(patient)
    db.session.commit()
    return patient


def _assessment(patient_id):
    assessment = ValoracionAntropometrica(
        paciente_id=patient_id,
        numero_cita=1,
        fecha=date.today(),
        motivo_consulta="Revisión de seguimiento",
        sintomas="Cefalea ocasional",
        impresion_diagnostica="Cefalea en estudio",
        plan_tratamiento="Vigilancia y control",
        prescripcion="Hidratación y reposo",
        tension_arterial="120/80",
        frecuencia_cardiaca=72,
        frecuencia_respiratoria=16,
        temperatura=36.5,
        saturacion_oxigeno=98,
        estatura=170,
        peso=70,
        imc=24.2,
    )
    db.session.add(assessment)
    db.session.commit()
    return assessment


def test_history_list_uses_current_model_fields(app, client, login):
    login()
    with app.app_context():
        patient = _patient()
        db.session.add(
            HistorialClinico(
                paciente_id=patient.id,
                enfermedades_previas="Asma controlada",
                alergias_medicamentosas="Penicilina",
                medicamentos_actuales="Ninguno",
                actividad_fisica="Caminata tres veces por semana",
            )
        )
        db.session.commit()

    response = client.get("/historial-clinico/")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Marina García López" in page
    assert "Asma controlada" in page
    assert "Penicilina" in page
    assert "Caminata tres veces por semana" in page
    assert "tipo_actividad_fisica" not in page
    assert "Antecedentes y padecimientos" in page


def test_patient_history_and_consultation_empty_states(client, login):
    login()
    patients = client.get("/pacientes/activos").get_data(as_text=True)
    histories = client.get("/historial-clinico/").get_data(as_text=True)
    assessments = client.get("/valoraciones/").get_data(as_text=True)

    assert "No hay pacientes activos registrados" in patients
    assert "Registrar paciente" in patients
    assert "No hay historiales clínicos registrados" in histories
    assert "No hay consultas clínicas registradas" in assessments


def test_patient_search_accepts_phone_and_email(app):
    with app.app_context():
        patient = _patient(phone="5511112233")
        assert Paciente.buscar("111122")[0].id == patient.id
        assert Paciente.buscar("marina@example.test")[0].id == patient.id


def test_dashboard_kpis_match_persisted_records(app, client, login):
    login()
    with app.app_context():
        patient = _patient()
        db.session.add(HistorialClinico(paciente_id=patient.id, enfermedades_previas="Asma"))
        db.session.add(PlantillaMensaje(titulo="Seguimiento", contenido="Hola {nombre}", esta_activa=True))
        db.session.add(
            Cita(
                paciente_id=patient.id,
                fecha=date.today(),
                hora=time(9, 30),
                motivo="Consulta de seguimiento",
                estatus="Programada",
            )
        )
        db.session.commit()
        _assessment(patient.id)

    page = client.get("/").get_data(as_text=True)
    assert 'data-kpi="pacientes">1</strong>' in page
    assert 'data-kpi="citas-hoy">1</strong>' in page
    assert 'data-kpi="consultas-mes">1</strong>' in page
    assert 'data-kpi="ingresos"' not in page
    assert "Ingresos del mes" not in page
    assert "Agenda de hoy" in page
    assert "Resumen de pacientes" in page
    assert "Pacientes recientes" in page
    assert "Pendientes de atención" in page
    assert "Actividad reciente" in page
    assert "Acompañamiento Intermedio (14-15 Días)" in page
    assert "Consulta de seguimiento" in page
    assert "EXP-0001" in page
    assert 'static/css/dashboard.css' in page
    assert 'class="fas fa-users"' in page
    assert 'class="fas fa-file-medical"' in page
    assert 'class="fas fa-weight"' in page
    assert "WhatsApp / SMS" not in page


def test_consultation_tabs_use_local_navigation(app, client, login):
    login()
    with app.app_context():
        patient_id = _patient().id

    page = client.get(f"/valoraciones/paciente/{patient_id}/nueva").get_data(as_text=True)
    script = (Path(__file__).parents[1] / "app" / "static" / "js" / "tabs.js").read_text(encoding="utf-8")

    assert 'id="formValoracion"' in page
    assert "data-tabs" in page
    assert page.count('role="tab"') == 4
    assert 'data-tab-target="vitales"' in page
    assert 'data-tab-panel="vitales" class="space-y-5" hidden' in page
    assert "activeTab" not in page
    assert '/static/js/tabs.js' in page
    assert "ArrowRight" in script
    assert "panel.hidden = !activo" in script
    assert "formulario.addEventListener('invalid'" in script


def test_print_view_is_standalone_and_contains_clinical_note(app, client, login):
    anonymous = app.test_client()
    assert anonymous.get("/valoraciones/valoraciones/1/imprimir").status_code == 302

    login()
    with app.app_context():
        patient = _patient()
        assessment = _assessment(patient.id)
        assessment_id = assessment.id

    detail = client.get(f"/valoraciones/valoraciones/{assessment_id}").get_data(as_text=True)
    response = client.get(f"/valoraciones/valoraciones/{assessment_id}/imprimir")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert f'/valoraciones/valoraciones/{assessment_id}/imprimir' in detail
    assert "onclick=\"window.print()\"" not in detail
    assert "Nota de consulta clínica" in page
    assert "Marina García López" in page
    assert "Revisión de seguimiento" in page
    assert "Cefalea ocasional" in page
    assert "120/80 mmHg" in page
    assert "Hidratación y reposo" in page
    assert "Guardar como PDF" in page
    assert "Encabezados y pies de página" in page
    assert "print-sheet" in page
    assert "@media print" in page
    assert "Cerrar Sesión" not in page
    assert "cdn.tailwindcss.com" not in page
