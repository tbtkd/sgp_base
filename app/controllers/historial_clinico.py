from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import asc, desc, func, or_
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
    from app.core.text import search_terms

    search = str(request.args.get("q", "")).strip()[:100]
    order = request.args.get("orden", "paciente_asc")
    allowed_orders = {
        "paciente_asc", "paciente_desc", "antecedentes_asc", "antecedentes_desc",
        "alergias_asc", "alergias_desc", "actividad_asc", "actividad_desc",
    }
    if order not in allowed_orders:
        order = "paciente_asc"
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except (TypeError, ValueError):
        page = 1
    per_page = 25
    query = (
        HistorialClinico.query.options(joinedload(HistorialClinico.paciente))
        .join(HistorialClinico.paciente)
    )
    full_name = func.sgpn_search_key(
        func.trim(
            Paciente.nombre + " " + Paciente.apellido_paterno + " "
            + func.coalesce(Paciente.apellido_materno, "")
        )
    )
    antecedents = func.sgpn_search_key(
        func.coalesce(HistorialClinico.enfermedades_previas, "") + " "
        + func.coalesce(HistorialClinico.antecedentes_familiares, "")
    )
    allergies = func.sgpn_search_key(
        func.coalesce(HistorialClinico.alergias_medicamentosas, "") + " "
        + func.coalesce(HistorialClinico.alergias_alimentarias, "") + " "
        + func.coalesce(HistorialClinico.medicamentos_actuales, "")
    )
    activity = func.sgpn_search_key(HistorialClinico.actividad_fisica)
    searchable = (full_name, antecedents, allergies, activity)
    condition_aliases = (
        (HistorialClinico.antecedente_diabetes, "diabetes"),
        (HistorialClinico.antecedente_hipertension, "hipertension arterial"),
        (HistorialClinico.antecedente_cardiopatias, "cardiopatia enfermedad corazon cardiovascular"),
        (HistorialClinico.antecedente_cancer, "cancer oncologico"),
        (HistorialClinico.antecedente_asma_epoc, "asma epoc enfermedad pulmonar respiratoria"),
        (HistorialClinico.antecedente_enfermedad_renal, "enfermedad renal rinon"),
        (HistorialClinico.antecedente_enfermedad_hepatica, "enfermedad hepatica higado"),
        (HistorialClinico.antecedente_tiroides, "tiroides tiroideo"),
        (HistorialClinico.antecedente_neurologicos, "neurologico neurologia"),
        (HistorialClinico.antecedente_psiquiatricos, "psiquiatrico salud mental"),
        (HistorialClinico.antecedente_autoinmunes, "autoinmune"),
        (HistorialClinico.antecedente_dislipidemia, "dislipidemia colesterol trigliceridos"),
        (HistorialClinico.antecedente_obesidad, "obesidad"),
    )
    for term in search_terms(search):
        matches = [field.contains(term, autoescape=True) for field in searchable]
        matches.extend(column.is_(True) for column, aliases in condition_aliases if term in aliases)
        query = query.filter(or_(*matches))
    orders = {
        "paciente_asc": asc(full_name), "paciente_desc": desc(full_name),
        "antecedentes_asc": asc(antecedents), "antecedentes_desc": desc(antecedents),
        "alergias_asc": asc(allergies), "alergias_desc": desc(allergies),
        "actividad_asc": asc(activity), "actividad_desc": desc(activity),
    }
    query = query.order_by(orders[order], HistorialClinico.id.asc())
    total = query.count()
    pages = max((total + per_page - 1) // per_page, 1)
    page = min(page, pages)
    histories = query.offset((page - 1) * per_page).limit(per_page).all()
    return render_template(
        "historiales/lista_historiales.html",
        historiales=histories,
        busqueda=search,
        orden=order,
        pagina=page,
        paginas=pages,
        total=total,
    )
