import math
import re
import unicodedata
from datetime import date, datetime
from email.utils import parseaddr


class ValidationError(ValueError):
    pass


ALLOWED_ROLES = {"admin", "medico", "recepcion"}
ALLOWED_PROFESSIONAL_PROFILES = {"medico_general", "dentista", "nutricion"}
ALLOWED_USER_STATUS = {"activo", "inactivo"}
ALLOWED_PATIENT_STATUS = {"activo", "inactivo"}
ALLOWED_GENDERS = {"hombre", "mujer", "otro", "prefiero_no_decir"}
ALLOWED_APPOINTMENT_STATUS = {"Programada", "Atendida", "No Asistió", "Cancelada"}
ALLOWED_PAYMENT_METHODS = {"efectivo", "tarjeta", "transferencia", "otro"}
ANTHROPOMETRY_FIELDS = (
    "grasa",
    "porcentaje_grasa",
    "cintura",
    "torax",
    "brazo",
    "cadera",
    "pierna",
    "pantorrilla",
    "bicep",
    "tricep",
    "suprailiaco",
    "subescapular",
    "femoral",
)
PRESCRIPTION_ITEM_FIELDS = (
    "denominacion_generica",
    "denominacion_distintiva",
    "presentacion",
    "dosis",
    "via_administracion",
    "frecuencia",
    "duracion",
    "cantidad",
    "indicaciones",
)


def clean_text(value, field, *, minimum=0, maximum=200, required=False):
    text = unicodedata.normalize("NFKC", str(value or ""))
    text = " ".join(text.replace("\x00", "").split())
    if required and len(text) < max(1, minimum):
        raise ValidationError(f"{field} es obligatorio.")
    if text and len(text) < minimum:
        raise ValidationError(f"{field} debe contener al menos {minimum} caracteres.")
    if len(text) > maximum:
        raise ValidationError(f"{field} excede el máximo de {maximum} caracteres.")
    return text


def multiline_text(value, field, *, minimum=0, maximum=2000, required=False):
    text = unicodedata.normalize("NFKC", str(value or "")).replace("\x00", "")
    text = "\n".join(line.rstrip() for line in text.splitlines()).strip()
    if required and len(text) < max(1, minimum):
        raise ValidationError(f"{field} es obligatorio.")
    if text and len(text) < minimum:
        raise ValidationError(f"{field} debe contener al menos {minimum} caracteres.")
    if len(text) > maximum:
        raise ValidationError(f"{field} excede el máximo de {maximum} caracteres.")
    return text


def name(value, field="Nombre", required=True):
    text = clean_text(value, field, minimum=2 if required else 0, maximum=60, required=required)
    if text and not all(ch.isalpha() or ch in " '-." for ch in text):
        raise ValidationError(f"{field} contiene caracteres no permitidos.")
    return text


def phone(value):
    text = re.sub(r"\D", "", str(value or ""))
    if not re.fullmatch(r"\d{10}", text):
        raise ValidationError("El teléfono debe contener exactamente 10 dígitos.")
    return text


def optional_phone(value, field="Teléfono de emergencia"):
    if value is None or not str(value).strip():
        return None
    text = re.sub(r"\D", "", str(value))
    if not re.fullmatch(r"\d{10}", text):
        raise ValidationError(f"{field} debe contener exactamente 10 dígitos.")
    return text


def email_address(value, *, required=True):
    text = clean_text(value, "Correo", maximum=254, required=required).lower()
    if not text:
        return ""
    parsed = parseaddr(text)[1]
    if parsed != text or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", text):
        raise ValidationError("El correo electrónico no tiene un formato válido.")
    return text


def enum_value(value, field, allowed):
    text = str(value or "").strip()
    if text not in allowed:
        raise ValidationError(f"{field} contiene una opción inválida.")
    return text


def date_value(value, field, *, allow_future=False, oldest_year=1900):
    try:
        parsed = value if isinstance(value, date) else datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ValidationError(f"{field} no tiene una fecha válida.") from None
    if parsed.year < oldest_year:
        raise ValidationError(f"{field} está fuera del rango permitido.")
    if not allow_future and parsed > date.today():
        raise ValidationError(f"{field} no puede ser futura.")
    return parsed


