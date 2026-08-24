import logging
from urllib.parse import urljoin, urlparse

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app import db_orm as db
from app.core.audit import AuditLog
from app.core.auth import admin_required, login_required
from app.core.password_recovery import reset_user_password
from app.core.security import login_blocked, register_login_failure, reset_login_failures
from app.core.validators import ValidationError, password_change_payload, user_payload
from app.models.usuario import Usuario

logger = logging.getLogger(__name__)
auth = Blueprint("auth", __name__)
DUMMY_HASH = generate_password_hash("dummy-password-never-used", method="scrypt")


def _safe_next(target):
    if not target:
        return None
    host = urlparse(request.host_url)
    candidate = urlparse(urljoin(request.host_url, target))
    return target if candidate.scheme in {"http", "https"} and candidate.netloc == host.netloc else None


@auth.route("/login", methods=["GET", "POST"])
def login():
    if Usuario.query.count() == 0:
        return redirect(url_for("auth.setup"))
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    if request.method == "POST":
        ip_address = request.remote_addr or "unknown"
        if login_blocked(ip_address):
            AuditLog.record("auth.login", outcome="denied", description="IP bloqueada temporalmente por intentos fallidos")
            db.session.commit()
            flash("Demasiados intentos fallidos. Espera 5 minutos antes de volver a intentarlo.", "warning")
            return render_template("auth/login.html"), 429
        username = str(request.form.get("username", "")).strip().lower()[:50]
        supplied_password = str(request.form.get("password", ""))[:128]
        user = Usuario.find_by_username(username)

        valid = user.check_password(supplied_password) if user else check_password_hash(DUMMY_HASH, supplied_password)
        if user and user.is_locked:
            valid = False
        if valid and user and user.status == "activo":
            user.record_successful_login()
            AuditLog.record("auth.login", entity_type="usuario", entity_id=user.id, user_id=user.id)
            db.session.commit()
            reset_login_failures(ip_address)
            session.clear()
            login_user(user, remember=request.form.get("remember") == "on", fresh=True)
            session.permanent = True
            session["auth_version"] = int(user.auth_version or 0)
            if user.uses_temporary_email:
                if user.rol_clinico == "admin":
                    flash("Tu cuenta usa un correo temporal de migración. Actualízalo desde Usuarios.", "warning")
                else:
                    flash("Tu cuenta usa un correo temporal de migración. Solicita al administrador actualizarlo.", "warning")
            destination = (
                url_for("auth.cambiar_contrasena")
                if user.must_change_password
                else (_safe_next(request.args.get("next")) or url_for("main.index"))
            )
            return redirect(destination)

        register_login_failure(ip_address)
        if user and not user.is_locked:
            user.record_failed_login()
        AuditLog.record(
            "auth.login",
            entity_type="usuario",
            entity_id=user.id if user else None,
            outcome="failure",
            user_id=user.id if user else None,
            description="Intento de autenticación rechazado",
        )
        db.session.commit()
        logger.warning("Intento de autenticación rechazado")
        flash("Usuario o contraseña incorrectos. Tras cinco intentos deberás esperar 5 minutos.", "error")
    return render_template("auth/login.html")


@auth.route("/recuperar-acceso")
def recuperar_acceso():
    """Instrucciones genéricas; no revela si una cuenta existe."""
    return render_template("auth/recuperar_acceso.html")


@auth.route("/mi-cuenta/cambiar-contrasena", methods=["GET", "POST"])
@login_required
def cambiar_contrasena():
    if request.method == "POST":
        try:
            data = password_change_payload(request.form, current_user)
            if not current_user.check_password(data["current_password"]):
                AuditLog.record(
                    "usuario.password_change",
                    entity_type="usuario",
                    entity_id=current_user.id,
                    outcome="failure",
                    description="Cambio de contraseña rechazado",
                )
                db.session.commit()
                logger.warning("Cambio de contraseña rechazado; usuario_id=%s", current_user.id)
                flash("La contraseña actual no es correcta.", "error")
                return render_template("auth/cambiar_contrasena.html"), 422
            current_user.replace_password(data["new_password"], temporary=False)
            AuditLog.record(
                "usuario.password_change",
                entity_type="usuario",
                entity_id=current_user.id,
                metadata={"sesiones_invalidadas": True},
            )
            db.session.commit()
            session["auth_version"] = int(current_user.auth_version or 0)
            logger.info("Contraseña actualizada; usuario_id=%s", current_user.id)
            flash("Contraseña actualizada. Las demás sesiones quedaron cerradas.", "success")
            return redirect(url_for("main.index"))
        except ValidationError as error:
            flash(str(error), "error")
            return render_template("auth/cambiar_contrasena.html"), 422
    return render_template("auth/cambiar_contrasena.html")


