from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.orm import joinedload

from app import db_orm as db
from app.core.audit import AuditLog
from app.core.auth import login_required
from app.core.security import roles_required
from app.core.validators import ValidationError, history_payload
from app.models.historial_clinico import HistorialClinico
from app.models.paciente import Paciente

historial_clinico = Blueprint("historial_clinico", __name__, url_prefix="/historial-clinico")
@historial_clinico.route("/paciente/<int:paciente_id>", methods=["GET", "POST"])
@login_required
@roles_required("admin", "medico")
def ver_crear_historial(paciente_id):
    patient = db.session.get(Paciente, paciente_id)
    if not patient:
        flash("Paciente no encontrado.", "error")
        return redirect(url_for("pacientes.lista_pacientes_activos"))
    history = HistorialClinico.obtener_por_paciente_id(paciente_id)
    if request.method == "POST":
        try:
            data = history_payload(request.form)
            if not history:
                history = HistorialClinico(paciente_id=paciente_id)
                db.session.add(history)
                action = "historial.create"
            else:
                action = "historial.update"
            for key, value in data.items():
                setattr(history, key, value)
            db.session.flush()
            AuditLog.record(
                action, entity_type="historial", entity_id=history.id, metadata={"paciente_id": paciente_id}
            )
            db.session.commit()
            flash("Historial clínico guardado exitosamente.", "success")
            return redirect(url_for("historial_clinico.ver_crear_historial", paciente_id=paciente_id))
        except ValidationError as error:
            flash(str(error), "error")
    return render_template(
        "historiales/historial_clinico.html",
        paciente=patient,
        historial=history,
    )


@historial_clinico.route("/")
@login_required
@roles_required("admin", "medico")
def lista_historiales():
    histories = (
        HistorialClinico.query.options(joinedload(HistorialClinico.paciente))
        .order_by(HistorialClinico.id.desc())
        .limit(500)
        .all()
    )
    return render_template("historiales/lista_historiales.html", historiales=histories)