def integer(value, field, *, minimum=None, maximum=None):
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValidationError(f"{field} debe ser un número entero.") from None
    if (minimum is not None and parsed < minimum) or (maximum is not None and parsed > maximum):
        raise ValidationError(f"{field} está fuera del rango permitido.")
    return parsed


def number(value, field, *, minimum=None, maximum=None, required=True):
    if value is None or str(value).strip() == "":
        if required:
            raise ValidationError(f"{field} es obligatorio.")
        return None
    try:
        parsed = float(str(value).replace(",", ".").strip())
    except (TypeError, ValueError):
        raise ValidationError(f"{field} debe ser numérico.") from None
    if not math.isfinite(parsed):
        raise ValidationError(f"{field} debe ser un número finito.")
    if (minimum is not None and parsed < minimum) or (maximum is not None and parsed > maximum):
        raise ValidationError(f"{field} está fuera del rango permitido.")
    return parsed


def username(value):
    text = clean_text(value, "Usuario", minimum=3, maximum=50, required=True).lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,49}", text):
        raise ValidationError("El usuario solo puede usar letras minúsculas, números, punto, guion y guion bajo.")
    return text


def password(value, *, user="", email=""):
    text = str(value or "")
    if len(text) < 12 or len(text) > 128:
        raise ValidationError("La contraseña debe tener entre 12 y 128 caracteres.")
    checks = [
        re.search(r"[a-z]", text),
        re.search(r"[A-Z]", text),
        re.search(r"\d", text),
        re.search(r"[^A-Za-z0-9]", text),
    ]
    if not all(checks):
        raise ValidationError("La contraseña debe incluir mayúscula, minúscula, número y símbolo.")
    lowered = text.casefold()
    fragments = [str(user).casefold(), str(email).split("@", 1)[0].casefold()]
    if any(fragment and len(fragment) >= 3 and fragment in lowered for fragment in fragments):
        raise ValidationError("La contraseña no debe contener el usuario ni el correo.")
    return text


def professional_license(value):
    text = clean_text(value, "Cédula profesional", maximum=12)
    if text and not re.fullmatch(r"\d{5,12}", text):
        raise ValidationError("La cédula profesional debe contener entre 5 y 12 dígitos.")
    return text


def professional_profile(value, role):
    if role == "recepcion":
        return None
    text = clean_text(value, "Perfil profesional", maximum=30)
    if not text:
        if role == "medico":
            raise ValidationError("Selecciona el perfil profesional del usuario clínico.")
        return None
    return enum_value(text, "Perfil profesional", ALLOWED_PROFESSIONAL_PROFILES)


def appointment_time(value):
    try:
        parsed = datetime.strptime(str(value), "%H:%M").time()
    except (TypeError, ValueError):
        raise ValidationError("La hora no tiene un formato válido.") from None
    if parsed.minute not in {0, 30} or parsed.hour < 9 or parsed.hour > 19 or (parsed.hour == 19 and parsed.minute > 0):
        raise ValidationError("La cita debe iniciar entre 09:00 y 19:00, en intervalos de 30 minutos.")
    return parsed


def blood_pressure(value):
    text = clean_text(value, "Tensión arterial", maximum=7, required=False)
    if not text:
        return None
    match = re.fullmatch(r"(\d{2,3})/(\d{2,3})", text)
    if not match:
        raise ValidationError("La tensión arterial debe usar el formato 120/80.")
    systolic, diastolic = map(int, match.groups())
    if not 60 <= systolic <= 260 or not 30 <= diastolic <= 160 or systolic <= diastolic:
        raise ValidationError("La tensión arterial está fuera del rango permitido.")
    return text


