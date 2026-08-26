import sqlite3
import tempfile
from datetime import date
from pathlib import Path

import pytest

from app import create_app
from app import db_orm as db
from app.core.validators import ValidationError, prescription_payload
from app.db import _migrate_prescription_versions, init_db
from app.models.bitacora import AuditLog
from app.models.historial_clinico import HistorialClinico
from app.models.paciente import Paciente
from app.models.receta import Receta
from app.models.usuario import Usuario
from app.models.valoracion_antropometrica import ValoracionAntropometrica
from tests.conftest import csrf_from


def _professional(username, profile, *, license_number="12345678", address=None):
    user = Usuario(
        username=username,
        nombre="Elena",
        apellido_paterno="Profesional",
        email=f"{username}@example.test",
        rol="medico",
        perfil_profesional=profile,
        cedula_profesional=license_number,
        nombre_establecimiento="Clínica de Pruebas",
        domicilio_profesional=address,
        status="activo",
    )
    user.set_password("ProfessionalPass!2026")
    db.session.add(user)
    db.session.commit()
    return user


def _patient_and_assessment(professional):
    patient = Paciente(
        nombre="María",
        apellido_paterno="Paciente",
        genero="mujer",
        fecha_nacimiento=date(1992, 4, 5),
        telefono="5512345678",
        ciudad="Ciudad de México",
        status="activo",
    )
    db.session.add(patient)
    db.session.flush()
    assessment = ValoracionAntropometrica.crear(
        patient.id,
        {
            "numero_cita": 1,
            "fecha": date.today(),
            "motivo_consulta": "Seguimiento",
            "prescripcion": "Indicaciones asentadas en la nota",
        },
        profesional=professional,
    )
    db.session.commit()
    return patient, assessment


def _login(client, username):
    token = csrf_from(client.get("/login"))
    response = client.post(
        "/login",
        data={"username": username, "password": "ProfessionalPass!2026", "csrf_token": token},
    )
    assert response.status_code == 302


def _prescription_data(token, count=1):
    return {
        "csrf_token": token,
        "confirmacion_competencia": "on",
        "confirmacion_ordinaria": "on",
        "confirmacion_firma": "on",
        "denominacion_generica[]": ["Paracetamol"] * count,
        "denominacion_distintiva[]": [""] * count,
        "presentacion[]": ["Tabletas de 500 mg"] * count,
        "dosis[]": ["500 mg"] * count,
        "via_administracion[]": ["Oral"] * count,
        "frecuencia[]": ["Cada 8 horas"] * count,
        "duracion[]": ["3 días"] * count,
        "cantidad[]": ["9 tabletas"] * count,
        "indicaciones[]": ["Tomar con agua"] * count,
        "observaciones": "Suspender y consultar ante una reacción adversa.",
    }


def test_prescription_requires_authorized_profile_and_complete_professional_data(app):
    with app.app_context():
        nutrition = _professional("nutrition-rx", "nutricion", address="Av. Salud 1, C.P. 01000, CDMX")
        patient, assessment = _patient_and_assessment(nutrition)
        assessment_id = assessment.id
        patient_id = patient.id

    client = app.test_client()
    assert client.get(f"/recetas/valoracion/{assessment_id}/nueva").status_code == 302
    _login(client, "nutrition-rx")
    response = client.get(f"/recetas/valoracion/{assessment_id}/nueva")
    assert response.status_code == 403

    with app.app_context():
        doctor = _professional("doctor-incomplete", "medico_general", address=None)
        assessment = ValoracionAntropometrica.crear(
            patient_id,
            {"numero_cita": 2, "fecha": date.today(), "motivo_consulta": "Nueva consulta"},
            profesional=doctor,
        )
        db.session.commit()
        doctor_assessment_id = assessment.id

    incomplete = app.test_client()
    _login(incomplete, "doctor-incomplete")
    page_response = incomplete.get(f"/recetas/valoracion/{doctor_assessment_id}/nueva")
    page = page_response.get_data(as_text=True)
    assert "No es posible emitir todavía" in page
    assert "domicilio profesional completo" in page
    response = incomplete.post(
        f"/recetas/valoracion/{doctor_assessment_id}/nueva",
        data=_prescription_data(csrf_from(page_response)),
    )
    assert response.status_code == 422
    with app.app_context():
        assert Receta.query.count() == 0


