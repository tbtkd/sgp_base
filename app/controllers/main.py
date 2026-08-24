from datetime import datetime, timedelta

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user

from app import db_orm as db
from app.core.audit import AuditLog
from app.core.auth import login_required
from app.core.security import roles_required
from app.core.time import utcnow_naive
from app.core.validators import ValidationError, date_value, multiline_text
from app.models.bitacora import BitacoraContacto
from app.models.cita import Cita
from app.models.historial_clinico import HistorialClinico
from app.models.paciente import Paciente
from app.models.plantilla import PlantillaMensaje
from app.models.valoracion_antropometrica import ValoracionAntropometrica

main = Blueprint("main", __name__)

WEEKDAYS_ES = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
MONTHS_ES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


def _dashboard_time_context(moment):
    if moment.hour < 12:
        greeting = "Buenos días"
    elif moment.hour < 19:
        greeting = "Buenas tardes"
    else:
        greeting = "Buenas noches"
    date_label = f"{WEEKDAYS_ES[moment.weekday()]}, {moment.day} de {MONTHS_ES[moment.month - 1]} de {moment.year}"
    return greeting, date_label


def _patient_chart(series):
    values = [item["count"] for item in series]
    maximum = max([1, *values])
    left, right, top, bottom = 18, 582, 18, 142
    step = (right - left) / max(len(series) - 1, 1)
    points = []
    chart_items = []
    for index, item in enumerate(series):
        x = left + (index * step)
        y = bottom - ((item["count"] / maximum) * (bottom - top))
        points.append(f"{x:.1f},{y:.1f}")
        chart_items.append({**item, "x": round(x, 1), "y": round(y, 1)})
    return {
        "items": chart_items,
        "line_points": " ".join(points),
        "area_points": f"{left},{bottom} {' '.join(points)} {right},{bottom}",
        "maximum": maximum,
    }


def _activity_chart(moment, can_view_clinical):
    start = moment.date() - timedelta(days=6)
    days = [start + timedelta(days=index) for index in range(7)]
    appointment_counts = {day: 0 for day in days}
    consultation_counts = {day: 0 for day in days}
    for (day,) in Cita.query.with_entities(Cita.fecha).filter(Cita.fecha.between(start, moment.date())).all():
        appointment_counts[day] += 1
    if can_view_clinical:
        rows = (
            ValoracionAntropometrica.query.with_entities(ValoracionAntropometrica.fecha)
            .filter(ValoracionAntropometrica.fecha.between(start, moment.date()))
            .all()
        )
        for (day,) in rows:
            consultation_counts[day] += 1

    maximum = max([1, *appointment_counts.values(), *consultation_counts.values()])
    left, right, top, bottom = 18, 582, 18, 142
    step = (right - left) / 6
    items, appointment_points, consultation_points = [], [], []
    for index, day in enumerate(days):
        x = left + (index * step)
        appointments = appointment_counts[day]
        consultations = consultation_counts[day]
        appointment_y = bottom - ((appointments / maximum) * (bottom - top))
        consultation_y = bottom - ((consultations / maximum) * (bottom - top))
        appointment_points.append(f"{x:.1f},{appointment_y:.1f}")
        consultation_points.append(f"{x:.1f},{consultation_y:.1f}")
        items.append(
            {
                "date": day.isoformat(),
                "label": WEEKDAYS_ES[day.weekday()][:3].capitalize(),
                "appointments": appointments,
                "consultations": consultations,
                "x": round(x, 1),
                "appointment_y": round(appointment_y, 1),
                "consultation_y": round(consultation_y, 1),
            }
        )
    return {
        "items": items,
        "appointment_points": " ".join(appointment_points),
        "consultation_points": " ".join(consultation_points),
        "maximum": maximum,
    }


