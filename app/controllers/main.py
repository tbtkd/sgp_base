from datetime import datetime

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


@main.route("/")
@login_required
def index():
    can_view_clinical = current_user.rol_clinico in {"admin", "medico"}
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
    template = PlantillaMensaje.obtener_activa()
    content = (
        template.contenido
        if template
        else "¡Hola, {nombre}! Han pasado {dias} días desde tu última consulta. ¿Cómo te has sentido?"
    )
    return render_template(
        "dashboard/index.html",
        can_view_clinical=can_view_clinical,
        total_pacientes=Paciente.contar_activos(),
        crecimiento_pacientes=Paciente.calcular_crecimiento_mensual(),
        total_valoraciones=ValoracionAntropometrica.query.count() if can_view_clinical else 0,
        total_historiales=HistorialClinico.query.count() if can_view_clinical else 0,
        total_plantillas=PlantillaMensaje.query.count() if can_view_clinical else 0,
        valoraciones_mes=assessments_month,
        promedio_diario=round(assessments_month / max(datetime.now().day, 1), 1),
        pacientes_seguimiento=Paciente.contar_en_seguimiento(),
        pacientes_sin_valoracion=Paciente.obtener_sin_valoracion_reciente(30) if can_view_clinical else [],
        citas_del_dia=Cita.obtener_citas_del_dia(),
        pendientes_por_agendar=Paciente.obtener_pendientes_por_agendar(),
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