def test_inactive_patient_cannot_receive_a_new_prescription(app):
    address = "Av. Salud 123, Col. Centro, C.P. 06000, Ciudad de México"
    with app.app_context():
        doctor = _professional("doctor-inactive", "medico_general", address=address)
        patient, assessment = _patient_and_assessment(doctor)
        patient.status = "inactivo"
        db.session.commit()
        assessment_id = assessment.id
    client = app.test_client()
    _login(client, "doctor-inactive")
    response = client.get(f"/recetas/valoracion/{assessment_id}/nueva", follow_redirects=True)
    assert response.status_code == 200
    assert "No es posible emitir una receta para un paciente inactivo" in response.get_data(as_text=True)
    with app.app_context():
        assert Receta.query.count() == 0


def test_create_print_and_audit_ordinary_prescription_with_immutable_snapshot(app):
    address = "Av. Salud 123, Col. Centro, C.P. 06000, Cuauhtémoc, Ciudad de México"
    with app.app_context():
        doctor = _professional("doctor-rx", "medico_general", address=address)
        patient, assessment = _patient_and_assessment(doctor)
        db.session.add(
            HistorialClinico(
                paciente_id=patient.id,
                alergias_medicamentosas="Penicilina",
                alergias_alimentarias="Ninguna conocida",
            )
        )
        db.session.commit()
        assessment_id = assessment.id
        doctor_id = doctor.id

    client = app.test_client()
    _login(client, "doctor-rx")
    detail = client.get(f"/valoraciones/valoraciones/{assessment_id}").get_data(as_text=True)
    assert "Generar receta" in detail
    assert "Indicaciones terapéuticas en la nota clínica" in detail

    page_response = client.get(f"/recetas/valoracion/{assessment_id}/nueva")
    response = client.post(
        f"/recetas/valoracion/{assessment_id}/nueva",
        data=_prescription_data(csrf_from(page_response)),
    )
    assert response.status_code == 302
    assert "/recetas/" in response.headers["Location"]

    with app.app_context():
        prescription = Receta.query.one()
        prescription_id = prescription.id
        prescription_folio = prescription.folio
        assert prescription.folio.startswith("RX-")
        assert prescription.profesional_nombre == "Elena Profesional"
        assert prescription.profesional_cedula == "12345678"
        assert prescription.domicilio_profesional == address
        assert prescription.alergias_conocidas == "Medicamentos: Penicilina | Alimentos: Ninguna conocida"
        assert len(prescription.medicamentos) == 1
        assert prescription.medicamentos[0].denominacion_generica == "Paracetamol"
        assert AuditLog.query.filter_by(action="CREAR_RECETA", entity_id=prescription.id).one()
        doctor = db.session.get(Usuario, doctor_id)
        doctor.cedula_profesional = "99999999"
        doctor.domicilio_profesional = "Domicilio modificado"
        db.session.commit()

    detail_with_prescription = client.get(
        f"/valoraciones/valoraciones/{assessment_id}"
    ).get_data(as_text=True)
    assert "prescription-replace-action" in detail_with_prescription
    assert f'aria-label="Sustituir receta {prescription_folio}"' in detail_with_prescription
    assert '<i class="fas fa-edit" aria-hidden="true"></i><span>Sustituir</span>' in detail_with_prescription

    printable = client.get(f"/recetas/{prescription_id}/imprimir").get_data(as_text=True)
    for required in (
        "Receta médica ordinaria",
        "Elena Profesional",
        "12345678",
        address,
        "Fecha de emisión",
        "Paracetamol",
        "Tabletas de 500 mg",
        "500 mg",
        "Oral",
        "Cada 8 horas",
        "3 días",
        "Firma autógrafa",
    ):
        assert required in printable
    assert "99999999" not in printable
    assert "Domicilio modificado" not in printable
    assert f"<strong>Domicilio:</strong> {address}" in printable
    assert "Domicilio profesional:" not in printable
    assert "Cerrar Sesión" not in printable
    assert "cdn.tailwindcss.com" not in printable
    assert printable.count("Elena Profesional") == 1
    assert printable.count("12345678") == 1
    assert "Fecha y sello" not in printable
    assert "data-prescriber-signature" in printable
    assert 'class="toolbar-replace"' in printable
    assert f'aria-label="Sustituir receta {prescription_folio}"' in printable
    assert "/static/img/logo.png?v=1.12.0-backup1" in printable
    assert 'margin: 14mm 12mm 12mm' in printable
    assert '@top-left { content: ""; }' in printable
    assert '@top-center { content: ""; }' in printable
    assert '@top-right { content: ""; }' in printable
    assert '@bottom-left { content: ""; }' in printable
    assert '@bottom-center { content: ""; }' in printable
    assert '@bottom-right { content: ""; }' in printable
    assert "data-print-prescription" in printable
    assert "addEventListener('click', printPrescription)" in printable
    assert 'document.title = " ";' in printable

    repeated = client.get(f"/recetas/valoracion/{assessment_id}/nueva")
    assert repeated.status_code == 302
    assert repeated.headers["Location"].endswith(f"/valoraciones/valoraciones/{assessment_id}")
    detail = client.get(repeated.headers["Location"]).get_data(as_text=True)
    assert "Receta adicional" in detail

    detail_response = client.get(f"/valoraciones/valoraciones/{assessment_id}")
    blocked_delete = client.post(
        f"/valoraciones/valoraciones/{assessment_id}/eliminar",
        data={"csrf_token": csrf_from(detail_response)},
    )
    assert blocked_delete.status_code == 302
    with app.app_context():
        assert db.session.get(Receta, prescription_id) is not None
        assert db.session.get(ValoracionAntropometrica, assessment_id) is not None


