"""Carga opcional de datos demostrativos para validar SMBase localmente.

No se ejecuta durante el arranque. Requiere ``--confirm`` y nunca elimina ni
reemplaza información existente. Los registros usan correos ``example.test`` y
teléfonos reservados para identificarlos como datos ficticios.
"""

import argparse
import os
import secrets
from datetime import date, timedelta
from pathlib import Path
from uuid import NAMESPACE_URL, uuid4, uuid5

from openpyxl import Workbook

from app import create_app
from app import db_orm as db
from app.models.cita import Cita
from app.models.historial_clinico import HistorialClinico
from app.models.paciente import Paciente
from app.models.pago import Pago
from app.models.receta import Receta
from app.models.usuario import Usuario
from app.models.valoracion_antropometrica import ValoracionAntropometrica

DEMO_USERS = (
    {
        "username": "demo_admin",
        "nombre": "Adriana",
        "apellido_paterno": "Administración",
        "apellido_materno": "Demo",
        "email": "demo.admin@example.test",
        "rol": "admin",
        "perfil_profesional": None,
        "cedula_profesional": None,
    },
    {
        "username": "demo_medico",
        "nombre": "Daniel",
        "apellido_paterno": "Médico",
        "apellido_materno": "Demo",
        "email": "demo.medico@example.test",
        "rol": "medico",
        "perfil_profesional": "medico_general",
        "cedula_profesional": "99000001",
    },
    {
        "username": "demo_dentista",
        "nombre": "Diana",
        "apellido_paterno": "Dentista",
        "apellido_materno": "Demo",
        "email": "demo.dentista@example.test",
        "rol": "medico",
        "perfil_profesional": "dentista",
        "cedula_profesional": "99000002",
    },
    {
        "username": "demo_nutricion",
        "nombre": "Natalia",
        "apellido_paterno": "Nutrición",
        "apellido_materno": "Demo",
        "email": "demo.nutricion@example.test",
        "rol": "medico",
        "perfil_profesional": "nutricion",
        "cedula_profesional": "99000003",
    },
    {
        "username": "demo_recepcion",
        "nombre": "Renata",
        "apellido_paterno": "Recepción",
        "apellido_materno": "Demo",
        "email": "demo.recepcion@example.test",
        "rol": "recepcion",
        "perfil_profesional": None,
        "cedula_profesional": None,
    },
)

DEMO_PATIENTS = (
    ("Patricia", "Ramírez", "Soto", "mujer", date(1988, 4, 12), "5500000101", "Ciudad de México"),
    ("Carlos", "Hernández", "Luna", "hombre", date(1976, 11, 3), "5500000102", "Naucalpan"),
    ("Mariana", "López", "Vega", "mujer", date(1994, 7, 21), "5500000103", "Tlalnepantla"),
    ("Jorge", "Castillo", "Núñez", "hombre", date(1982, 1, 17), "5500000104", "Ciudad de México"),
    ("Sofía", "Mendoza", "Ruiz", "mujer", date(2001, 9, 8), "5500000105", "Ecatepec"),
    ("Luis", "Torres", "Campos", "hombre", date(1969, 6, 30), "5500000106", "Ciudad de México"),
)


def _demo_password():
    return os.environ.get("SGPN_DEMO_PASSWORD") or f"Demo!Aa1-{secrets.token_urlsafe(12)}"


def _get_or_create_users(password):
    users = {}
    created = []
    for values in DEMO_USERS:
        user = Usuario.find_by_username(values["username"])
        if user is None:
            user = Usuario.create(
                password=password,
                nombre_establecimiento="Consultorio Demostrativo",
                domicilio_profesional="Av. Salud 100, Col. Centro, C.P. 06000, Ciudad de México",
                **values,
            )
            db.session.flush()
            created.append(user.username)
        users[values["username"]] = user
    return users, created