def patient_payload(form, *, include_status=False):
    data = {
        "nombre": name(form.get("nombre"), "Nombre"),
        "apellido_paterno": name(form.get("apellido_paterno"), "Apellido paterno"),
        "apellido_materno": name(form.get("apellido_materno"), "Apellido materno", required=False),
        "genero": enum_value(form.get("genero"), "Género", ALLOWED_GENDERS),
        "fecha_nacimiento": date_value(
            form.get("fecha_nacimiento"), "Fecha de nacimiento", oldest_year=1900
        ),
        "telefono": phone(form.get("telefono")),
        "correo": email_address(form.get("correo"), required=False),
        "ciudad": clean_text(form.get("ciudad"), "Ciudad", minimum=2, maximum=100, required=True),
        "direccion": clean_text(form.get("direccion"), "Dirección", maximum=250),
        "ocupacion": clean_text(form.get("ocupacion"), "Ocupación", maximum=120),
        "contacto_emergencia": clean_text(
            form.get("contacto_emergencia"), "Contacto de emergencia", maximum=120
        ),
        "telefono_emergencia": optional_phone(form.get("telefono_emergencia")),
    }
    if include_status:
        data["status"] = enum_value(form.get("status"), "Estado", ALLOWED_PATIENT_STATUS)
    return data


def user_payload(form, *, include_password=True, include_status=False):
    user_name = username(form.get("username")) if include_password else None
    email = email_address(form.get("email"))
    role = enum_value(form.get("rol"), "Rol", ALLOWED_ROLES)
    data = {
        "nombre": name(form.get("nombre"), "Nombre"),
        "apellido_paterno": name(form.get("apellido_paterno"), "Apellido paterno"),
        "apellido_materno": name(form.get("apellido_materno"), "Apellido materno", required=False),
        "email": email,
        "rol": role,
        "perfil_profesional": professional_profile(form.get("perfil_profesional"), role),
        "cedula_profesional": professional_license(form.get("cedula_profesional"))
        if role != "recepcion"
        else "",
        "nombre_establecimiento": clean_text(
            form.get("nombre_establecimiento"), "Nombre del establecimiento", minimum=2, maximum=160
        )
        if role != "recepcion"
        else "",
        "domicilio_profesional": clean_text(
            form.get("domicilio_profesional"), "Domicilio profesional", minimum=10, maximum=300
        )
        if role != "recepcion"
        else "",
    }
    if include_password:
        data["username"] = user_name
        data["password"] = password(form.get("password"), user=user_name, email=email)
    if include_status:
        data["status"] = enum_value(form.get("status"), "Estado", ALLOWED_USER_STATUS)
    return data


def _form_values(form, field):
    values = form.getlist(field) if hasattr(form, "getlist") else form.get(field, [])
    if not isinstance(values, (list, tuple)):
        values = [values]
    return list(values)


def prescription_payload(form):
    """Valida una receta ordinaria estructurada; no admite recetas especiales o controladas."""
    if form.get("confirmacion_competencia") != "on":
        raise ValidationError("Confirma que la prescripción se encuentra dentro de tu competencia profesional.")
    if form.get("confirmacion_ordinaria") != "on":
        raise ValidationError("Confirma que no se trata de un medicamento que requiera receta especial.")
    if form.get("confirmacion_firma") != "on":
        raise ValidationError("Confirma que revisarás y firmarás la receta antes de entregarla.")

    columns = {field: _form_values(form, f"{field}[]") for field in PRESCRIPTION_ITEM_FIELDS}
    lengths = {len(values) for values in columns.values()}
    if len(lengths) != 1:
        raise ValidationError("Los datos de medicamentos están incompletos o no coinciden.")
    row_count = lengths.pop() if lengths else 0
    if row_count > 10:
        raise ValidationError("Una receta puede contener como máximo 10 medicamentos.")

    medicines = []
    fingerprints = set()
    required = {
        "denominacion_generica": ("Denominación genérica", 160),
        "presentacion": ("Presentación", 160),
        "dosis": ("Dosis", 160),
        "via_administracion": ("Vía de administración", 100),
        "frecuencia": ("Frecuencia", 160),
        "duracion": ("Duración", 160),
    }
    optional = {
        "denominacion_distintiva": ("Denominación distintiva", 160),
        "cantidad": ("Cantidad a surtir", 100),
        "indicaciones": ("Indicaciones adicionales", 500),
    }
    for index in range(row_count):
        raw = {field: columns[field][index] for field in PRESCRIPTION_ITEM_FIELDS}
        if not any(str(value or "").strip() for value in raw.values()):
            continue
        item = {
            field: clean_text(raw[field], f"{label} del medicamento {index + 1}", maximum=maximum, required=True)
            for field, (label, maximum) in required.items()
        }
        item.update(
            {
                field: clean_text(raw[field], f"{label} del medicamento {index + 1}", maximum=maximum) or None
                for field, (label, maximum) in optional.items()
            }
        )
        fingerprint = tuple(str(item.get(field) or "").casefold() for field in PRESCRIPTION_ITEM_FIELDS)
        if fingerprint in fingerprints:
            raise ValidationError(f"El medicamento {index + 1} duplica exactamente otra fila.")
        fingerprints.add(fingerprint)
        medicines.append(item)

    if not medicines:
        raise ValidationError("Registra al menos un medicamento con sus instrucciones completas.")
    return {
        "medicamentos": medicines,
        "observaciones": multiline_text(form.get("observaciones"), "Observaciones", maximum=1000),
    }


