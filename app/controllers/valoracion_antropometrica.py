from datetime import date
from uuid import uuid4

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from app import db_orm as db
from app.core.audit import AuditLog
from app.core.auth import login_required
from app.core.security import roles_required
from app.core.validators import (
    ValidationError,
    assessment_payload,
    clinical_note_addendum_payload,
    clinical_note_close_payload,
    date_value,
)
from app.models.cita import Cita
from app.models.nota_clinica import AclaracionNotaClinica, NotaCierreClinico
from app.models.paciente import Paciente
from app.models.valoracion_antropometrica import ValoracionAntropometrica

valoracion = Blueprint("valoracion", __name__, url_prefix="/valoraciones")


def _can_manage_note(assessment):
    return current_user.rol_clinico == "admin" or (
        assessment.profesional_id is not None and assessment.profesional_id == current_user.id
    )


def _audit_note_denial(action, assessment, reason):
    AuditLog.record(
        action,
        entity_type="valoracion",
        entity_id=assessment.id,
        outcome="denied",
        metadata={"paciente_id": assessment.paciente_id, "motivo": reason},
    )
    db.session.commit()


def _projected_daily_number(raw_date=None):
    try:
        assessment_date = date_value(raw_date, "Fecha de consulta") if raw_date else date.today()
    except ValidationError:
        assessment_date = date.today()
    return ValoracionAntropometrica.siguiente_numero_diario(assessment_date)


@valoracion.route("/paciente/<int:paciente_id>/nueva", methods=["GET", "POST"])
@login_required
@roles_required("admin", "medico")
def nueva_valoracion(paciente_id):
    patient = db.session.get(Paciente, paciente_id)
    if not patient:
        flash("Paciente no encontrado.", "error")
        return redirect(url_for("pacientes.lista_pacientes_activos"))
    if request.method == "POST":
        try:
            raw = request.form.to_dict()
            # El cliente sólo muestra una proyección. El turno definitivo se
            # asigna dentro del bloqueo inmediatamente antes de persistir.
            raw["numero_cita"] = "1"
            data = assessment_payload(
                raw, allow_anthropometry=current_user.puede_capturar_antropometria
            )
            with ValoracionAntropometrica.bloqueo_numeracion_diaria():
                data["numero_cita"] = ValoracionAntropometrica.siguiente_numero_diario(data["fecha"])
                assessment = ValoracionAntropometrica.crear(paciente_id, data, profesional=current_user)
                appointment = Cita.query.filter_by(
                    paciente_id=paciente_id, fecha=data["fecha"], estatus="Programada"
                ).first()
                if appointment:
                    appointment.estado, appointment.estatus = "completada", "Atendida"
                db.session.flush()
                AuditLog.record(
                    "valoracion.create",
                    entity_type="valoracion",
                    entity_id=assessment.id,
                    metadata={
                        "paciente_id": paciente_id,
                        "profesional_id": current_user.id,
                        "perfil_profesional": current_user.perfil_profesional_clinico,
                        "fecha": data["fecha"].isoformat(),
                        "turno_diario": data["numero_cita"],
                    },
                )
                db.session.commit()
            flash("Consulta clínica registrada correctamente.", "success")
            return redirect(url_for("valoracion.lista_valoraciones", paciente_id=paciente_id))
        except ValidationError as error:
            flash(str(error), "error")
        except IntegrityError:
            db.session.rollback()
            flash("No se pudo asignar el turno de la consulta. Actualiza la página e inténtalo de nuevo.", "error")
        return render_template(
            "valoraciones/nueva_valoracion.html",
            paciente=patient,
            numero_diario=_projected_daily_number(request.form.get("fecha")),
            fecha_consulta_default=date.today().isoformat(),
        )
    return render_template(
        "valoraciones/nueva_valoracion.html",
        paciente=patient,
        numero_diario=_projected_daily_number(),
        fecha_consulta_default=date.today().isoformat(),
    )