def _get_or_create_patients():
    patients = []
    created = 0
    for index, values in enumerate(DEMO_PATIENTS, start=1):
        patient = Paciente.query.filter_by(telefono=values[5]).first()
        if patient is None:
            patient = Paciente(
                nombre=values[0],
                apellido_paterno=values[1],
                apellido_materno=values[2],
                genero=values[3],
                fecha_nacimiento=values[4],
                telefono=values[5],
                correo=f"paciente.demo{index}@example.test",
                ciudad=values[6],
                direccion=f"Calle Demostración {index * 10}, Col. Pruebas",
                ocupacion=("Docente", "Contador", "Diseñadora", "Técnico", "Estudiante", "Comerciante")[index - 1],
                contacto_emergencia=f"Contacto Demo {index}",
                telefono_emergencia=f"55000002{index:02d}",
                status="activo",
            )
            db.session.add(patient)
            db.session.flush()
            created += 1
        patients.append(patient)
    return patients, created


def _create_histories(patients):
    histories = (
        ("Migraña episódica", "Apendicectomía en 2012", "Madre con hipertensión", "Penicilina", None, "Ibuprofeno ocasional", "Caminata 3 veces por semana"),
        ("Hipertensión controlada", None, "Padre con diabetes", None, None, "Losartán 50 mg", "Actividad ligera"),
        ("Sin enfermedades crónicas", None, None, None, "Nuez", None, "Entrenamiento funcional 4 veces por semana"),
        ("Gastritis", "Colecistectomía en 2018", None, None, None, "Omeprazol ocasional", "Bicicleta de fin de semana"),
        ("Asma leve", None, "Abuela con cardiopatía", "Sulfas", None, "Salbutamol de rescate", "Natación 2 veces por semana"),
        ("Diabetes tipo 2", None, "Antecedentes de diabetes e hipertensión", None, None, "Metformina 850 mg", "Caminata diaria"),
    )
    created = 0
    for patient, values in zip(patients, histories, strict=True):
        if HistorialClinico.obtener_por_paciente_id(patient.id) is None:
            db.session.add(
                HistorialClinico(
                    paciente_id=patient.id,
                    enfermedades_previas=values[0],
                    cirugias=values[1],
                    antecedentes_familiares=values[2],
                    alergias_medicamentosas=values[3],
                    alergias_alimentarias=values[4],
                    medicamentos_actuales=values[5],
                    actividad_fisica=values[6],
                    motivo_consulta_habitual="Seguimiento clínico demostrativo",
                    notas_generales="Registro ficticio creado exclusivamente para validación local.",
                )
            )
            created += 1
    return created


def _create_assessment(patient, professional, *, days_ago, reason, diagnosis, nutrition=False):
    assessment_date = date.today() - timedelta(days=days_ago)
    existing = ValoracionAntropometrica.query.filter_by(
        paciente_id=patient.id,
        fecha=assessment_date,
        motivo_consulta=reason,
    ).first()
    if existing:
        return existing, False
    number = ValoracionAntropometrica.siguiente_numero_diario(assessment_date)
    data = {
        "numero_cita": number,
        "fecha": assessment_date,
        "motivo_consulta": reason,
        "sintomas": "Información clínica ficticia para validar la interfaz.",
        "impresion_diagnostica": diagnosis,
        "plan_tratamiento": "Seguimiento y reevaluación según evolución.",
        "prescripcion": "Indicaciones demostrativas; no utilizar como tratamiento real.",
        "tension_arterial": "120/80",
        "frecuencia_cardiaca": 72,
        "frecuencia_respiratoria": 16,
        "temperatura": 36.6,
        "saturacion_oxigeno": 98,
        "estatura": 168,
        "peso": 72.4,
        "imc": 25.65,
    }
    if nutrition:
        data.update(
            {
                "cintura": 82.5,
                "torax": 94.0,
                "brazo": 31.2,
                "cadera": 101.0,
                "pierna": 56.0,
                "pantorrilla": 36.5,
                "porcentaje_grasa": 24.8,
            }
        )
    assessment = ValoracionAntropometrica.crear(patient.id, data, profesional=professional)
    db.session.flush()
    return assessment, True