def test_prescription_server_validation_rejects_incomplete_or_excess_items():
    valid = _prescription_data("unused")
    valid.pop("csrf_token")
    parsed = prescription_payload(valid)
    assert parsed["medicamentos"][0]["frecuencia"] == "Cada 8 horas"

    incomplete = dict(valid)
    incomplete["duracion[]"] = []
    with pytest.raises(ValidationError, match="no coinciden"):
        prescription_payload(incomplete)

    with pytest.raises(ValidationError, match="máximo 10"):
        prescription_payload(_prescription_data("unused", count=11))

    uncontrolled = dict(valid)
    uncontrolled.pop("confirmacion_ordinaria")
    with pytest.raises(ValidationError, match="receta especial"):
        prescription_payload(uncontrolled)

    unsigned = dict(valid)
    unsigned.pop("confirmacion_firma")
    with pytest.raises(ValidationError, match="firmarás"):
        prescription_payload(unsigned)

    duplicated = _prescription_data("unused", count=2)
    duplicated.pop("csrf_token")
    with pytest.raises(ValidationError, match="duplica exactamente"):
        prescription_payload(duplicated)


def test_prescription_preserves_capture_order_when_new_rows_are_visually_prepended(app):
    data = _prescription_data("unused", count=3)
    data.pop("csrf_token")
    data["orden_medicamento[]"] = ["3", "2", "1"]
    data["denominacion_generica[]"] = ["Tercero", "Segundo", "Primero"]

    parsed = prescription_payload(data)
    assert [item["denominacion_generica"] for item in parsed["medicamentos"]] == [
        "Primero",
        "Segundo",
        "Tercero",
    ]

    invalid = dict(data)
    invalid["orden_medicamento[]"] = ["1", "1", "2"]
    with pytest.raises(ValidationError, match="consecutivo"):
        prescription_payload(invalid)

    root = Path(__file__).parents[1]
    script = (root / "app" / "static" / "js" / "recetas.js").read_text(encoding="utf-8")
    template = (root / "app" / "templates" / "recetas" / "nueva_receta.html").read_text(
        encoding="utf-8"
    )
    assert "list.prepend(fragment)" in script
    assert "list.appendChild" not in script
    assert "firstRequired.focus()" in script
    assert 'name="orden_medicamento[]"' in template


