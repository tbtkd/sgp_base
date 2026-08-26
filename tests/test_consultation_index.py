import io
from datetime import date, timedelta

from app import db_orm as db
from app.core.audit import AuditLog
from app.models.cita import Cita
from app.models.paciente import Paciente
from app.models.pago import Pago
from app.models.usuario import Usuario
from app.models.valoracion_antropometrica import ValoracionAntropometrica
from seed_demo import create_demo_workbook, seed_demo_data
from tests.conftest import csrf_from


def _patient(name, paternal, phone):
    patient = Paciente(
        nombre=name,
        apellido_paterno=paternal,
        apellido_materno="Demo",
        genero="mujer",
        fecha_nacimiento=date(1990, 1, 1),
        telefono=phone,
        correo=f"{phone}@example.test",
        ciudad="Ciudad de México",
        status="activo",
    )
    db.session.add(patient)
    db.session.flush()
    return patient


def _assessment(patient, when, number, reason):
    assessment = ValoracionAntropometrica(
        paciente_id=patient.id,
        numero_cita=number,
        fecha=when,
        motivo_consulta=reason,
        impresion_diagnostica=f"Diagnóstico {reason}",
    )
    db.session.add(assessment)
    db.session.flush()
    return assessment


def _professional(username, profile):
    user = Usuario(
        username=username,
        nombre="Profesional",
        apellido_paterno="Pruebas",
        email=f"{username}@example.test",
        rol="medico",
        perfil_profesional=profile,
        status="activo",
    )
    user.set_password("StrongPass!2026")
    db.session.add(user)
    db.session.commit()
    return user


def _login(client, username, password="StrongPass!2026"):
    page = client.get("/login")
    return client.post(
        "/login",
        data={
            "username": username,
            "password": password,
            "csrf_token": csrf_from(page),
        },
    )


def test_consultation_index_lists_each_patient_once_and_opens_latest_note(app, client, login):
    login()
    with app.app_context():
        patient = _patient("Laura", "Méndez", "5501000001")
        old = _assessment(patient, date.today() - timedelta(days=1), 1, "Nota anterior")
        same_day_first = _assessment(patient, date.today(), 1, "Nota del mismo día")
        latest = _assessment(patient, date.today(), 2, "Nota determinista más reciente")
        db.session.commit()
        latest_id = latest.id
        assert old.id != same_day_first.id != latest.id

    page = client.get("/valoraciones/").get_data(as_text=True)
    assert page.count("Laura Méndez Demo") == 1
    assert f'/valoraciones/valoraciones/{latest_id}' in page
    assert "Nota anterior" not in page
    assert "Nota determinista más reciente" not in page
    assert "Motivo" not in page
    assert "Diagnóstico" not in page
    assert "Última nota registrada de cada paciente" in page


def test_consultation_search_order_and_invalid_parameters_are_server_controlled(app, client, login):
    login()
    with app.app_context():
        first = _patient("Ana", "Álvarez", "5501000002")
        second = _patient("Brenda", "Zúñiga", "5501000003")
        _assessment(first, date.today() - timedelta(days=5), 1, "Primera")
        _assessment(second, date.today(), 1, "Segunda")
        db.session.commit()

    filtered = client.get("/valoraciones/?q=ana+alva").get_data(as_text=True)
    assert "Ana Álvarez Demo" in filtered
    assert "Brenda Zúñiga Demo" not in filtered
    assert "1 paciente encontrado" in filtered

    ascending = client.get("/valoraciones/?orden=fecha_asc").get_data(as_text=True)
    assert ascending.index("Ana Álvarez Demo") < ascending.index("Brenda Zúñiga Demo")
    assert 'aria-sort="ascending"' in ascending

    invalid = client.get("/valoraciones/?orden=fecha;DROP+TABLE&page=no-numero")
    assert invalid.status_code == 200
    invalid_page = invalid.get_data(as_text=True)
    assert 'aria-sort="descending"' in invalid_page
    assert invalid_page.index("Brenda Zúñiga Demo") < invalid_page.index("Ana Álvarez Demo")


def test_consultation_index_paginates_without_repeating_patients(app, client, login):
    login()
    with app.app_context():
        for index in range(26):
            patient = _patient(f"Paciente{index:02d}", "Paginación", f"551000{index:04d}")
            _assessment(patient, date.today() - timedelta(days=index), index + 1, f"Consulta {index}")
        db.session.commit()

    first_page = client.get("/valoraciones/").get_data(as_text=True)
    second_page = client.get("/valoraciones/?page=2").get_data(as_text=True)
    assert "26 pacientes encontrados" in first_page
    assert "Página 1 de 2" in first_page
    assert "Siguiente" in first_page
    assert "Página 2 de 2" in second_page
    assert "Anterior" in second_page
    assert "Paciente00 Paginación Demo" in first_page
    assert "Paciente00 Paginación Demo" not in second_page
    assert "Paciente25 Paginación Demo" in second_page


def test_recipe_context_keeps_specific_historical_consultations(app, client, login):
    login()
    with app.app_context():
        patient = _patient("Rosa", "Recetas", "5501000004")
        _assessment(patient, date.today() - timedelta(days=1), 1, "Consulta anterior para receta")
        _assessment(patient, date.today(), 1, "Consulta actual para receta")
        db.session.commit()

    page = client.get("/valoraciones/?origen=recetas").get_data(as_text=True)
    assert page.count("Rosa Recetas Demo") == 2
    assert "Consulta anterior para receta" in page
    assert "Consulta actual para receta" in page
    assert "Selecciona la consulta específica" in page


