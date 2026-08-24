import json
import sqlite3
import tempfile
from datetime import date, timedelta
from pathlib import Path

from app import create_app
from app import db_orm as db
from app.models.bitacora import AuditLog
from app.models.paciente import Paciente
from app.models.valoracion_antropometrica import ValoracionAntropometrica
from tests.conftest import csrf_from


def _patient(index):
    patient = Paciente(
        nombre=f"Paciente {index}",
        apellido_paterno="Secuencia",
        genero="otro",
        fecha_nacimiento=date(1990, 1, min(index, 28)),
        telefono=f"551234{index:04d}",
        ciudad="Ciudad de México",
        status="activo",
    )
    db.session.add(patient)
    db.session.commit()
    return patient


def _create_from_route(client, patient_id, assessment_date, submitted_number):
    page = client.get(f"/valoraciones/paciente/{patient_id}/nueva")
    response = client.post(
        f"/valoraciones/paciente/{patient_id}/nueva",
        data={
            "csrf_token": csrf_from(page),
            "numero_cita": str(submitted_number),
            "fecha": assessment_date.isoformat(),
            "motivo_consulta": "Atención de prueba",
        },
    )
    assert response.status_code == 302


def test_daily_number_is_global_server_assigned_and_resets_by_date(app, client, login):
    login()
    with app.app_context():
        patient_ids = [_patient(index).id for index in range(1, 4)]

    today = date.today()
    yesterday = today - timedelta(days=1)
    _create_from_route(client, patient_ids[0], today, 9999)
    _create_from_route(client, patient_ids[1], today, 9999)
    _create_from_route(client, patient_ids[2], yesterday, 9999)

    with app.app_context():
        today_rows = ValoracionAntropometrica.query.filter_by(fecha=today).order_by(
            ValoracionAntropometrica.numero_cita
        ).all()
        yesterday_rows = ValoracionAntropometrica.query.filter_by(fecha=yesterday).all()
        assert [row.numero_cita for row in today_rows] == [1, 2]
        assert [row.numero_cita for row in yesterday_rows] == [1]
        events = AuditLog.query.filter_by(action="CREAR_CONSULTA").order_by(AuditLog.id).all()
        metadata = [json.loads(event.metadata_json) for event in events]
        assert [item["turno_diario"] for item in metadata] == [1, 2, 1]


def test_daily_number_projection_is_protected_validated_and_not_cached(app, client, login):
    endpoint = f"/valoraciones/siguiente-numero?fecha={date.today().isoformat()}"
    assert client.get(endpoint).status_code == 302
    login()
    response = client.get(endpoint, headers={"X-Requested-With": "XMLHttpRequest"})
    assert response.status_code == 200
    assert response.get_json()["numero"] == 1
    assert response.headers["Cache-Control"] == "no-store"
    assert client.get("/valoraciones/siguiente-numero?fecha=2099-01-01").status_code == 400


def test_daily_sequence_migration_preserves_and_renumbers_legacy_rows():
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "legacy-daily.db"
        connection = sqlite3.connect(database)
        connection.executescript(
            """
            CREATE TABLE valoracion_antropometrica (
                id INTEGER PRIMARY KEY,
                paciente_id INTEGER NOT NULL,
                numero_cita INTEGER NOT NULL,
                fecha DATE NOT NULL,
                motivo_consulta TEXT,
                created_at DATETIME,
                UNIQUE (paciente_id, numero_cita, fecha)
            );
            INSERT INTO valoracion_antropometrica
                (id, paciente_id, numero_cita, fecha, motivo_consulta, created_at)
            VALUES
                (10, 1, 1, '2026-08-23', 'Primera', '2026-08-23 08:00:00'),
                (20, 2, 1, '2026-08-23', 'Segunda', '2026-08-23 09:00:00'),
                (30, 1, 2, '2026-08-24', 'Otro día', '2026-08-24 08:00:00');
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
        rows = connection.execute(
            "SELECT id, fecha, numero_cita, motivo_consulta FROM valoracion_antropometrica ORDER BY id"
        ).fetchall()
        indexes = connection.execute("PRAGMA index_list('valoracion_antropometrica')").fetchall()
        daily_unique = False
        for index in indexes:
            if not index[2]:
                continue
            columns = [
                row[2] for row in connection.execute(f'PRAGMA index_info("{index[1]}")').fetchall()
            ]
            daily_unique = daily_unique or columns == ["fecha", "numero_cita"]
        connection.close()

        assert rows == [
            (10, "2026-08-23", 1, "Primera"),
            (20, "2026-08-23", 2, "Segunda"),
            (30, "2026-08-24", 1, "Otro día"),
        ]
        assert daily_unique
