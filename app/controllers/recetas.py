from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from app import db_orm as db
from app.core.audit import AuditLog
from app.core.auth import login_required
from app.core.security import roles_required
from app.core.validators import (
    PRESCRIPTION_ITEM_FIELDS,
    ValidationError,
    prescription_payload,
    prescription_replacement_reason,
)
from app.models.historial_clinico import HistorialClinico
from app.models.receta import Receta
from app.models.valoracion_antropometrica import ValoracionAntropometrica

recetas = Blueprint("recetas", __name__, url_prefix="/recetas")
MAX_PRESCRIPTIONS_PER_ASSESSMENT = 50


def _medication_rows(form=None, prescription=None):
    if form:
        columns = {field: form.getlist(f"{field}[]") for field in PRESCRIPTION_ITEM_FIELDS}
        count = max((len(values) for values in columns.values()), default=0)
        orders = form.getlist("orden_medicamento[]")
        return [
            {
                **{field: columns[field][index] if index < len(columns[field]) else "" for field in columns},
                "_capture_order": orders[index] if index < len(orders) else index + 1,
            }
            for index in range(count)
        ] or [{"_capture_order": 1}]
    if prescription:
        return [
            {
                **{field: getattr(item, field) or "" for field in PRESCRIPTION_ITEM_FIELDS},
                "_capture_order": index,
            }
            for index, item in enumerate(prescription.medicamentos, start=1)
        ] or [{"_capture_order": 1}]
    return [{"_capture_order": 1}]


def _known_allergies(patient_id):
    history = HistorialClinico.obtener_por_paciente_id(patient_id)
    if not history:
        return None
    details = []
    if history.alergias_medicamentosas:
        details.append(f"Medicamentos: {history.alergias_medicamentosas}")
    if history.alergias_alimentarias:
        details.append(f"Alimentos: {history.alergias_alimentarias}")
    return " | ".join(details) or None


def _emission_requirements(assessment):
    if not current_user.puede_emitir_receta_ordinaria:
        abort(403, description="Tu perfil profesional no está autorizado para emitir recetas médicas ordinarias.")
    if assessment.paciente.status != "activo":
        raise ValidationError("No es posible emitir una receta para un paciente inactivo.")
    if len(assessment.recetas) >= MAX_PRESCRIPTIONS_PER_ASSESSMENT:
        raise ValidationError("La consulta alcanzó el límite de documentos; solicita una revisión administrativa.")
    return current_user.requisitos_receta_faltantes


def _render_form(assessment, *, mode, source=None, status=200):
    observations = request.form.get("observaciones") if request.form else None
    if observations is None and source is not None:
        observations = source.observaciones or ""
    return (
        render_template(
            "recetas/nueva_receta.html",
            valoracion=assessment,
            paciente=assessment.paciente,
            requisitos_faltantes=current_user.requisitos_receta_faltantes,
            medicamento_rows=_medication_rows(request.form, source),
            modo=mode,
            receta_origen=source,
            observaciones_form=observations or "",
        ),
        status,
    )


def _create_prescription(assessment, *, prescription_type, source=None, replacement_reason=None):
    data = prescription_payload(request.form)
    prescription = Receta.crear(
        assessment,
        assessment.paciente,
        current_user,
        data,
        alergias_conocidas=_known_allergies(assessment.paciente_id),
        tipo=prescription_type,
        version=Receta.siguiente_version(assessment.id),
        receta_sustituida=source,
        motivo_cambio=replacement_reason,
    )
    if source is not None:
        source.marcar_sustituida(current_user)
    db.session.flush()
    event = "receta.replace" if source is not None else (
        "receta.additional" if prescription_type == "adicional" else "receta.create"
    )
    metadata = {
        "valoracion_id": assessment.id,
        "paciente_id": assessment.paciente_id,
        "profesional_id": current_user.id,
        "medicamentos": len(prescription.medicamentos),
        "tipo": prescription.tipo,
        "version": prescription.version,
    }
    if source is not None:
        metadata["receta_sustituida_id"] = source.id
    AuditLog.record(event, entity_type="receta", entity_id=prescription.id, metadata=metadata)
    db.session.commit()
    current_app.logger.info(
        "Documento de receta emitido; receta_id=%s valoracion_id=%s tipo=%s version=%s",
        prescription.id,
        assessment.id,
        prescription.tipo,
        prescription.version,
    )
    return prescription