def _create_consultations(patients, users):
    definitions = (
        (0, "demo_medico", 35, "Valoración inicial demostrativa", "Cefalea tensional en seguimiento", False),
        (0, "demo_medico", 7, "Revisión de evolución demostrativa", "Evolución clínica estable", False),
        (0, "demo_medico", 0, "Consulta más reciente demostrativa", "Sin datos de alarma", False),
        (1, "demo_medico", 3, "Control de presión arterial", "Hipertensión arterial controlada", False),
        (2, "demo_nutricion", 20, "Valoración nutricional inicial", "Plan nutricional individualizado", True),
        (2, "demo_nutricion", 2, "Seguimiento nutricional", "Evolución antropométrica favorable", True),
        (3, "demo_dentista", 12, "Revisión odontológica", "Gingivitis leve", False),
        (4, "demo_medico", 1, "Control respiratorio", "Asma leve controlada", False),
        (5, "demo_nutricion", 15, "Orientación alimentaria", "Seguimiento metabólico", True),
    )
    created = 0
    assessments = []
    for patient_index, username, days, reason, diagnosis, nutrition in definitions:
        assessment, was_created = _create_assessment(
            patients[patient_index],
            users[username],
            days_ago=days,
            reason=reason,
            diagnosis=diagnosis,
            nutrition=nutrition,
        )
        assessments.append(assessment)
        created += int(was_created)
    return assessments, created


def _next_free_appointment_slot(day):
    for slot in Cita.HORARIOS_ATENCION:
        if Cita.es_horario_disponible(day, slot):
            return slot
    return None


def _create_appointments(patients):
    created = 0
    definitions = (
        (0, 1, "Cita demostrativa programada", "Programada", None),
        (1, 2, "Cita demostrativa programada", "Programada", None),
        (2, 3, "Cita demostrativa programada", "Programada", None),
        (3, 4, "Cita demostrativa programada", "Programada", None),
        (4, -4, "Cita demostrativa atendida", "Atendida", None),
        (5, -3, "Cita demostrativa no asistida", "No Asistió", None),
        (0, -10, "Cita demostrativa cancelada", "Cancelada", "Cancelación ficticia de validación"),
    )
    for patient_index, day_offset, reason, status, cancellation_reason in definitions:
        patient = patients[patient_index]
        if Cita.query.filter_by(paciente_id=patient.id, motivo=reason, estatus=status).first():
            continue
        target = date.today() + timedelta(days=day_offset)
        slot = _next_free_appointment_slot(target)
        if slot is None:
            continue
        db.session.add(
            Cita(
                paciente_id=patient.id,
                fecha=target,
                hora=slot,
                motivo=reason,
                estado="pendiente" if status == "Programada" else "cerrada",
                estatus=status,
                motivo_cancelacion=cancellation_reason,
            )
        )
        db.session.flush()
        created += 1
    return created