@main.route("/")
@login_required
def index():
    can_view_clinical = current_user.rol_clinico in {"admin", "medico"}
    now = datetime.now()
    greeting, date_label = _dashboard_time_context(now)
    start_raw, end_raw = request.args.get("fecha_inicio"), request.args.get("fecha_fin")
    if can_view_clinical and start_raw and end_raw:
        try:
            start = date_value(start_raw, "Fecha inicial")
            end = date_value(end_raw, "Fecha final")
            if start > end:
                raise ValidationError("La fecha inicial no puede ser posterior a la fecha final.")
            activity = ValoracionAntropometrica.obtener_por_rango(start, end)
        except ValidationError:
            activity = []
    elif can_view_clinical:
        activity = ValoracionAntropometrica.obtener_recientes(10)
    else:
        activity = []
    assessments_month = ValoracionAntropometrica.contar_mes_vigente() if can_view_clinical else 0
    total_patients = Paciente.contar_activos()
    today_appointments = Cita.obtener_citas_del_dia()
    scheduled_today = sum(1 for appointment in today_appointments if appointment.estatus == "Programada")
    attended_today = sum(1 for appointment in today_appointments if appointment.estatus == "Atendida")
    appointment_progress = round((attended_today / len(today_appointments)) * 100) if today_appointments else 0
    pending_schedule = Paciente.obtener_pendientes_por_agendar()
    without_assessment = Paciente.obtener_sin_valoracion_reciente(30) if can_view_clinical else []
    without_history = Paciente.obtener_sin_historial() if can_view_clinical else []
    monthly_patient_series = Paciente.resumen_altas_mensuales(6)
    template = PlantillaMensaje.obtener_activa()
    content = (
        template.contenido
        if template
        else "¡Hola, {nombre}! Han pasado {dias} días desde tu última consulta. ¿Cómo te has sentido?"
    )
    return render_template(
        "dashboard/index.html",
        can_view_clinical=can_view_clinical,
        saludo=greeting,
        fecha_actual_etiqueta=date_label,
        total_pacientes=total_patients,
        crecimiento_pacientes=Paciente.calcular_crecimiento_mensual(),
        total_valoraciones=ValoracionAntropometrica.query.count() if can_view_clinical else 0,
        total_historiales=HistorialClinico.query.count() if can_view_clinical else 0,
        total_plantillas=PlantillaMensaje.query.count() if can_view_clinical else 0,
        valoraciones_mes=assessments_month,
        promedio_diario=round(assessments_month / max(datetime.now().day, 1), 1),
        pacientes_seguimiento=Paciente.contar_en_seguimiento(),
        pacientes_sin_valoracion=without_assessment,
        pacientes_sin_historial=without_history,
        pacientes_recientes=Paciente.obtener_recientes(5),
        citas_del_dia=today_appointments,
        citas_programadas_hoy=scheduled_today,
        citas_atendidas_hoy=attended_today,
        consultas_pendientes_hoy=scheduled_today,
        progreso_citas_hoy=appointment_progress,
        proximas_citas=Cita.obtener_proximas(5, now),
        pendientes_por_agendar=pending_schedule,
        resumen_pacientes=_patient_chart(monthly_patient_series),
        resumen_actividad=_activity_chart(now, can_view_clinical),
        seguimiento_14_15=ValoracionAntropometrica.obtener_seguimiento_14_15_dias() if can_view_clinical else [],
        actividad_reciente=activity,
        contenido_plantilla=content,
        datetime=datetime,
    )


@main.route("/dashboard/marcar-seguimiento/<int:valoracion_id>", methods=["POST"])
@login_required
@roles_required("admin", "medico")
def marcar_seguimiento(valoracion_id):
    assessment = db.session.get(ValoracionAntropometrica, valoracion_id)
    if not assessment:
        return jsonify({"success": False, "error": "Valoración no encontrada"}), 404
    try:
        message = multiline_text(
            (request.get_json(silent=True) or {}).get("mensaje"), "Mensaje", maximum=2000, required=True
        )
    except ValidationError as error:
        return jsonify({"success": False, "error": str(error)}), 400
    assessment.seguimiento_15d_enviado = True
    assessment.fecha_seguimiento_15d = utcnow_naive()
    db.session.add(BitacoraContacto(paciente_id=assessment.paciente_id, usuario_id=current_user.id, mensaje=message))
    AuditLog.record(
        "seguimiento.sent", entity_type="valoracion", entity_id=assessment.id, metadata={"message_length": len(message)}
    )
    db.session.commit()
    return jsonify({"success": True, "message": "Seguimiento registrado correctamente"})


@main.route("/dashboard/omitir-seguimiento/<int:valoracion_id>", methods=["POST"])
@login_required
@roles_required("admin", "medico")
def omitir_seguimiento(valoracion_id):
    assessment = db.session.get(ValoracionAntropometrica, valoracion_id)
    if not assessment:
        return jsonify({"success": False, "error": "Valoración no encontrada"}), 404
    assessment.seguimiento_15d_enviado = True
    assessment.fecha_seguimiento_15d = utcnow_naive()
    AuditLog.record("seguimiento.skipped", entity_type="valoracion", entity_id=assessment.id)
    db.session.commit()
    return jsonify({"success": True, "message": "Seguimiento omitido correctamente"})