@recetas.route("/valoracion/<int:valoracion_id>/nueva", methods=["GET", "POST"])
@login_required
@roles_required("admin", "medico")
def nueva_receta(valoracion_id):
    assessment = db.get_or_404(ValoracionAntropometrica, valoracion_id)
    try:
        missing = _emission_requirements(assessment)
    except ValidationError as error:
        flash(str(error), "error")
        return redirect(url_for("valoracion.detalle_valoracion", valoracion_id=assessment.id))
    if assessment.recetas:
        flash(
            "La consulta ya tiene una receta inicial. Puedes emitir una adicional o sustituir una vigente.",
            "info",
        )
        return redirect(url_for("valoracion.detalle_valoracion", valoracion_id=assessment.id))
    if request.method == "POST" and missing:
        flash("Completa los datos profesionales obligatorios antes de emitir una receta.", "error")
        return _render_form(assessment, mode="original", status=422)
    if request.method == "POST":
        try:
            prescription = _create_prescription(assessment, prescription_type="original")
            flash("Receta original emitida. Revísala, imprímela y agrega la firma autógrafa.", "success")
            return redirect(url_for("recetas.imprimir_receta", receta_id=prescription.id))
        except ValidationError as error:
            current_app.logger.warning("Receta rechazada por validación; valoracion_id=%s", assessment.id)
            flash(str(error), "error")
        except IntegrityError:
            db.session.rollback()
            current_app.logger.warning("Conflicto al emitir receta original; valoracion_id=%s", assessment.id)
            flash("No fue posible emitir la receta. Recarga la consulta y verifica los documentos existentes.", "error")
    return _render_form(assessment, mode="original")


@recetas.route("/valoracion/<int:valoracion_id>/adicional", methods=["GET", "POST"])
@login_required
@roles_required("admin", "medico")
def receta_adicional(valoracion_id):
    assessment = db.get_or_404(ValoracionAntropometrica, valoracion_id)
    try:
        missing = _emission_requirements(assessment)
    except ValidationError as error:
        flash(str(error), "error")
        return redirect(url_for("valoracion.detalle_valoracion", valoracion_id=assessment.id))
    if not assessment.recetas:
        return redirect(url_for("recetas.nueva_receta", valoracion_id=assessment.id))
    if request.method == "POST" and missing:
        flash("Completa los datos profesionales obligatorios antes de emitir una receta.", "error")
        return _render_form(assessment, mode="adicional", status=422)
    if request.method == "POST":
        try:
            prescription = _create_prescription(assessment, prescription_type="adicional")
            flash("Receta adicional emitida con folio independiente.", "success")
            return redirect(url_for("recetas.imprimir_receta", receta_id=prescription.id))
        except ValidationError as error:
            current_app.logger.warning("Receta adicional rechazada; valoracion_id=%s", assessment.id)
            flash(str(error), "error")
        except IntegrityError:
            db.session.rollback()
            current_app.logger.warning("Conflicto al emitir receta adicional; valoracion_id=%s", assessment.id)
            flash("No fue posible emitir la receta adicional. Recarga la consulta e inténtalo de nuevo.", "error")
    return _render_form(assessment, mode="adicional")


@recetas.route("/<int:receta_id>/sustituir", methods=["GET", "POST"])
@login_required
@roles_required("admin", "medico")
def sustituir_receta(receta_id):
    source = db.get_or_404(Receta, receta_id)
    assessment = source.valoracion
    try:
        missing = _emission_requirements(assessment)
    except ValidationError as error:
        flash(str(error), "error")
        return redirect(url_for("valoracion.detalle_valoracion", valoracion_id=assessment.id))
    if not source.esta_vigente or source.receta_reemplazo is not None:
        flash("Esta receta ya fue sustituida y no puede volver a modificarse.", "warning")
        return redirect(url_for("recetas.imprimir_receta", receta_id=source.id))
    if request.method == "POST" and missing:
        flash("Completa los datos profesionales obligatorios antes de sustituir la receta.", "error")
        return _render_form(assessment, mode="sustitucion", source=source, status=422)
    if request.method == "POST":
        try:
            reason = prescription_replacement_reason(request.form.get("motivo_cambio"))
            replacement = _create_prescription(
                assessment,
                prescription_type="sustitucion",
                source=source,
                replacement_reason=reason,
            )
            flash("Receta sustituida. El folio anterior se conserva marcado como no vigente.", "success")
            return redirect(url_for("recetas.imprimir_receta", receta_id=replacement.id))
        except ValidationError as error:
            current_app.logger.warning("Sustitución de receta rechazada; receta_id=%s", source.id)
            flash(str(error), "error")
        except (IntegrityError, ValueError):
            db.session.rollback()
            current_app.logger.warning("Conflicto al sustituir receta; receta_id=%s", source.id)
            flash("No fue posible sustituir la receta; pudo haber sido reemplazada desde otra sesión.", "error")
    return _render_form(assessment, mode="sustitucion", source=source)


@recetas.route("/<int:receta_id>/imprimir")
@login_required
@roles_required("admin", "medico")
def imprimir_receta(receta_id):
    prescription = db.get_or_404(Receta, receta_id)
    return render_template("recetas/imprimir_receta.html", receta=prescription)
