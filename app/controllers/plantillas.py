from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from app import db_orm as db
from app.core.audit import AuditLog
from app.core.auth import login_required
from app.core.security import roles_required
from app.core.validators import ValidationError, clean_text, multiline_text
from app.models.plantilla import PlantillaMensaje

plantillas_bp = Blueprint("plantillas", __name__, url_prefix="/plantillas-mensajes")


def _payload(form):
    title = clean_text(form.get("titulo"), "Título", minimum=2, maximum=100, required=True)
    content = multiline_text(form.get("contenido"), "Contenido", maximum=2000, required=True)
    remainder = content.replace("{nombre}", "").replace("{dias}", "")
    if "{" in remainder or "}" in remainder:
        raise ValidationError("Solo se permiten las variables {nombre} y {dias}.")
    return title, content, form.get("esta_activa") == "on"


@plantillas_bp.route("/")
@login_required
@roles_required("admin", "medico")
def index():
    return render_template(
        "plantillas/whatsapp.html", plantillas=PlantillaMensaje.query.order_by(PlantillaMensaje.titulo).all()
    )


@plantillas_bp.route("/nueva", methods=["GET", "POST"])
@login_required
@roles_required("admin", "medico")
def nueva():
    if request.method == "POST":
        try:
            title, content, active = _payload(request.form)
            if active:
                PlantillaMensaje.query.update({PlantillaMensaje.esta_activa: False})
            template = PlantillaMensaje(titulo=title, contenido=content, esta_activa=active)
            db.session.add(template)
            db.session.flush()
            AuditLog.record("plantilla.create", entity_type="plantilla", entity_id=template.id)
            db.session.commit()
            flash("Plantilla creada correctamente.", "success")
            return redirect(url_for("plantillas.index"))
        except ValidationError as error:
            flash(str(error), "error")
    return render_template("plantillas/form.html", plantilla=None)


@plantillas_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
@roles_required("admin", "medico")
def editar(id):
    template = db.get_or_404(PlantillaMensaje, id)
    if request.method == "POST":
        try:
            title, content, active = _payload(request.form)
            if active:
                PlantillaMensaje.query.update({PlantillaMensaje.esta_activa: False})
            template.titulo, template.contenido, template.esta_activa = title, content, active
            AuditLog.record("plantilla.update", entity_type="plantilla", entity_id=template.id)
            db.session.commit()
            flash("Plantilla actualizada correctamente.", "success")
            return redirect(url_for("plantillas.index"))
        except ValidationError as error:
            flash(str(error), "error")
    return render_template("plantillas/form.html", plantilla=template)


@plantillas_bp.route("/eliminar/<int:id>", methods=["POST"])
@login_required
@roles_required("admin", "medico")
def eliminar(id):
    template = db.get_or_404(PlantillaMensaje, id)
    AuditLog.record("plantilla.delete", entity_type="plantilla", entity_id=template.id)
    db.session.delete(template)
    db.session.commit()
    flash("Plantilla eliminada correctamente.", "success")
    return redirect(url_for("plantillas.index"))


@plantillas_bp.route("/activar/<int:id>", methods=["POST"])
@login_required
@roles_required("admin", "medico")
def activar(id):
    template = db.session.get(PlantillaMensaje, id)
    if not template:
        return jsonify({"success": False, "error": "Plantilla no encontrada"}), 404
    PlantillaMensaje.query.update({PlantillaMensaje.esta_activa: False})
    template.esta_activa = True
    AuditLog.record("plantilla.activate", entity_type="plantilla", entity_id=template.id)
    db.session.commit()
    return jsonify({"success": True, "message": "Plantilla activada"})