def test_prescription_print_uses_capture_order_one_to_n(app):
    address = "Av. Salud 123, Col. Centro, C.P. 06000, Ciudad de México"
    with app.app_context():
        doctor = _professional("doctor-order", "medico_general", address=address)
        _, assessment = _patient_and_assessment(doctor)
        assessment_id = assessment.id

    client = app.test_client()
    _login(client, "doctor-order")
    page = client.get(f"/recetas/valoracion/{assessment_id}/nueva")
    data = _prescription_data(csrf_from(page), count=6)
    data["orden_medicamento[]"] = ["6", "5", "4", "3", "2", "1"]
    data["denominacion_generica[]"] = [
        "Medicamento sexto",
        "Medicamento quinto",
        "Medicamento cuarto",
        "Medicamento tercero",
        "Medicamento segundo",
        "Medicamento primero",
    ]
    response = client.post(f"/recetas/valoracion/{assessment_id}/nueva", data=data)
    assert response.status_code == 302

    with app.app_context():
        prescription = Receta.query.one()
        prescription_id = prescription.id
        assert [item.denominacion_generica for item in prescription.medicamentos] == [
            "Medicamento primero",
            "Medicamento segundo",
            "Medicamento tercero",
            "Medicamento cuarto",
            "Medicamento quinto",
            "Medicamento sexto",
        ]

    printable = client.get(f"/recetas/{prescription_id}/imprimir").get_data(as_text=True)
    assert printable.index("1. Medicamento primero") < printable.index("2. Medicamento segundo")
    assert printable.index("2. Medicamento segundo") < printable.index("3. Medicamento tercero")
    assert printable.index("3. Medicamento tercero") < printable.index("6. Medicamento sexto")
    assert 'class="sheet sheet--dense"' in printable
    assert "data-compact-medication-list" in printable
    assert 'class="medicine-list"' in printable
    assert "Forma, presentación y concentración" not in printable
    assert 'class="grid"' not in printable


