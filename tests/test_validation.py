import pytest

from app.core.validators import ValidationError, assessment_payload, password, patient_payload


def test_password_policy():
    assert password("ValidPassword!2026", user="someone", email="mail@example.test")
    for invalid in ["short1!A", "alllowercase!2026", "ALLUPPERCASE!2026", "NoSymbols2026", "someone!PASS2026"]:
        with pytest.raises(ValidationError):
            password(invalid, user="someone", email="mail@example.test")


def test_patient_payload_normalizes_and_validates():
    data = patient_payload(
        {
            "nombre": "  José  Luis ",
            "apellido_paterno": "Pérez",
            "apellido_materno": "López",
            "genero": "hombre",
            "fecha_nacimiento": "1990-01-02",
            "telefono": "55 1234 5678",
            "correo": "TEST@EXAMPLE.COM",
            "ciudad": "Ciudad de México",
        }
    )
    assert data["nombre"] == "José Luis"
    assert data["telefono"] == "5512345678"
    assert data["correo"] == "test@example.com"


def test_assessment_recalculates_bmi_and_rejects_ranges():
    raw = {
        "numero_cita": "1",
        "fecha": "2026-01-01",
        "motivo_consulta": "Revisión general",
        "estatura": "1.80",
        "peso": "81",
        "grasa": "15",
        "cintura": "90",
        "torax": "100",
        "brazo": "35",
        "cadera": "100",
        "pierna": "60",
        "pantorrilla": "38",
        "tension_arterial": "120/80",
        "frecuencia_cardiaca": "60",
        "bicep": "5",
        "tricep": "10",
        "suprailiaco": "12",
        "subescapular": "11",
        "femoral": "15",
        "porcentaje_grasa": "18",
        "imc": "999",
    }
    data = assessment_payload(raw)
    assert data["imc"] == 25.0
    raw["tension_arterial"] = "20/300"
    with pytest.raises(ValidationError):
        assessment_payload(raw)