def prescription_replacement_reason(value):
    """Motivo clínico-administrativo de una sustitución, sin permitir cambios silenciosos."""
    return multiline_text(value, "Motivo de sustitución", minimum=10, maximum=500, required=True)


def password_change_payload(form, user, *, require_current=True):
    current = str(form.get("current_password", ""))[:128]
    new_password = password(form.get("new_password"), user=user.username, email=user.email)
    confirmation = str(form.get("confirm_password", ""))[:128]
    if require_current and not current:
        raise ValidationError("La contraseña actual es obligatoria.")
    if new_password != confirmation:
        raise ValidationError("La confirmación de la nueva contraseña no coincide.")
    if user.check_password(new_password):
        raise ValidationError("La nueva contraseña debe ser distinta de la contraseña actual.")
    return {"current_password": current, "new_password": new_password}


def assessment_payload(form, *, allow_anthropometry=True):
    height = number(form.get("estatura"), "Estatura", minimum=0.1, maximum=250, required=False)
    if height is not None and height <= 3:
        height *= 100
    if height is not None and height < 30:
        raise ValidationError("Estatura está fuera del rango permitido.")
    weight = number(form.get("peso"), "Peso", minimum=0.1, maximum=500, required=False)
    bmi = round(weight / ((height / 100) ** 2), 2) if height and weight else None
    data = {
        "numero_cita": integer(form.get("numero_cita", 1), "Número de cita", minimum=1, maximum=10000),
        "fecha": date_value(form.get("fecha"), "Fecha de consulta"),
        "motivo_consulta": multiline_text(
            form.get("motivo_consulta"), "Motivo de consulta", maximum=2000, required=True
        ),
        "sintomas": multiline_text(form.get("sintomas"), "Síntomas", maximum=4000),
        "impresion_diagnostica": multiline_text(
            form.get("impresion_diagnostica"), "Impresión diagnóstica", maximum=4000
        ),
        "plan_tratamiento": multiline_text(
            form.get("plan_tratamiento"), "Plan de tratamiento", maximum=4000
        ),
        "prescripcion": multiline_text(form.get("prescripcion"), "Indicaciones clínicas", maximum=4000),
        "tension_arterial": blood_pressure(form.get("tension_arterial")),
        "frecuencia_cardiaca": _optional_integer(
            form.get("frecuencia_cardiaca"), "Frecuencia cardiaca", minimum=30, maximum=250
        ),
        "frecuencia_respiratoria": _optional_integer(
            form.get("frecuencia_respiratoria"), "Frecuencia respiratoria", minimum=5, maximum=80
        ),
        "temperatura": number(form.get("temperatura"), "Temperatura", minimum=30, maximum=45, required=False),
        "saturacion_oxigeno": _optional_integer(
            form.get("saturacion_oxigeno"), "Saturación de oxígeno", minimum=50, maximum=100
        ),
        "estatura": height,
        "peso": weight,
        "imc": bmi,
    }
    if not allow_anthropometry:
        if any(str(form.get(field, "")).strip() for field in ANTHROPOMETRY_FIELDS):
            raise ValidationError("La antropometría sólo está disponible para profesionales de Nutrición.")
        return data
    data.update(
        {
            "grasa": number(form.get("grasa"), "Grasa", minimum=0, maximum=100, required=False),
            "cintura": number(form.get("cintura"), "Cintura", minimum=1, maximum=300, required=False),
            "torax": number(form.get("torax"), "Tórax", minimum=1, maximum=300, required=False),
            "brazo": number(form.get("brazo"), "Brazo", minimum=1, maximum=100, required=False),
            "cadera": number(form.get("cadera"), "Cadera", minimum=1, maximum=300, required=False),
            "pierna": number(form.get("pierna"), "Pierna", minimum=1, maximum=150, required=False),
            "pantorrilla": number(
                form.get("pantorrilla"), "Pantorrilla", minimum=1, maximum=100, required=False
            ),
            "bicep": number(form.get("bicep"), "Pliegue bíceps", minimum=0, maximum=100, required=False),
            "tricep": number(form.get("tricep"), "Pliegue tríceps", minimum=0, maximum=100, required=False),
            "suprailiaco": number(
                form.get("suprailiaco"), "Pliegue suprailiaco", minimum=0, maximum=100, required=False
            ),
            "subescapular": number(
                form.get("subescapular"), "Pliegue subescapular", minimum=0, maximum=100, required=False
            ),
            "femoral": number(
                form.get("femoral"), "Pliegue femoral", minimum=0, maximum=100, required=False
            ),
            "porcentaje_grasa": number(
                form.get("porcentaje_grasa"), "Porcentaje de grasa", minimum=0, maximum=75, required=False
            ),
        }
    )
    return data


