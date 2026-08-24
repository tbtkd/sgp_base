import sqlite3
import tempfile
from datetime import date
from pathlib import Path

import pytest

from app import create_app
from app import db_orm as db
from app.core.validators import ValidationError, professional_license, user_payload
from app.models.paciente import Paciente
from app.models.usuario import Usuario
from app.models.valoracion_antropometrica import ValoracionAntropometrica
from tests.conftest import csrf_from


def _user(username, profile, *, license_number=None, role="medico"):
    user = Usuario(
        username=username,
        nombre="Profesional",
        apellido_paterno="Pruebas",
        email=f"{username}@example.test",
        rol=role,
        perfil_profesional=profile,
        cedula_profesional=license_number,
        status="activo",
    )
    user.set_password("ProfessionalPass!2026")
    db.session.add(user)
    db.session.commit()
    return user


def _patient():
    patient = Paciente(
        nombre="Laura",
        apellido_paterno="Salud",
        genero="mujer",
        fecha_nacimiento=date(1990, 1, 1),
        telefono="5512345678",
        ciudad="Ciudad de México",
        status="activo",
    )
    db.session.add(patient)
    db.session.commit()
    return patient


def _login(client, username):
    token = csrf_from(client.get("/login"))
    response = client.post(
        "/login",
        data={
            "username": username,
            "password": "ProfessionalPass!2026",
            "csrf_token": token,
        },
    )
    assert response.status_code == 302


def _consultation_form(**extra):
    data = {
        "numero_cita": "1",
        "fecha": date.today().isoformat(),
        "motivo_consulta": "Consulta de prueba",
        "sintomas": "Sin datos de alarma",
        "prescripcion": "Indicaciones de prueba",
    }
    data.update(extra)
    return data


def test_professional_profile_and_license_are_validated():
    base = {
        "nombre": "Claudia",
        "apellido_paterno": "Médica",
        "apellido_materno": "Pruebas",
        "email": "claudia@example.test",
        "rol": "medico",
        "cedula_profesional": "12345678",
    }
    with pytest.raises(ValidationError, match="perfil profesional"):
        user_payload(base, include_password=False)

    data = user_payload({**base, "perfil_profesional": "dentista"}, include_password=False)
    assert data["perfil_profesional"] == "dentista"
    assert data["cedula_profesional"] == "12345678"

    reception = user_payload(
        {**base, "rol": "recepcion", "perfil_profesional": "nutricion", "cedula_profesional": "inválida"},
        include_password=False,
    )
    assert reception["perfil_profesional"] is None
    assert reception["cedula_profesional"] == ""
    with pytest.raises(ValidationError, match="5 y 12 dígitos"):
        professional_license("123")


def test_user_registration_persists_professional_profile(app, client, login):
    login()
    page_response = client.get("/registrar-usuario")
    page = page_response.get_data(as_text=True)
    assert 'name="perfil_profesional"' in page
    assert 'value="medico_general"' in page
    assert 'value="dentista"' in page
    assert 'value="nutricion"' in page
    assert 'name="domicilio_profesional"' in page
    assert 'name="nombre_establecimiento"' in page
    assert "usuario_profesional.js" in page

    token = csrf_from(page_response)
    response = client.post(
        "/registrar-usuario",
        data={
            "csrf_token": token,
            "nombre": "Daniel",
            "apellido_paterno": "Dental",
            "apellido_materno": "Pruebas",
            "username": "dentista",
            "email": "dentista@example.test",
            "rol": "medico",
            "perfil_profesional": "dentista",
            "cedula_profesional": "87654321",
            "nombre_establecimiento": "Clínica Dental Pruebas",
            "domicilio_profesional": "Av. Salud 123, C.P. 06000, Ciudad de México",
            "password": "DentistSecure!2026",
        },
    )
    assert response.status_code == 302
    with app.app_context():
        user = Usuario.find_by_username("dentista")
        assert user.perfil_profesional_clinico == "dentista"
        assert user.cedula_profesional == "87654321"
        assert user.nombre_establecimiento == "Clínica Dental Pruebas"
        assert user.domicilio_profesional == "Av. Salud 123, C.P. 06000, Ciudad de México"


def test_only_nutrition_can_capture_anthropometry_and_snapshot_author(app):
    with app.app_context():
        _user("general", "medico_general", license_number="11112222")
        nutritionist = _user("nutrition", "nutricion", license_number="33334444")
        patient = _patient()
        patient_id = patient.id
        nutritionist_id = nutritionist.id

    doctor_client = app.test_client()
    _login(doctor_client, "general")
    doctor_page_response = doctor_client.get(f"/valoraciones/paciente/{patient_id}/nueva")
    doctor_page = doctor_page_response.get_data(as_text=True)
    assert doctor_page.count('role="tab"') == 3
    assert 'data-tab-target="antropometria"' not in doctor_page
    assert 'name="cintura"' not in doctor_page

    forged = _consultation_form(cintura="90", csrf_token=csrf_from(doctor_page_response))
    response = doctor_client.post(f"/valoraciones/paciente/{patient_id}/nueva", data=forged)
    assert response.status_code == 200
    assert "sólo está disponible para profesionales de Nutrición" in response.get_data(as_text=True)
    with app.app_context():
        assert ValoracionAntropometrica.query.count() == 0

    nutrition_client = app.test_client()
    _login(nutrition_client, "nutrition")
    nutrition_page_response = nutrition_client.get(f"/valoraciones/paciente/{patient_id}/nueva")
    nutrition_page = nutrition_page_response.get_data(as_text=True)
    assert nutrition_page.count('role="tab"') == 4
    assert 'data-tab-target="antropometria"' in nutrition_page
    assert 'name="cintura"' in nutrition_page

    valid = _consultation_form(cintura="88", csrf_token=csrf_from(nutrition_page_response))
    response = nutrition_client.post(f"/valoraciones/paciente/{patient_id}/nueva", data=valid)
    assert response.status_code == 302
    with app.app_context():
        assessment = ValoracionAntropometrica.query.one()
        assessment_id = assessment.id
        assert assessment.cintura == 88
        assert assessment.profesional_id == nutritionist_id
        assert assessment.profesional_nombre == "Profesional Pruebas"
        assert assessment.profesional_cedula == "33334444"
        assert assessment.profesional_perfil == "nutricion"
        Usuario.get(nutritionist_id).cedula_profesional = "99990000"
        db.session.commit()

    printable = nutrition_client.get(f"/valoraciones/valoraciones/{assessment_id}/imprimir").get_data(
        as_text=True
    )
    assert "Indicaciones nutricionales / plan alimentario" in printable
    assert "Prescripción / receta médica" not in printable
    assert "Cédula profesional:</strong> 33334444" in printable
    assert "99990000" not in printable