@auth.route("/setup", methods=["GET", "POST"])
def setup():
    if Usuario.query.count() > 0:
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        try:
            raw = request.form.to_dict()
            raw["rol"] = "admin"
            data = user_payload(raw, include_password=True)
            user = Usuario.create(**data)
            db.session.flush()
            AuditLog.record("system.bootstrap_admin", entity_type="usuario", entity_id=user.id, user_id=user.id)
            db.session.commit()
            flash("Administrador inicial creado. Ya puedes iniciar sesión.", "success")
            return redirect(url_for("auth.login"))
        except ValidationError as error:
            flash(str(error), "error")
        except IntegrityError:
            db.session.rollback()
            flash("No fue posible crear el administrador inicial.", "error")
    return render_template("auth/setup.html")


@auth.route("/logout", methods=["POST"])
@login_required
def logout():
    user_id = current_user.id
    AuditLog.record("auth.logout", entity_type="usuario", entity_id=user_id)
    db.session.commit()
    session.clear()
    logout_user()
    return redirect(url_for("auth.login"))


@auth.route("/registrar-usuario", methods=["GET", "POST"])
@admin_required
def registrar_usuario():
    if request.method == "POST":
        try:
            data = user_payload(request.form, include_password=True)
            user = Usuario.create(**data)
            db.session.flush()
            AuditLog.record(
                "usuario.create",
                entity_type="usuario",
                entity_id=user.id,
                metadata={"rol": user.rol, "perfil_profesional": user.perfil_profesional},
            )
            db.session.commit()
            flash("Usuario registrado exitosamente.", "success")
            return redirect(url_for("auth.lista_usuarios"))
        except ValidationError as error:
            flash(str(error), "error")
        except IntegrityError:
            db.session.rollback()
            flash("El usuario o el correo ya están registrados.", "error")
    return render_template("auth/registrar_usuario.html")


@auth.route("/usuarios")
@admin_required
def lista_usuarios():
    return render_template("auth/lista_usuarios.html", usuarios=Usuario.obtener_todos())


@auth.route("/usuarios/<int:id>/editar", methods=["GET", "POST"])
@admin_required
def editar_usuario(id):
    user = db.get_or_404(Usuario, id)
    if request.method == "POST":
        try:
            data = user_payload(request.form, include_password=False, include_status=True)
            if user.id == current_user.id and data["status"] != "activo":
                raise ValidationError("No puedes desactivar tu propia cuenta.")
            if user.rol_clinico == "admin" and data["rol"] != "admin" and Usuario.active_admin_count() <= 1:
                raise ValidationError("Debe existir al menos un administrador activo.")
            data["rol"] = Usuario.role_for_storage(data["rol"])
            for key, value in data.items():
                setattr(
                    user,
                    key,
                    value or None
                    if key
                    in {
                        "apellido_materno",
                        "cedula_profesional",
                        "perfil_profesional",
                        "nombre_establecimiento",
                        "domicilio_profesional",
                    }
                    else value,
                )
            AuditLog.record(
                "usuario.update",
                entity_type="usuario",
                entity_id=user.id,
                metadata={
                    "rol": user.rol,
                    "status": user.status,
                    "perfil_profesional": user.perfil_profesional,
                },
            )
            db.session.commit()
            flash("Usuario actualizado exitosamente.", "success")
            return redirect(url_for("auth.lista_usuarios"))
        except ValidationError as error:
            flash(str(error), "error")
        except IntegrityError:
            db.session.rollback()
            flash("El correo ya está registrado por otro usuario.", "error")
    return render_template("auth/editar_usuario.html", usuario=user)