def _optional_integer(value, field, *, minimum=None, maximum=None):
    if value is None or str(value).strip() == "":
        return None
    return integer(value, field, minimum=minimum, maximum=maximum)


def history_payload(form):
    return {
        "enfermedades_previas": multiline_text(
            form.get("enfermedades_previas"), "Enfermedades previas", maximum=4000
        ),
        "cirugias": multiline_text(form.get("cirugias"), "Cirugías", maximum=4000),
        "antecedentes_familiares": multiline_text(
            form.get("antecedentes_familiares"), "Antecedentes familiares", maximum=4000
        ),
        "antecedente_diabetes": form.get("antecedente_diabetes") == "on",
        "antecedente_hipertension": form.get("antecedente_hipertension") == "on",
        "antecedente_cardiopatias": form.get("antecedente_cardiopatias") == "on",
        "antecedente_cancer": form.get("antecedente_cancer") == "on",
        "alergias_medicamentosas": multiline_text(
            form.get("alergias_medicamentosas"), "Alergias medicamentosas", maximum=4000
        ),
        "alergias_alimentarias": multiline_text(
            form.get("alergias_alimentarias"), "Alergias alimentarias", maximum=4000
        ),
        "medicamentos_actuales": multiline_text(
            form.get("medicamentos_actuales"), "Medicamentos actuales", maximum=4000
        ),
        "tratamientos_actuales": multiline_text(
            form.get("tratamientos_actuales"), "Tratamientos actuales", maximum=4000
        ),
        "actividad_fisica": clean_text(form.get("actividad_fisica"), "Actividad física", maximum=300),
        "motivo_consulta_habitual": multiline_text(
            form.get("motivo_consulta_habitual"), "Motivo habitual de consulta", maximum=2000
        ),
        "notas_generales": multiline_text(form.get("notas_generales"), "Notas generales", maximum=4000),
    }


def appointment_payload(form):
    appointment_date = date_value(form.get("proxima_cita_fecha"), "Fecha de cita", allow_future=True)
    if appointment_date < date.today():
        raise ValidationError("La fecha de cita no puede estar en el pasado.")
    return {
        "fecha": appointment_date,
        "hora": appointment_time(form.get("proxima_cita_hora")),
        "motivo": clean_text(form.get("motivo"), "Motivo de la cita", maximum=500),
    }


def payment_payload(form):
    return {
        "fecha_pago": date_value(form.get("fecha_pago"), "Fecha de pago"),
        "monto": number(form.get("monto"), "Monto", minimum=0, maximum=10_000_000),
        "concepto": clean_text(form.get("concepto"), "Concepto", maximum=200, required=True),
        "metodo_pago": enum_value(form.get("metodo_pago"), "Método de pago", ALLOWED_PAYMENT_METHODS),
    }