def _create_payments(patients, users):
    created = 0
    definitions = (
        # paciente, días, centavos, concepto, método, registrador, cita, estado
        (0, 1, 50000, "Consulta demostrativa", "efectivo", "demo_recepcion", "Programada", "vigente"),
        (1, 2, 55000, "Consulta demostrativa", "tarjeta", "demo_recepcion", "Programada", "vigente"),
        (2, 3, 60000, "Consulta demostrativa", "transferencia", "demo_recepcion", "Programada", "vigente"),
        (0, 8, 35000, "Seguimiento demostrativo", "tarjeta", "demo_medico", None, "vigente"),
        (1, 12, 80000, "Procedimiento demostrativo", "transferencia", "demo_admin", "Programada", "vigente"),
        (2, 16, 42550, "Valoración nutricional demostrativa", "efectivo", "demo_nutricion", None, "vigente"),
        (3, 5, 67500, "Atención odontológica demostrativa", "tarjeta", "demo_dentista", "Programada", "vigente"),
        (3, 25, 30000, "Revisión odontológica demostrativa", "efectivo", "demo_recepcion", None, "vigente"),
        (4, 4, 48000, "Consulta respiratoria demostrativa", "transferencia", "demo_medico", "Atendida", "vigente"),
        (4, 18, 52000, "Seguimiento respiratorio demostrativo", "otro", "demo_recepcion", None, "vigente"),
        (5, 7, 39000, "Orientación alimentaria demostrativa", "efectivo", "demo_nutricion", "No Asistió", "vigente"),
        (5, 31, 44000, "Seguimiento metabólico demostrativo", "tarjeta", "demo_recepcion", None, "vigente"),
        (0, 0, 15000, "Pago cancelado demostrativo", "efectivo", "demo_admin", "Cancelada", "cancelado"),
        (1, 0, 12345, "Cobro sin cita aunque existe una programada", "otro", "demo_recepcion", None, "vigente"),
        (2, 0, 101, "=PRUEBA_CSV_NEUTRALIZADA", "transferencia", "demo_admin", None, "vigente"),
        (3, 65, 91000, "Pago de otro periodo para reporte mensual", "tarjeta", "demo_admin", None, "vigente"),
        (5, 45, 27575, "Pago registrado por Odontología", "efectivo", "demo_dentista", None, "vigente"),
    )
    for patient_index, days_ago, cents, concept, method, username, appointment_status, status in definitions:
        patient = patients[patient_index]
        if Pago.query.filter_by(paciente_id=patient.id, concepto=concept).first():
            continue
        appointment = None
        if appointment_status:
            appointment = (
                Cita.query.filter_by(paciente_id=patient.id, estatus=appointment_status)
                .order_by(Cita.fecha.desc(), Cita.hora.desc(), Cita.id.desc())
                .first()
            )
        payment = Pago.crear(
            patient.id,
            {
                "fecha_pago": date.today() - timedelta(days=days_ago),
                "monto_centavos": cents,
                "concepto": concept,
                "metodo_pago": method,
                "operation_key": str(uuid4()),
            },
            usuario_id=users[username].id,
            cita_id=appointment.id if appointment else None,
        )
        db.session.flush()
        if status == "cancelado":
            payment.cancelar(
                usuario_id=users["demo_admin"].id,
                motivo="Cancelación demostrativa para validar trazabilidad",
            )
        created += 1

    review_concept = "Pago legado incompleto para revisión"
    review_patient = patients[4]
    if not Pago.query.filter_by(paciente_id=review_patient.id, concepto=review_concept).first():
        db.session.add(
            Pago(
                paciente_id=review_patient.id,
                fecha_pago=date.today() - timedelta(days=90),
                monto=None,
                monto_centavos=0,
                moneda="MXN",
                concepto=review_concept,
                metodo_pago="otro",
                folio="PAG-LEGADO-DEMO-0001",
                operation_key=str(uuid5(NAMESPACE_URL, "sgpn-demo-pago-requiere-revision")),
                usuario_registro_id=None,
                cita_id=None,
                estatus="requiere_revision",
            )
        )
        created += 1
    return created


def _create_demo_prescription(assessment, patient, doctor):
    if assessment.recetas:
        return False
    history = HistorialClinico.obtener_por_paciente_id(patient.id)
    allergies = history.alergias_medicamentosas if history else None
    Receta.crear(
        assessment,
        patient,
        doctor,
        {
            "observaciones": "Documento ficticio para validar impresión y orden de medicamentos.",
            "medicamentos": [
                {
                    "denominacion_generica": "Paracetamol",
                    "denominacion_distintiva": None,
                    "presentacion": "Tabletas de 500 mg",
                    "dosis": "1 tableta",
                    "via_administracion": "Oral",
                    "frecuencia": "Cada 8 horas",
                    "duracion": "3 días",
                    "cantidad": "9 tabletas",
                    "indicaciones": "Sólo como ejemplo; no constituye una indicación médica real.",
                },
                {
                    "denominacion_generica": "Loratadina",
                    "denominacion_distintiva": None,
                    "presentacion": "Tabletas de 10 mg",
                    "dosis": "1 tableta",
                    "via_administracion": "Oral",
                    "frecuencia": "Cada 24 horas",
                    "duracion": "5 días",
                    "cantidad": "5 tabletas",
                    "indicaciones": None,
                },
                {
                    "denominacion_generica": "Solución salina",
                    "denominacion_distintiva": None,
                    "presentacion": "Solución nasal",
                    "dosis": "2 aplicaciones",
                    "via_administracion": "Nasal",
                    "frecuencia": "Cada 12 horas",
                    "duracion": "5 días",
                    "cantidad": "1 frasco",
                    "indicaciones": None,
                },
            ],
        },
        alergias_conocidas=allergies,
    )
    return True