def test_account_identity_is_in_sidebar_and_icon_is_canonical(app, client, login):
    login()
    page = client.get("/").get_data(as_text=True)
    root = Path(__file__).parents[1]
    templates = root / "app" / "templates"
    sidebar = (templates / "components" / "_sidebar.html").read_text(encoding="utf-8")
    header = (templates / "components" / "_header.html").read_text(encoding="utf-8")
    app_script = (root / "app" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    template_sources = "\n".join(path.read_text(encoding="utf-8") for path in templates.rglob("*.html"))
    build = (root / "build_exe.bat").read_text(encoding="utf-8")

    assert page.count("Cerrar Sesión") == 1
    assert "Admin Pruebas Sistema" in page
    assert "Administrador · Nutrición" in page
    assert "Bienvenido," not in page
    assert "Dashboard" in page
    assert "Cerrar Sesión" in sidebar
    assert "auth.logout" in sidebar
    assert "current_user.nombre_completo" in sidebar
    assert "current_user.nombre_corto" not in header
    assert "current_user.username" not in header
    assert "data-account-menu-toggle" not in header
    assert "data-account-menu-panel" not in header
    assert "data-account-menu-toggle" in sidebar
    assert "data-account-menu-panel" in sidebar
    assert 'class="shell-account-more">...</button>' in sidebar
    assert "x-show=\"open\"" not in header
    assert "hidden>" in header
    assert "panel.hidden = true" in app_script
    assert "aria-expanded" in app_script
    assert "img/logo.png" in sidebar
    assert "img/logo.svg" not in template_sources
    assert 'app/static/img/logo.ico' in build
    assert (root / "app" / "static" / "img" / "logo.png").is_file()
    assert (root / "app" / "static" / "img" / "logo.ico").is_file()
    favicon = client.get("/favicon.ico")
    assert favicon.status_code == 200
    assert favicon.mimetype == "image/vnd.microsoft.icon"
    assert favicon.headers["Cache-Control"] == "no-cache, max-age=0, must-revalidate"
    assert "/static/img/logo.png?v=1.12.0-backup1" in page


def test_additional_and_replacement_prescriptions_preserve_every_folio(app):
    address = "Av. Salud 123, Col. Centro, C.P. 06000, Ciudad de México"
    with app.app_context():
        doctor = _professional("doctor-history", "medico_general", address=address)
        _, assessment = _patient_and_assessment(doctor)
        assessment_id = assessment.id

    client = app.test_client()
    _login(client, "doctor-history")
    page = client.get(f"/recetas/valoracion/{assessment_id}/nueva")
    assert client.post(
        f"/recetas/valoracion/{assessment_id}/nueva",
        data=_prescription_data(csrf_from(page)),
    ).status_code == 302

    additional_page = client.get(f"/recetas/valoracion/{assessment_id}/adicional")
    additional_data = _prescription_data(csrf_from(additional_page))
    additional_data["denominacion_generica[]"] = ["Ibuprofeno"]
    assert client.post(
        f"/recetas/valoracion/{assessment_id}/adicional", data=additional_data
    ).status_code == 302

    with app.app_context():
        original = Receta.query.filter_by(valoracion_id=assessment_id, version=1).one()
        original_id = original.id
        original_folio = original.folio

    replacement_page = client.get(f"/recetas/{original_id}/sustituir")
    replacement_data = _prescription_data(csrf_from(replacement_page))
    replacement_data["denominacion_generica[]"] = ["Paracetamol corregido"]
    replacement_data["motivo_cambio"] = "Corrección de la denominación asentada en el documento original."
    response = client.post(f"/recetas/{original_id}/sustituir", data=replacement_data)
    assert response.status_code == 302

    with app.app_context():
        documents = Receta.query.filter_by(valoracion_id=assessment_id).order_by(Receta.version).all()
        assert [document.tipo for document in documents] == ["original", "adicional", "sustitucion"]
        assert [document.version for document in documents] == [1, 2, 3]
        assert documents[0].estado == "sustituida"
        assert documents[1].estado == documents[2].estado == "vigente"
        assert documents[0].medicamentos[0].denominacion_generica == "Paracetamol"
        assert documents[2].medicamentos[0].denominacion_generica == "Paracetamol corregido"
        assert documents[2].receta_sustituida_id == documents[0].id
        replacement_id = documents[2].id
        replacement_folio = documents[2].folio
        assert AuditLog.query.filter_by(action="CREAR_RECETA_ADICIONAL").count() == 1
        assert AuditLog.query.filter_by(action="SUSTITUIR_RECETA").count() == 1

    old_print = client.get(f"/recetas/{original_id}/imprimir").get_data(as_text=True)
    assert "NO ENTREGAR NI SURTIR" in old_print
    assert replacement_folio in old_print
    new_print = client.get(f"/recetas/{replacement_id}/imprimir").get_data(as_text=True)
    assert f"sustituye al folio {original_folio}" in new_print

    repeated = client.get(f"/recetas/{original_id}/sustituir")
    assert repeated.status_code == 302
    assert repeated.headers["Location"].endswith(f"/recetas/{original_id}/imprimir")


def test_replacement_requires_a_meaningful_reason(app):
    address = "Av. Salud 123, Col. Centro, C.P. 06000, Ciudad de México"
    with app.app_context():
        doctor = _professional("doctor-reason", "dentista", address=address)
        _, assessment = _patient_and_assessment(doctor)
        assessment_id = assessment.id
    client = app.test_client()
    _login(client, "doctor-reason")
    page = client.get(f"/recetas/valoracion/{assessment_id}/nueva")
    client.post(f"/recetas/valoracion/{assessment_id}/nueva", data=_prescription_data(csrf_from(page)))
    with app.app_context():
        prescription_id = Receta.query.one().id
    replacement_page = client.get(f"/recetas/{prescription_id}/sustituir")
    data = _prescription_data(csrf_from(replacement_page))
    data["motivo_cambio"] = "Breve"
    response = client.post(f"/recetas/{prescription_id}/sustituir", data=data)
    assert response.status_code == 200
    assert "Motivo de sustitución" in response.get_data(as_text=True)
    with app.app_context():
        assert Receta.query.count() == 1


def test_legacy_single_prescription_constraint_migrates_without_losing_folios():
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "legacy-recetas.db"
        connection = sqlite3.connect(database)
        connection.executescript(
            """
            CREATE TABLE usuarios (id INTEGER PRIMARY KEY);
            CREATE TABLE pacientes (id INTEGER PRIMARY KEY);
            CREATE TABLE valoracion_antropometrica (id INTEGER PRIMARY KEY);
            INSERT INTO pacientes VALUES (1);
            INSERT INTO valoracion_antropometrica VALUES (1);
            CREATE TABLE recetas (
                id INTEGER PRIMARY KEY, folio VARCHAR(40) NOT NULL UNIQUE,
                valoracion_id INTEGER NOT NULL UNIQUE, paciente_id INTEGER NOT NULL,
                profesional_id INTEGER, fecha_emision DATE NOT NULL, created_at DATETIME NOT NULL,
                tipo VARCHAR(20) NOT NULL DEFAULT 'original', version INTEGER NOT NULL DEFAULT 1,
                estado VARCHAR(20) NOT NULL DEFAULT 'vigente', receta_sustituida_id INTEGER,
                motivo_cambio VARCHAR(500), sustituida_at DATETIME, sustituida_por_id INTEGER,
                paciente_nombre VARCHAR(200) NOT NULL, paciente_fecha_nacimiento DATE NOT NULL,
                paciente_genero VARCHAR(30), alergias_conocidas TEXT,
                profesional_nombre VARCHAR(200) NOT NULL, profesional_cedula VARCHAR(30) NOT NULL,
                profesional_perfil VARCHAR(30) NOT NULL, domicilio_profesional VARCHAR(300) NOT NULL,
                nombre_establecimiento VARCHAR(160), observaciones TEXT
            );
            INSERT INTO recetas VALUES (
                1,'RX-LEGACY',1,1,NULL,'2026-08-23','2026-08-23 10:00:00',
                'original',1,'vigente',NULL,NULL,NULL,NULL,'Paciente legado','1990-01-01',
                'mujer',NULL,'Profesional legado','12345678','medico_general',
                'Domicilio profesional completo',NULL,NULL
            );
            """
        )
        connection.commit()
        connection.close()
        migration_app = create_app(
            "testing",
            {
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database.as_posix()}",
                "AUTO_CREATE_SCHEMA": False,
                "AUTO_BACKUP_DATABASE": False,
            },
        )
        with migration_app.app_context():
            assert _migrate_prescription_versions(db) is True
            db.session.remove()
            db.engine.dispose()

        connection = sqlite3.connect(database)
        assert connection.execute("SELECT folio FROM recetas WHERE id=1").fetchone()[0] == "RX-LEGACY"
        connection.execute(
            """INSERT INTO recetas (
                id,folio,valoracion_id,paciente_id,fecha_emision,created_at,tipo,version,estado,
                paciente_nombre,paciente_fecha_nacimiento,profesional_nombre,profesional_cedula,
                profesional_perfil,domicilio_profesional
            ) VALUES (2,'RX-ADDITIONAL',1,1,'2026-08-23','2026-08-23 11:00:00','adicional',2,
                'vigente','Paciente legado','1990-01-01','Profesional legado','12345678',
                'medico_general','Domicilio profesional completo')"""
        )
        targets = {row[2] for row in connection.execute("PRAGMA foreign_key_list(recetas)")}
        connection.commit()
        assert connection.execute("SELECT COUNT(*) FROM recetas WHERE valoracion_id=1").fetchone()[0] == 2
        assert "recetas" in targets
        connection.close()