@valoracion.route("/siguiente-numero")
@login_required
@roles_required("admin", "medico")
def siguiente_numero_diario():
    try:
        assessment_date = date_value(request.args.get("fecha"), "Fecha de consulta")
    except ValidationError as error:
        return jsonify({"success": False, "error": str(error)}), 400
    response = jsonify(
        {
            "success": True,
            "fecha": assessment_date.isoformat(),
            "numero": ValoracionAntropometrica.siguiente_numero_diario(assessment_date),
        }
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@valoracion.route("/paciente/<int:paciente_id>/lista")
@login_required
@roles_required("admin", "medico")
def lista_valoraciones(paciente_id):
    patient = db.get_or_404(Paciente, paciente_id)
    return render_template(
        "valoraciones/lista_valoraciones.html",
        paciente=patient,
        valoraciones=ValoracionAntropometrica.obtener_por_paciente(paciente_id),
    )


@valoracion.route("/")
@login_required
@roles_required("admin", "medico")
def todas_valoraciones():
    recipe_context = request.args.get("origen") == "recetas"
    search = str(request.args.get("q", "")).strip()[:100]
    order = request.args.get("orden", "fecha_desc")
    allowed_orders = {"fecha_desc", "fecha_asc"}
    if recipe_context:
        allowed_orders |= {
            "paciente_asc", "paciente_desc", "motivo_asc", "motivo_desc",
            "diagnostico_asc", "diagnostico_desc",
        }
    if order not in allowed_orders:
        order = "fecha_desc"
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except (TypeError, ValueError):
        page = 1
    per_page = 25
    finder = (
        ValoracionAntropometrica.buscar_todas
        if recipe_context
        else ValoracionAntropometrica.buscar_ultimas_por_paciente
    )
    assessments, total = finder(search, order, page, per_page)
    pages = max((total + per_page - 1) // per_page, 1)
    if page > pages:
        page = pages
        assessments, total = finder(search, order, page, per_page)
    return render_template(
        "valoraciones/todas_valoraciones.html",
        valoraciones=assessments,
        modo_recetas=recipe_context,
        busqueda=search,
        orden=order,
        pagina=page,
        paginas=pages,
        total=total,
    )


@valoracion.route("/valoraciones/<int:valoracion_id>")
@login_required
@roles_required("admin", "medico")
def detalle_valoracion(valoracion_id):
    assessment = db.get_or_404(ValoracionAntropometrica, valoracion_id)
    history = ValoracionAntropometrica.obtener_por_paciente(assessment.paciente_id)
    previous = next((history[i + 1] for i, item in enumerate(history[:-1]) if item.id == assessment.id), None)
    return render_template(
        "valoraciones/detalle_valoracion.html",
        valoracion=assessment,
        valoracion_anterior=previous,
        paciente=assessment.paciente,
        historial_valoraciones=history,
        puede_gestionar_nota=_can_manage_note(assessment),
        cierre_operation_key=str(uuid4()),
        aclaracion_operation_key=str(uuid4()),
    )


@valoracion.route("/valoraciones/<int:valoracion_id>/imprimir")
@login_required
@roles_required("admin", "medico")
def imprimir_valoracion(valoracion_id):
    assessment = db.get_or_404(ValoracionAntropometrica, valoracion_id)
    return render_template(
        "valoraciones/imprimir_valoracion.html",
        valoracion=assessment,
        paciente=assessment.paciente,
    )


@valoracion.route("/valoraciones/<int:valoracion_id>/editar", methods=["GET", "POST"])
@login_required
@roles_required("admin", "medico")
def editar_valoracion(valoracion_id):
    assessment = db.get_or_404(ValoracionAntropometrica, valoracion_id)
    if assessment.esta_cerrada:
        if request.method == "POST":
            _audit_note_denial("valoracion.update", assessment, "nota_cerrada")
        flash("La nota ya fue cerrada y no puede modificarse. Si necesitas corregir o ampliar algo, agrega una aclaración.", "warning")
        return redirect(url_for("valoracion.detalle_valoracion", valoracion_id=assessment.id))
    if request.method == "POST":
        try:
            raw = request.form.to_dict()
            raw["numero_cita"] = str(assessment.numero_cita)
            data = assessment_payload(
                raw, allow_anthropometry=current_user.puede_capturar_antropometria
            )
            previous_date = assessment.fecha
            previous_number = assessment.numero_cita
            with ValoracionAntropometrica.bloqueo_numeracion_diaria():
                if data["fecha"] != previous_date:
                    data["numero_cita"] = ValoracionAntropometrica.siguiente_numero_diario(data["fecha"])
                else:
                    data["numero_cita"] = previous_number
                for key, value in data.items():
                    setattr(assessment, key, value)
                AuditLog.record(
                    "valoracion.update",
                    entity_type="valoracion",
                    entity_id=assessment.id,
                    metadata={
                        "fecha_anterior": previous_date.isoformat(),
                        "turno_anterior": previous_number,
                        "fecha": assessment.fecha.isoformat(),
                        "turno_diario": assessment.numero_cita,
                    },
                )
                db.session.commit()
            flash("Consulta clínica actualizada correctamente.", "success")
            return redirect(url_for("valoracion.detalle_valoracion", valoracion_id=assessment.id))
        except ValidationError as error:
            flash(str(error), "error")
        except IntegrityError:
            db.session.rollback()
            flash("No se pudo asignar un turno para la nueva fecha. Actualiza la página e inténtalo de nuevo.", "error")
    return render_template(
        "valoraciones/editar_valoracion.html",
        valoracion=assessment,
        paciente=assessment.paciente,
        numero_diario=assessment.numero_cita,
        fecha_consulta_default=date.today().isoformat(),
    )


@valoracion.route("/valoraciones/<int:valoracion_id>/eliminar", methods=["POST"])
@login_required
@roles_required("admin", "medico")
def eliminar_valoracion(valoracion_id):
    assessment = db.get_or_404(ValoracionAntropometrica, valoracion_id)
    if assessment.esta_cerrada:
        _audit_note_denial("valoracion.delete", assessment, "nota_cerrada")
        flash("La nota ya fue cerrada y debe conservarse. No es posible eliminarla.", "warning")
        return redirect(url_for("valoracion.detalle_valoracion", valoracion_id=assessment.id))
    if assessment.recetas:
        flash("Esta consulta no puede eliminarse porque tiene recetas guardadas. Para conservarlas, la consulta debe permanecer.", "warning")
        return redirect(url_for("valoracion.detalle_valoracion", valoracion_id=assessment.id))
    patient_id = assessment.paciente_id
    AuditLog.record(
        "valoracion.delete", entity_type="valoracion", entity_id=assessment.id, metadata={"paciente_id": patient_id}
    )
    db.session.delete(assessment)
    db.session.commit()
    flash("Consulta clínica eliminada correctamente.", "success")
    return redirect(url_for("valoracion.lista_valoraciones", paciente_id=patient_id))


@valoracion.route("/valoraciones/<int:valoracion_id>/cerrar", methods=["POST"])
@login_required
@roles_required("admin", "medico")
def cerrar_nota(valoracion_id):
    assessment = db.get_or_404(ValoracionAntropometrica, valoracion_id)
    if not _can_manage_note(assessment):
        _audit_note_denial("valoracion.close", assessment, "sin_permiso")
        flash("Sólo el profesional que registró la nota o una cuenta de Administración puede cerrarla.", "error")
        return redirect(url_for("valoracion.detalle_valoracion", valoracion_id=assessment.id)), 403
    try:
        data = clinical_note_close_payload(request.form)
        if assessment.esta_cerrada:
            flash("La nota ya se encuentra cerrada.", "info")
            return redirect(url_for("valoracion.detalle_valoracion", valoracion_id=assessment.id))
        duplicate = NotaCierreClinico.query.filter_by(operation_key=data["operation_key"]).first()
        if duplicate:
            flash("Esta solicitud ya fue atendida.", "info")
            return redirect(url_for("valoracion.detalle_valoracion", valoracion_id=assessment.id))
        closure = NotaCierreClinico(
            valoracion_id=assessment.id,
            cerrado_por_id=current_user.id,
            responsable_nombre=current_user.nombre_completo,
            responsable_perfil=current_user.perfil_profesional_etiqueta or current_user.rol_etiqueta,
            operation_key=data["operation_key"],
        )
        db.session.add(closure)
        AuditLog.record(
            "valoracion.close",
            entity_type="valoracion",
            entity_id=assessment.id,
            metadata={"paciente_id": assessment.paciente_id, "responsable_id": current_user.id},
        )
        db.session.commit()
        flash("La nota quedó cerrada. Su contenido original ya no se puede modificar.", "success")
    except ValidationError as error:
        db.session.rollback()
        _audit_note_denial("valoracion.close", assessment, "datos_de_cierre_invalidos")
        flash(str(error), "error")
    except IntegrityError:
        db.session.rollback()
        flash("La nota ya fue cerrada desde otra solicitud.", "info")
    return redirect(url_for("valoracion.detalle_valoracion", valoracion_id=assessment.id))


@valoracion.route("/valoraciones/<int:valoracion_id>/aclaraciones", methods=["POST"])
@login_required
@roles_required("admin", "medico")
def agregar_aclaracion(valoracion_id):
    assessment = db.get_or_404(ValoracionAntropometrica, valoracion_id)
    if not _can_manage_note(assessment):
        _audit_note_denial("valoracion.addendum", assessment, "sin_permiso")
        flash("Sólo el profesional que registró la nota o una cuenta de Administración puede agregar aclaraciones.", "error")
        return redirect(url_for("valoracion.detalle_valoracion", valoracion_id=assessment.id)), 403
    if not assessment.esta_cerrada:
        _audit_note_denial("valoracion.addendum", assessment, "nota_sin_cerrar")
        flash("Primero debes cerrar la nota para poder agregar una aclaración.", "warning")
        return redirect(url_for("valoracion.detalle_valoracion", valoracion_id=assessment.id))
    try:
        data = clinical_note_addendum_payload(request.form)
        duplicate = AclaracionNotaClinica.query.filter_by(operation_key=data["operation_key"]).first()
        if duplicate:
            flash("Esta aclaración ya había sido guardada.", "info")
            return redirect(url_for("valoracion.detalle_valoracion", valoracion_id=assessment.id))
        with AclaracionNotaClinica.bloqueo_numeracion():
            addendum = AclaracionNotaClinica(
                cierre_id=assessment.cierre_nota.id,
                numero=AclaracionNotaClinica.siguiente_numero(assessment.cierre_nota.id),
                autor_id=current_user.id,
                autor_nombre=current_user.nombre_completo,
                autor_perfil=current_user.perfil_profesional_etiqueta or current_user.rol_etiqueta,
                **data,
            )
            db.session.add(addendum)
            db.session.flush()
            AuditLog.record(
                "valoracion.addendum",
                entity_type="valoracion",
                entity_id=assessment.id,
                metadata={
                    "paciente_id": assessment.paciente_id,
                    "aclaracion_id": addendum.id,
                    "numero": addendum.numero,
                },
            )
            db.session.commit()
        flash("La aclaración se agregó sin cambiar el contenido original de la nota.", "success")
    except ValidationError as error:
        db.session.rollback()
        _audit_note_denial("valoracion.addendum", assessment, "datos_de_aclaracion_invalidos")
        flash(str(error), "error")
    except IntegrityError:
        db.session.rollback()
        flash("No fue posible guardar la aclaración. Actualiza la página e inténtalo de nuevo.", "error")
    return redirect(url_for("valoracion.detalle_valoracion", valoracion_id=assessment.id))