def test_print_omits_professional_license_when_it_is_missing(app):
    with app.app_context():
        doctor = _user("doctor-no-license", "medico_general")
        patient = _patient()
        assessment = ValoracionAntropometrica.crear(
            patient.id,
            {
                "numero_cita": 1,
                "fecha": date.today(),
                "motivo_consulta": "Revisión general",
                "prescripcion": "Tratamiento de prueba",
            },
            profesional=doctor,
        )
        db.session.commit()
        assessment_id = assessment.id
        doctor.cedula_profesional = "55556666"
        db.session.commit()

    doctor_client = app.test_client()
    _login(doctor_client, "doctor-no-license")
    printable = doctor_client.get(f"/valoraciones/valoraciones/{assessment_id}/imprimir").get_data(
        as_text=True
    )
    assert "Profesional Pruebas" in printable
    assert "Medicina general" in printable
    assert "Indicaciones terapéuticas en la nota clínica" in printable
    assert "corresponde a una nota clínica" in printable
    assert "Cédula profesional:" not in printable
    assert "55556666" not in printable


def test_general_professional_edit_preserves_existing_anthropometry(app):
    with app.app_context():
        nutritionist = _user("nutrition-edit", "nutricion")
        _user("general-edit", "medico_general")
        patient = _patient()
        assessment = ValoracionAntropometrica.crear(
            patient.id,
            {
                "numero_cita": 1,
                "fecha": date.today(),
                "motivo_consulta": "Valoración nutricional",
                "cintura": 84,
            },
            profesional=nutritionist,
        )
        db.session.commit()
        assessment_id = assessment.id

    doctor_client = app.test_client()
    _login(doctor_client, "general-edit")
    edit_page = doctor_client.get(f"/valoraciones/valoraciones/{assessment_id}/editar")
    assert 'name="cintura"' not in edit_page.get_data(as_text=True)
    response = doctor_client.post(
        f"/valoraciones/valoraciones/{assessment_id}/editar",
        data=_consultation_form(
            motivo_consulta="Seguimiento general",
            csrf_token=csrf_from(edit_page),
        ),
    )
    assert response.status_code == 302
    with app.app_context():
        assessment = db.session.get(ValoracionAntropometrica, assessment_id)
        assert assessment.motivo_consulta == "Seguimiento general"
        assert assessment.cintura == 84


def test_professional_snapshot_columns_migrate_without_data_loss():
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "legacy-professional.db"
        connection = sqlite3.connect(database)
        connection.executescript(
            """
            CREATE TABLE pacientes (
                id INTEGER PRIMARY KEY, nombre VARCHAR(60) NOT NULL,
                apellido_paterno VARCHAR(60) NOT NULL, apellido_materno VARCHAR(60),
                genero VARCHAR(30) NOT NULL, fecha_nacimiento DATE NOT NULL,
                telefono VARCHAR(10) NOT NULL, correo VARCHAR(254), ciudad VARCHAR(100) NOT NULL,
                fecha_registro DATETIME NOT NULL, status VARCHAR(20) NOT NULL
            );
            INSERT INTO pacientes VALUES
                (1,'Laura','Salud',NULL,'mujer','1990-01-01','5512345678',NULL,'México','2026-01-01','activo');
            CREATE TABLE valoracion_antropometrica (
                id INTEGER PRIMARY KEY, paciente_id INTEGER NOT NULL,
                numero_cita INTEGER NOT NULL, fecha DATE NOT NULL, motivo_consulta TEXT
            );
            INSERT INTO valoracion_antropometrica VALUES
                (1,1,1,'2026-01-02','Consulta legada');
            """
        )
        connection.commit()
        connection.close()

        migration_app = create_app(
            "testing",
            {
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database.as_posix()}",
                "AUTO_BACKUP_DATABASE": False,
            },
        )
        with migration_app.app_context():
            db.session.remove()
            db.engine.dispose()

        connection = sqlite3.connect(database)
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(valoracion_antropometrica)")
        }
        saved = connection.execute(
            "SELECT motivo_consulta FROM valoracion_antropometrica WHERE id=1"
        ).fetchone()
        connection.close()

        assert {
            "profesional_id",
            "profesional_nombre",
            "profesional_cedula",
            "profesional_perfil",
        } <= columns
        assert saved == ("Consulta legada",)
