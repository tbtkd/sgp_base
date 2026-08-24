from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from app import db_orm as db
from app.core.audit import AuditLog
from app.core.auth import login_required
from app.core.security import roles_required
from app.core.validators import ValidationError, assessment_payload
from app.models.cita import Cita
from app.models.paciente import Paciente
from app.models.valoracion_antropometrica import ValoracionAntropometrica

valoracion = Blueprint("valoracion", __name__, url_prefix="/valoraciones")


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
            data = assessment_payload(
                request.form, allow_anthropometry=current_user.puede_capturar_antropometria
            )
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
                },
            )
            db.session.commit()
            flash("Consulta clínica registrada correctamente.", "success")
            return redirect(url_for("valoracion.lista_valoraciones", paciente_id=paciente_id))
        except ValidationError as error:
            flash(str(error), "error")
        except IntegrityError:
            db.session.rollback()
            flash("Ya existe una consulta con el mismo paciente, número de cita y fecha.", "error")
        return render_template("valoraciones/nueva_valoracion.html", paciente=patient, form_data=request.form)
    return render_template("valoraciones/nueva_valoracion.html", paciente=patient)


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
    return render_template(
        "valoraciones/todas_valoraciones.html", valoraciones=ValoracionAntropometrica.obtener_todas()
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
    if request.method == "POST":
        try:
            raw = request.form.to_dict()
            raw.setdefault("numero_cita", str(assessment.numero_cita))
            data = assessment_payload(
                raw, allow_anthropometry=current_user.puede_capturar_antropometria
            )
            for key, value in data.items():
                setattr(assessment, key, value)
            AuditLog.record("valoracion.update", entity_type="valoracion", entity_id=assessment.id)
            db.session.commit()
            flash("Consulta clínica actualizada correctamente.", "success")
            return redirect(url_for("valoracion.detalle_valoracion", valoracion_id=assessment.id))
        except ValidationError as error:
            flash(str(error), "error")
        except IntegrityError:
            db.session.rollback()
            flash("La actualización duplicaría otra consulta.", "error")
    return render_template("valoraciones/editar_valoracion.html", valoracion=assessment, paciente=assessment.paciente)


@valoracion.route("/valoraciones/<int:valoracion_id>/eliminar", methods=["POST"])
@login_required
@roles_required("admin", "medico")
def eliminar_valoracion(valoracion_id):
    assessment = db.get_or_404(ValoracionAntropometrica, valoracion_id)
    if assessment.recetas:
        flash("La consulta no puede eliminarse porque tiene recetas emitidas e inmutables.", "warning")
        return redirect(url_for("valoracion.detalle_valoracion", valoracion_id=assessment.id))
    patient_id = assessment.paciente_id
    AuditLog.record(
        "valoracion.delete", entity_type="valoracion", entity_id=assessment.id, metadata={"paciente_id": patient_id}
    )
    db.session.delete(assessment)
    db.session.commit()
    flash("Consulta clínica eliminada correctamente.", "success")
    return redirect(url_for("valoracion.lista_valoraciones", paciente_id=patient_id))