@auth.route("/usuarios/<int:id>/restablecer-contrasena", methods=["GET", "POST"])
@admin_required
def restablecer_contrasena(id):
    user = db.get_or_404(Usuario, id)
    if user.id == current_user.id:
        flash("Para tu propia cuenta utiliza Cambiar contraseña.", "warning")
        return redirect(url_for("auth.cambiar_contrasena"))
    if request.method == "POST":
        admin_password = str(request.form.get("admin_password", ""))[:128]
        if not current_user.check_password(admin_password):
            attempts = min(int(session.get("password_reset_attempts", 0)) + 1, 5)
            session["password_reset_attempts"] = attempts
            AuditLog.record(
                "usuario.password_reset",
                entity_type="usuario",
                entity_id=user.id,
                outcome="denied",
                description="Restablecimiento rechazado por reautenticación",
            )
            db.session.commit()
            logger.warning("Restablecimiento rechazado; actor_id=%s objetivo_id=%s", current_user.id, user.id)
            flash("No fue posible confirmar tu identidad.", "error")
            return render_template("auth/restablecer_contrasena.html", usuario=user), 422
        if int(session.get("password_reset_attempts", 0)) >= 5:
            AuditLog.record(
                "usuario.password_reset",
                entity_type="usuario",
                entity_id=user.id,
                outcome="denied",
                description="Restablecimiento bloqueado temporalmente en la sesión",
            )
            db.session.commit()
            flash("Se alcanzó el límite de confirmaciones fallidas. Cierra sesión y vuelve a autenticarte.", "warning")
            return render_template("auth/restablecer_contrasena.html", usuario=user), 429
        temporary_password = reset_user_password(user)
        AuditLog.record(
            "usuario.password_reset",
            entity_type="usuario",
            entity_id=user.id,
            metadata={"sesiones_invalidadas": True, "cambio_obligatorio": True},
        )
        db.session.commit()
        session.pop("password_reset_attempts", None)
        logger.warning("Contraseña restablecida por administrador; actor_id=%s objetivo_id=%s", current_user.id, user.id)
        return render_template(
            "auth/contrasena_temporal.html", usuario=user, temporary_password=temporary_password
        )
    return render_template("auth/restablecer_contrasena.html", usuario=user)


@auth.route("/usuarios/<int:id>/cambiar-estatus", methods=["POST"])
@admin_required
def cambiar_estatus_usuario(id):
    user = db.session.get(Usuario, id)
    if not user:
        return jsonify({"success": False, "error": "Usuario no encontrado"}), 404
    if user.id == current_user.id:
        return jsonify({"success": False, "error": "No puedes desactivar tu propia cuenta"}), 400
    if user.rol_clinico == "admin" and user.status == "activo" and Usuario.active_admin_count() <= 1:
        return jsonify({"success": False, "error": "Debe existir al menos un administrador activo"}), 400
    user.status = "inactivo" if user.status == "activo" else "activo"
    AuditLog.record("usuario.status", entity_type="usuario", entity_id=user.id, metadata={"status": user.status})
    db.session.commit()
    return jsonify(
        {
            "success": True,
            "nuevo_estado": user.status,
            "usuarios_activos": Usuario.query.filter_by(status="activo").count(),
            "total_usuarios": Usuario.query.count(),
        }
    )


@auth.route("/auditoria")
@admin_required
def auditoria():
    from app.models.bitacora import AuditLog as AuditEntry

    action = str(request.args.get("accion", "")).strip()[:80]
    module = str(request.args.get("modulo", "")).strip()[:50]
    outcome = str(request.args.get("resultado", "")).strip()[:20]
    query = AuditEntry.query
    if action:
        query = query.filter(AuditEntry.action.contains(action.upper()))
    if module:
        query = query.filter(AuditEntry.module == module.lower())
    if outcome in {"success", "failure", "denied"}:
        query = query.filter(AuditEntry.outcome == outcome)
    events = query.order_by(AuditEntry.created_at.desc()).limit(500).all()
    return render_template("auth/auditoria.html", eventos=events, accion=action, modulo=module, resultado=outcome)