def test_init_db_upgrades_a_v15_prescription_table_with_existing_data():
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "v15.db"
        migration_app = create_app(
            "testing",
            {
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database.as_posix()}",
                "AUTO_BACKUP_DATABASE": False,
            },
        )
        with migration_app.app_context():
            doctor = _professional(
                "legacy-doctor", "medico_general", address="Av. Salud 123, C.P. 06000, Ciudad de México"
            )
            patient, assessment = _patient_and_assessment(doctor)
            doctor_id, patient_id, assessment_id = doctor.id, patient.id, assessment.id
            db.session.remove()
            db.engine.dispose()

        connection = sqlite3.connect(database)
        connection.execute("PRAGMA foreign_keys=OFF")
        connection.execute("DROP TABLE recetas")
        connection.executescript(
            """
            CREATE TABLE recetas (
                id INTEGER PRIMARY KEY, folio VARCHAR(40) NOT NULL UNIQUE,
                valoracion_id INTEGER NOT NULL UNIQUE, paciente_id INTEGER NOT NULL,
                profesional_id INTEGER, fecha_emision DATE NOT NULL, created_at DATETIME NOT NULL,
                paciente_nombre VARCHAR(200) NOT NULL, paciente_fecha_nacimiento DATE NOT NULL,
                paciente_genero VARCHAR(30), alergias_conocidas TEXT,
                profesional_nombre VARCHAR(200) NOT NULL, profesional_cedula VARCHAR(30) NOT NULL,
                profesional_perfil VARCHAR(30) NOT NULL, domicilio_profesional VARCHAR(300) NOT NULL,
                nombre_establecimiento VARCHAR(160), observaciones TEXT,
                FOREIGN KEY(valoracion_id) REFERENCES valoracion_antropometrica(id) ON DELETE RESTRICT,
                FOREIGN KEY(paciente_id) REFERENCES pacientes(id) ON DELETE RESTRICT,
                FOREIGN KEY(profesional_id) REFERENCES usuarios(id) ON DELETE SET NULL
            );
            """
        )
        connection.execute(
            """INSERT INTO recetas VALUES (
                1,'RX-V15',?,?,?,'2026-08-23','2026-08-23 10:00:00','Paciente legado',
                '1992-04-05','mujer',NULL,'Elena Profesional','12345678','medico_general',
                'Av. Salud 123, C.P. 06000, Ciudad de México','Clínica de Pruebas',NULL
            )""",
            (assessment_id, patient_id, doctor_id),
        )
        connection.commit()
        connection.close()

        with migration_app.app_context():
            applied = init_db(db)
            prescription = Receta.query.one()
            assert prescription.folio == "RX-V15"
            assert prescription.tipo == "original"
            assert prescription.version == 1
            assert "recetas.constraint.multiple_versions" in applied
            db.session.remove()
            db.engine.dispose()

        connection = sqlite3.connect(database)
        unique_indexes = [
            [column[0] for column in connection.execute("SELECT name FROM pragma_index_info(?)", (row[1],))]
            for row in connection.execute("PRAGMA index_list('recetas')")
            if row[2]
        ]
        assert ["valoracion_id"] not in unique_indexes
        assert ["valoracion_id", "version"] in unique_indexes
        assert connection.execute("PRAGMA foreign_key_check").fetchone() is None
        connection.close()
