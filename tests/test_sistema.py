import os
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stderr
from datetime import date, timedelta
from io import StringIO
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from app import create_app
from app import db_orm as db
from app.config import _load_or_create_secret
from app.core.audit import AuditLog
from app.core.security import reset_rate_limiter
from app.core.validators import (
    ValidationError,
    assessment_payload,
    date_value,
    email_address,
    phone,
    prescription_payload,
)
from app.db import get_database_path, respaldar_db
from app.models.cita import Cita
from app.models.historial_clinico import HistorialClinico
from app.models.paciente import Paciente
from app.models.pago import Pago
from app.models.receta import Receta
from app.models.usuario import Usuario
from app.models.valoracion_antropometrica import ValoracionAntropometrica
from run import _report_startup_failure


def _dispose_database(application):
    """Libera sesiones y conexiones para permitir borrar SQLite en Windows."""
    with application.app_context():
        db.session.remove()
        db.engine.dispose()


class SistemaClinicoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.app = create_app(
            "testing",
            {
                "WTF_CSRF_ENABLED": False,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "AUTO_BACKUP_DATABASE": False,
            },
        )

    @classmethod
    def tearDownClass(cls):
        _dispose_database(cls.app)
        cls.temp_dir.cleanup()

    def setUp(self):
        reset_rate_limiter()
        self.context = self.app.app_context()
        self.context.push()
        db.drop_all()
        db.create_all()
        self.admin = Usuario(
            username="administrator",
            nombre="Admin",
            apellido_paterno="Pruebas",
            email="admin@example.test",
            rol="admin",
            status="activo",
        )
        self.admin.set_password("StrongPass!2026")
        db.session.add(self.admin)
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def _patient(self):
        patient = Paciente(
            nombre="María Elena",
            apellido_paterno="García",
            apellido_materno="López",
            genero="mujer",
            fecha_nacimiento=date(1990, 5, 10),
            telefono="5512345678",
            correo="maria@example.test",
            ciudad="Ciudad de México",
            direccion="Dirección de prueba",
            ocupacion="Docente",
            contacto_emergencia="Juan García",
            telefono_emergencia="5587654321",
            status="activo",
        )
        db.session.add(patient)
        db.session.commit()
        return patient

    def test_01_secret_key_is_generated_and_persisted(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"SGPN_SECRET_KEY": ""}):
            first = _load_or_create_secret(directory)
            second = _load_or_create_secret(directory)
            self.assertEqual(first, second)
            self.assertEqual(len(first), 64)
            self.assertTrue((Path(directory) / ".secret_key").is_file())

    def test_02_authentication_and_password_hashing(self):
        self.assertNotEqual(self.admin.password_hash, "StrongPass!2026")
        self.assertTrue(self.admin.check_password("StrongPass!2026"))
        self.assertFalse(self.admin.check_password("incorrecta"))
        response = self.client.post(
            "/login", data={"username": "administrator", "password": "StrongPass!2026"}
        )
        self.assertEqual(response.status_code, 302)

    def test_03_server_validators(self):
        self.assertEqual(phone("55 1234 5678"), "5512345678")
        self.assertEqual(email_address("TEST@example.com"), "test@example.com")
        self.assertEqual(date_value("1900-01-01", "Nacimiento"), date(1900, 1, 1))
        for invalid in ("123", "abcdefghij"):
            with self.assertRaises(ValidationError):
                phone(invalid)
        with self.assertRaises(ValidationError):
            date_value((date.today() + timedelta(days=1)).isoformat(), "Nacimiento")

    def test_04_patient_crud_and_search(self):
        patient = self._patient()
        self.assertEqual(Paciente.obtener_por_id(patient.id), patient)
        self.assertEqual(Paciente.buscar("García")[0].id, patient.id)
        patient.ocupacion = "Investigadora"
        patient.status = "inactivo"
        db.session.commit()
        self.assertEqual(Paciente.obtener_por_id(patient.id).ocupacion, "Investigadora")
        self.assertEqual(Paciente.buscar("García", status="inactivo")[0].id, patient.id)

    def test_05_history_and_allergies(self):
        patient = self._patient()
        history = HistorialClinico(
            paciente_id=patient.id,
            enfermedades_previas="Asma",
            antecedente_diabetes=True,
            alergias_medicamentosas="Penicilina",
            medicamentos_actuales="Ninguno",
            actividad_fisica="Tres días por semana",
        )
        db.session.add(history)
        db.session.commit()
        saved = HistorialClinico.obtener_por_paciente_id(patient.id)
        self.assertEqual(saved.alergias_medicamentosas, "Penicilina")
        self.assertTrue(saved.antecedente_diabetes)

    def test_06_consultation_vitals_and_prescription(self):
        patient = self._patient()
        data = assessment_payload(
            {
                "numero_cita": "1",
                "fecha": date.today().isoformat(),
                "motivo_consulta": "Revisión general",
                "sintomas": "Fatiga",
                "impresion_diagnostica": "En estudio",
                "plan_tratamiento": "Seguimiento",
                "prescripcion": "Hidratación",
                "tension_arterial": "120/80",
                "frecuencia_cardiaca": "70",
                "frecuencia_respiratoria": "16",
                "temperatura": "36.5",
                "saturacion_oxigeno": "98",
                "estatura": "180",
                "peso": "81",
            }
        )
        consultation = ValoracionAntropometrica.crear(patient.id, data)
        db.session.commit()
        self.assertEqual(consultation.imc, 25.0)
        self.assertEqual(consultation.saturacion_oxigeno, 98)
        self.assertEqual(consultation.prescripcion, "Hidratación")

    def test_07_appointments_and_payments(self):
        patient = self._patient()
        appointment = Cita(
            paciente_id=patient.id,
            fecha=date.today() + timedelta(days=1),
            hora=__import__("datetime").time(10, 0),
            motivo="Seguimiento",
            estatus="Programada",
            estado="pendiente",
        )
        Pago.crear(
            patient.id,
            {
                "fecha_pago": date.today(),
                "monto_centavos": 50000,
                "concepto": "Consulta",
                "metodo_pago": "tarjeta",
                "operation_key": str(uuid4()),
            },
            usuario_id=self.admin.id,
        )
        db.session.add(appointment)
        db.session.commit()
        self.assertEqual(Cita.obtener_siguiente_cita(patient.id).motivo, "Seguimiento")
        self.assertEqual(Pago.obtener_ultimo_pago(patient.id).monto, 500.0)

    def test_08_audit_registration(self):
        patient = self._patient()
        with self.app.test_request_context("/", environ_base={"REMOTE_ADDR": "127.0.0.1"}):
            AuditLog.record("paciente.create", entity_type="paciente", entity_id=patient.id, user_id=self.admin.id)
            db.session.commit()
        event = AuditLog.query.one()
        self.assertEqual(event.action, "CREAR_PACIENTE")
        self.assertEqual(event.module, "paciente")
        self.assertEqual(event.ip_address, "127.0.0.1")

    def test_09_native_sqlite_backup_and_rotation(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "pacientes.db"
            backups = Path(directory) / "backups"
            connection = sqlite3.connect(source)
            connection.execute("CREATE TABLE prueba (id INTEGER PRIMARY KEY, valor TEXT)")
            connection.execute("INSERT INTO prueba(valor) VALUES ('dato')")
            connection.commit()
            connection.close()
            for _ in range(12):
                respaldar_db(source, retention=10, backup_directory=backups)
            saved = list(backups.glob("pacientes_backup_*.db"))
            self.assertEqual(len(saved), 10)
            check = sqlite3.connect(saved[0])
            self.assertEqual(check.execute("SELECT valor FROM prueba").fetchone()[0], "dato")
            check.close()

    def test_10_clinical_routes_require_login(self):
        for path in ("/", "/pacientes/activos", "/historial-clinico/", "/valoraciones/"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 302, path)

    def test_11_additive_schema_migration_preserves_data(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "legacy.db"
            connection = sqlite3.connect(database)
            connection.execute(
                """CREATE TABLE pacientes (
                    id INTEGER PRIMARY KEY,
                    nombre VARCHAR(60) NOT NULL,
                    apellido_paterno VARCHAR(60) NOT NULL,
                    apellido_materno VARCHAR(60),
                    genero VARCHAR(30) NOT NULL,
                    fecha_nacimiento DATE NOT NULL,
                    telefono VARCHAR(10) NOT NULL,
                    correo VARCHAR(254),
                    ciudad VARCHAR(100) NOT NULL,
                    fecha_registro DATETIME NOT NULL,
                    status VARCHAR(20) NOT NULL
                )"""
            )
            connection.execute(
                "INSERT INTO pacientes VALUES (1,'Ana','Prueba',NULL,'mujer','1990-01-01','5512345678',NULL,'México','2026-01-01','activo')"
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
            _dispose_database(migration_app)
            connection = sqlite3.connect(database)
            columns = {row[1] for row in connection.execute("PRAGMA table_info(pacientes)")}
            saved_name = connection.execute("SELECT nombre FROM pacientes WHERE id=1").fetchone()[0]
            connection.close()
            self.assertTrue({"direccion", "ocupacion", "contacto_emergencia", "telefono_emergencia"} <= columns)
            self.assertEqual(saved_name, "Ana")

    def test_12_legacy_database_and_secret_are_migrated(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"SGPN_DATA_DIR": directory}):
            instance = Path(directory) / "instance"
            instance.mkdir()
            legacy_database = instance / "sgpn.db"
            connection = sqlite3.connect(legacy_database)
            connection.execute("CREATE TABLE prueba (id INTEGER PRIMARY KEY, valor TEXT)")
            connection.execute("INSERT INTO prueba(valor) VALUES ('conservado')")
            connection.commit()
            connection.close()
            legacy_secret = "legacy-secret-that-is-long-enough-1234567890"
            (instance / ".session_secret").write_text(legacy_secret, encoding="utf-8")

            migrated_database = get_database_path()
            self.assertEqual(migrated_database.name, "pacientes.db")
            connection = sqlite3.connect(migrated_database)
            self.assertEqual(connection.execute("SELECT valor FROM prueba").fetchone()[0], "conservado")
            connection.close()
            self.assertEqual(_load_or_create_secret(instance), legacy_secret)
            self.assertTrue((instance / ".secret_key").is_file())

    def test_13_required_columns_with_safe_defaults_migrate_legacy_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "legacy.db"
            connection = sqlite3.connect(database)
            connection.executescript(
                """
                CREATE TABLE pacientes (
                    id INTEGER PRIMARY KEY, nombre VARCHAR(60) NOT NULL,
                    apellido_paterno VARCHAR(60) NOT NULL, apellido_materno VARCHAR(60),
                    genero VARCHAR(30) NOT NULL, fecha_nacimiento DATE NOT NULL,
                    telefono VARCHAR(10) NOT NULL, correo VARCHAR(254), ciudad VARCHAR(100) NOT NULL,
                    fecha_registro DATETIME, status VARCHAR(20)
                );
                INSERT INTO pacientes VALUES
                    (1,'Ana','Prueba',NULL,'mujer','1990-01-01','5512345678',NULL,'México','2026-01-01','activo');
                CREATE TABLE usuarios (
                    id INTEGER PRIMARY KEY, username VARCHAR(50) NOT NULL,
                    password_hash VARCHAR(256) NOT NULL, nombre VARCHAR(50),
                    cedula_profesional VARCHAR(30), rol VARCHAR(20), apellido_paterno VARCHAR(50),
                    apellido_materno VARCHAR(50), status VARCHAR(20)
                );
                INSERT INTO usuarios VALUES
                    (1,'legacy','hash','Usuario',NULL,'Admin','Prueba',NULL,'activo');
                INSERT INTO usuarios VALUES
                    (2,'legacy2','hash','Usuario Dos',NULL,'Asistente','Prueba',NULL,'activo');
                CREATE TABLE pagos (
                    id INTEGER PRIMARY KEY, paciente_id INTEGER NOT NULL, fecha_pago DATE NOT NULL,
                    FOREIGN KEY(paciente_id) REFERENCES pacientes(id)
                );
                INSERT INTO pagos VALUES (1,1,'2026-01-01');
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
            _dispose_database(migration_app)

            connection = sqlite3.connect(database)
            users = connection.execute(
                "SELECT username, email, failed_login_attempts, created_at FROM usuarios ORDER BY id"
            ).fetchall()
            user_columns = {row[1] for row in connection.execute("PRAGMA table_info(usuarios)")}
            payment = connection.execute("SELECT paciente_id, created_at FROM pagos WHERE id=1").fetchone()
            email_index = connection.execute(
                "SELECT name, \"unique\" FROM pragma_index_list('usuarios') WHERE name='ix_usuarios_email'"
            ).fetchone()
            connection.close()
            self.assertEqual([user[0] for user in users], ["legacy", "legacy2"])
            self.assertEqual(
                [user[1] for user in users],
                ["usuario-migrado-1@local.invalid", "usuario-migrado-2@local.invalid"],
            )
            self.assertTrue(all(user[2] == 0 and user[3] for user in users))
            self.assertTrue({"nombre_establecimiento", "domicilio_profesional"} <= user_columns)
            self.assertEqual(email_index, ("ix_usuarios_email", 1))
            self.assertEqual(payment[0], 1)
            self.assertTrue(payment[1])

    def test_14_startup_failures_are_visible_without_recreating_flask(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"SGPN_DATA_DIR": directory}):
            output = StringIO()
            error = RuntimeError("fallo de prueba\ncon detalle")
            with redirect_stderr(output):
                _report_startup_failure(error)
            log_path = Path(directory) / "instance" / "logs" / "startup.log"
            self.assertTrue(log_path.is_file())
            self.assertIn("RuntimeError: fallo de prueba con detalle", output.getvalue())
            self.assertIn("RuntimeError: fallo de prueba", log_path.read_text(encoding="utf-8"))

    def test_15_structured_ordinary_prescription(self):
        self.admin.perfil_profesional = "medico_general"
        self.admin.cedula_profesional = "12345678"
        self.admin.domicilio_profesional = "Av. Salud 123, C.P. 06000, Ciudad de México"
        patient = self._patient()
        assessment = ValoracionAntropometrica.crear(
            patient.id,
            {"numero_cita": 1, "fecha": date.today(), "motivo_consulta": "Revisión"},
            profesional=self.admin,
        )
        db.session.flush()
        data = prescription_payload(
            {
                "confirmacion_competencia": "on",
                "confirmacion_ordinaria": "on",
                "confirmacion_firma": "on",
                "denominacion_generica[]": ["Paracetamol"],
                "denominacion_distintiva[]": [""],
                "presentacion[]": ["Tabletas de 500 mg"],
                "dosis[]": ["500 mg"],
                "via_administracion[]": ["Oral"],
                "frecuencia[]": ["Cada 8 horas"],
                "duracion[]": ["3 días"],
                "cantidad[]": ["9 tabletas"],
                "indicaciones[]": ["Tomar con agua"],
            }
        )
        prescription = Receta.crear(assessment, patient, self.admin, data)
        db.session.commit()
        self.assertEqual(prescription.profesional_cedula, "12345678")
        self.assertEqual(prescription.medicamentos[0].via_administracion, "Oral")


if __name__ == "__main__":
    unittest.main()