def test_excel_import_controls_are_only_rendered_for_nutrition(app, client, login):
    login()
    with app.app_context():
        patient = _patient("Nora", "Nutrición", "5501000005")
        db.session.commit()
        patient_id = patient.id

    nutrition_page = client.get(f"/pacientes/{patient_id}").get_data(as_text=True)
    assert "Importar Excel" in nutrition_page
    assert 'id="formCargarExcel"' in nutrition_page
    assert 'id="modalResultadoCarga"' in nutrition_page

    with app.app_context():
        _professional("doctor-no-import", "medico_general")
    doctor_client = app.test_client()
    _login(doctor_client, "doctor-no-import")
    doctor_page = doctor_client.get(f"/pacientes/{patient_id}").get_data(as_text=True)
    assert "Importar Excel" not in doctor_page
    assert 'id="formCargarExcel"' not in doctor_page
    assert 'id="modalResultadoCarga"' not in doctor_page


def test_forged_excel_import_is_denied_and_audited_before_patient_lookup(app):
    with app.app_context():
        doctor = _professional("doctor-forged-import", "medico_general")
        doctor_id = doctor.id
    doctor_client = app.test_client()
    _login(doctor_client, "doctor-forged-import")
    token = csrf_from(doctor_client.get("/pacientes/activos"))
    response = doctor_client.post(
        "/pacientes/999999/cargar-excel",
        data={
            "csrf_token": token,
            "file": (io.BytesIO(b"not-an-xlsx"), "ataque.xlsx"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 403
    assert "sólo está disponible para profesionales de Nutrición" in response.get_json()["message"]
    with app.app_context():
        denied = AuditLog.query.filter_by(user_id=doctor_id, action="IMPORTAR_CONSULTAS").one()
        assert denied.outcome == "denied"
        assert "professional_profile_not_allowed" in denied.metadata_json


def test_demo_seed_is_idempotent_and_generates_importable_workbook(app, tmp_path):
    first = seed_demo_data(app, password="DemoSeed!2026-Segura")
    second = seed_demo_data(app, password="AnotherDemo!2026-Segura")
    workbook_path = create_demo_workbook(tmp_path / "demo.xlsx")

    assert first["usuarios"] == [
        "demo_admin",
        "demo_medico",
        "demo_dentista",
        "demo_nutricion",
        "demo_recepcion",
    ]
    assert first["pacientes"] == 6
    assert first["consultas"] == 9
    assert first["citas"] == 7
    assert first["pagos"] == 18
    assert first["recetas"] == 1
    assert second["usuarios"] == []
    assert second["pacientes"] == 0
    assert second["consultas"] == 0
    assert second["citas"] == 0
    assert second["pagos"] == 0
    assert second["recetas"] == 0
    assert workbook_path.is_file()

    with app.app_context():
        assert Usuario.find_by_username("demo_admin").rol_clinico == "admin"
        assert Usuario.find_by_username("demo_nutricion").puede_capturar_antropometria
        assert not Usuario.find_by_username("demo_medico").puede_capturar_antropometria
        assert Paciente.query.filter(Paciente.telefono.like("55000001%")).count() == 6
        assert Cita.query.filter(Cita.estatus == "Programada").count() == 4
        assert Cita.query.filter(Cita.estatus == "Atendida").count() == 1
        assert Cita.query.filter(Cita.estatus == "No Asistió").count() == 1
        assert Cita.query.filter(Cita.estatus == "Cancelada").count() == 1
        assert Pago.query.filter(Pago.estatus == "vigente").count() == 16
        assert Pago.query.filter(Pago.estatus == "cancelado").count() == 1
        assert Pago.query.filter(Pago.estatus == "requiere_revision").count() == 1
        linked = Pago.query.filter_by(concepto="Consulta demostrativa").first()
        assert linked.cita_id is not None
        unlinked = Pago.query.filter_by(concepto="Cobro sin cita aunque existe una programada").one()
        assert unlinked.cita_id is None
        assert Cita.obtener_cita_pendiente(unlinked.paciente_id) is not None
        review = Pago.query.filter_by(concepto="Pago legado incompleto para revisión").one()
        assert review.monto_centavos == 0
        assert review.usuario_registro_id is None
        prescription = ValoracionAntropometrica.query.filter_by(
            motivo_consulta="Consulta más reciente demostrativa"
        ).one().recetas[0]
        assert [item.denominacion_generica for item in prescription.medicamentos] == [
            "Paracetamol",
            "Loratadina",
            "Solución salina",
        ]


def test_demo_workbook_is_accepted_by_nutrition_import_flow(app, tmp_path):
    seed_demo_data(app, password="DemoSeed!2026-Segura")
    workbook_path = create_demo_workbook(tmp_path / "demo-import.xlsx")
    with app.app_context():
        patient = Paciente.query.filter_by(telefono="5500000102").one()
        patient_id = patient.id
        before = ValoracionAntropometrica.query.filter_by(paciente_id=patient_id).count()

    nutrition_client = app.test_client()
    _login(nutrition_client, "demo_nutricion", "DemoSeed!2026-Segura")
    token = csrf_from(nutrition_client.get(f"/pacientes/{patient_id}"))
    response = nutrition_client.post(
        f"/pacientes/{patient_id}/cargar-excel",
        data={
            "csrf_token": token,
            "file": (io.BytesIO(workbook_path.read_bytes()), "demo-import.xlsx"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    result = response.get_json()
    assert result["success"] is True
    assert result["registros_procesados"] == 3
    with app.app_context():
        assert ValoracionAntropometrica.query.filter_by(paciente_id=patient_id).count() == before + 3