def seed_demo_data(application, password=None):
    """Inserta el conjunto demo y devuelve un resumen; es seguro repetirlo."""
    demo_password = password or _demo_password()
    with application.app_context():
        users, created_users = _get_or_create_users(demo_password)
        patients, created_patients = _get_or_create_patients()
        created_histories = _create_histories(patients)
        assessments, created_assessments = _create_consultations(patients, users)
        created_appointments = _create_appointments(patients)
        created_payments = _create_payments(patients, users)
        created_prescriptions = int(
            _create_demo_prescription(assessments[2], patients[0], users["demo_medico"])
        )
        db.session.commit()
        return {
            "usuarios": created_users,
            "pacientes": created_patients,
            "historiales": created_histories,
            "consultas": created_assessments,
            "citas": created_appointments,
            "pagos": created_payments,
            "recetas": created_prescriptions,
            "password": demo_password if created_users else None,
        }


def create_demo_workbook(target):
    """Genera un XLSX antropométrico compatible con el importador del sistema."""
    destination = Path(target)
    destination.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Demo antropometría"
    sheet["L7"] = "Visita"
    sheet["M7"] = "Fecha"
    sheet["N7"] = "Peso"
    sheet["M8"] = 168
    demo_rows = (
        (1, date.today() - timedelta(days=90), 78.5, "Grasa 24.8", 88, 96, 32, 104, 58, 37, "BC 10 TC 18 SI 20 SE 16 FEM 22", 24.8, "118/76", 68),
        (2, date.today() - timedelta(days=60), 76.9, "Grasa 23.9", 86, 95, 31.5, 102, 57.5, 36.8, "BC 9 TC 17 SI 19 SE 15 FEM 21", 23.9, "116/74", 70),
        (3, date.today() - timedelta(days=30), 75.4, "Grasa 22.7", 84, 94, 31, 100, 57, 36.5, "BC 8 TC 16 SI 18 SE 14 FEM 20", 22.7, "114/72", 66),
    )
    for row_number, values in enumerate(demo_rows, start=10):
        for column, value in enumerate(values, start=12):
            sheet.cell(row=row_number, column=column, value=value)
    workbook.save(destination)
    workbook.close()
    return destination


def main():
    parser = argparse.ArgumentParser(description="Carga datos ficticios para validar SMBase.")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirma que los registros DEMO se agregarán a la base configurada.",
    )
    parser.add_argument(
        "--xlsx-output",
        default="demo_data/expediente_antropometrico_demo.xlsx",
        help="Ruta donde se generará el archivo XLSX demostrativo.",
    )
    args = parser.parse_args()
    if not args.confirm:
        parser.error("Debes usar --confirm. Ejecuta primero sobre una copia o base de pruebas.")

    application = create_app(os.environ.get("SGPN_ENV", "default"))
    summary = seed_demo_data(application)
    workbook = create_demo_workbook(args.xlsx_output)
    print("Datos demostrativos procesados correctamente.")
    print(
        "Nuevos: "
        f"{summary['pacientes']} pacientes, {summary['consultas']} consultas, "
        f"{summary['citas']} citas, {summary['pagos']} pagos, {summary['recetas']} receta."
    )
    if summary["usuarios"]:
        print(f"Usuarios nuevos: {', '.join(summary['usuarios'])}")
        print(f"Contraseña compartida para esta carga DEMO: {summary['password']}")
        print("Estas cuentas son sólo para validación local; desactívalas antes de usar datos reales.")
    else:
        print("Las cuentas demo ya existían; se conservaron sus contraseñas actuales.")
    print(f"XLSX demostrativo: {workbook.resolve()}")


if __name__ == "__main__":
    main()
