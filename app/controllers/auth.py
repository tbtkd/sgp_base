import logging
import sqlite3
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin, urlparse

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask_login import current_user, login_user, logout_user
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app import db_orm as db
from app.core.audit import AuditLog
from app.core.auth import admin_required, login_required
from app.core.backup_crypto import (
    BackupSecurityError,
    backup_key_status,
    load_or_create_backup_key,
    recovery_key_document,
)
from app.core.password_recovery import reset_user_password
from app.core.security import login_blocked, register_login_failure, reset_login_failures
from app.core.validators import ValidationError, password_change_payload, user_payload
from app.db import (
    get_backup_directory,
    get_database_path,
    protect_legacy_backups,
    prune_backups,
    resolve_internal_backup,
    respaldar_db,
    restore_sqlite_database,
    verify_backup,
)
from app.models.usuario import Usuario

logger = logging.getLogger(__name__)
auth = Blueprint("auth", __name__)
DUMMY_HASH = generate_password_hash("dummy-password-never-used", method="scrypt")


def _runtime_database_path():
    configured = current_app.config.get("BACKUP_DATABASE_PATH")
    if configured:
        return Path(configured).resolve()
    uri = str(current_app.config.get("SQLALCHEMY_DATABASE_URI", ""))
    if uri.startswith("sqlite:////"):
        return Path("/" + uri.removeprefix("sqlite:////")).resolve()
    return get_database_path()


def _backup_directory():
    configured = current_app.config.get("BACKUP_DIRECTORY")
    return Path(configured).resolve() if configured else get_backup_directory(_runtime_database_path())


def _requested_backup(filename):
    try:
        return resolve_internal_backup(filename, backup_directory=_backup_directory())
    except (ValueError, FileNotFoundError):
        abort(404)


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
                    flash("El correo registrado en tu cuenta necesita actualizarse. Hazlo desde Usuarios.", "warning")
                else:
                    flash("El correo registrado en tu cuenta necesita actualizarse. Solicita el cambio a Administración.", "warning")
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
    users = Usuario.obtener_todos()
    active = sum(1 for user in users if user.status == "activo")
    return render_template(
        "auth/lista_usuarios.html",
        usuarios=users,
        total_usuarios=len(users),
        usuarios_activos=active,
        usuarios_inactivos=len(users) - active,
    )


@auth.route("/usuarios/<int:id>/editar", methods=["GET", "POST"])
@admin_required
def editar_usuario(id):
    user = db.get_or_404(Usuario, id)
    if request.method == "POST":
        try:
            data = user_payload(request.form, include_password=False, include_status=True)
            previous_role = user.rol_clinico
            previous_status = user.status
            if user.id == current_user.id and data["rol"] != previous_role:
                raise ValidationError(
                    "No puedes cambiar tu propio rol de Administración. Para evitar perder el acceso, "
                    "el cambio debe hacerlo otra cuenta de Administración."
                )
            if user.id == current_user.id and data["status"] != "activo":
                raise ValidationError("No puedes desactivar tu propia cuenta.")
            removes_active_admin = (
                previous_role == "admin"
                and previous_status == "activo"
                and (data["rol"] != "admin" or data["status"] != "activo")
            )
            if removes_active_admin and Usuario.active_admin_count() <= 1:
                raise ValidationError(
                    "No puedes quitar la última cuenta de Administración activa. "
                    "Crea otra cuenta de Administración antes de continuar."
                )
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
            access_changed = user.rol_clinico != previous_role or user.status != previous_status
            if access_changed:
                user.auth_version = int(user.auth_version or 0) + 1
            AuditLog.record(
                "usuario.update",
                entity_type="usuario",
                entity_id=user.id,
                metadata={
                    "rol": user.rol,
                    "status": user.status,
                    "perfil_profesional": user.perfil_profesional,
                    "acceso_cambiado": access_changed,
                    "sesiones_invalidadas": access_changed,
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
            flash("Ingresaste una contraseña incorrecta varias veces. Cierra sesión, vuelve a entrar e inténtalo de nuevo.", "warning")
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
        return jsonify(
            {"success": False, "error": "Tu cuenta no se puede desactivar mientras la estás utilizando."}
        ), 400
    if user.rol_clinico == "admin" and user.status == "activo" and Usuario.active_admin_count() <= 1:
        return jsonify(
            {
                "success": False,
                "error": "Esta es la única cuenta de Administración activa. Crea otra antes de inhabilitarla.",
            }
        ), 400
    user.status = "inactivo" if user.status == "activo" else "activo"
    user.auth_version = int(user.auth_version or 0) + 1
    AuditLog.record(
        "usuario.status",
        entity_type="usuario",
        entity_id=user.id,
        metadata={"status": user.status, "sesiones_invalidadas": True},
    )
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


@auth.route("/administracion/respaldos")
@admin_required
def respaldos():
    directory = _backup_directory()
    directory.mkdir(parents=True, exist_ok=True)
    items = []
    candidates = [*directory.glob("pacientes_backup_*.sgpnbak"), *directory.glob("pacientes_backup_*.db")]
    for path in sorted(candidates, key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            resolved = resolve_internal_backup(path.name, backup_directory=directory)
        except (ValueError, FileNotFoundError):
            continue
        stat = resolved.stat()
        items.append(
            {
                "name": resolved.name,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "encrypted": resolved.suffix == ".sgpnbak",
            }
        )
    try:
        key_status = backup_key_status(
            database_path=_runtime_database_path(),
            key_path=current_app.config.get("BACKUP_KEY_PATH"),
        )
    except BackupSecurityError:
        logger.exception("No fue posible abrir la llave de respaldos")
        key_status = {"fingerprint": "NO DISPONIBLE", "source": "error", "exportable": False}
        flash(
            "No se pudo abrir la llave de recuperación. Conserva las copias actuales y solicita ayuda antes de crear o recuperar información.",
            "error",
        )
    return render_template(
        "auth/respaldos.html",
        respaldos=items,
        legacy_count=sum(not item["encrypted"] for item in items),
        key_status=key_status,
        restore_phrase="RESTAURAR",
        protect_phrase="PROTEGER",
        export_phrase="DESCARGAR",
    )


@auth.route("/administracion/respaldos/crear", methods=["POST"])
@admin_required
def crear_respaldo():
    try:
        path = respaldar_db(
            _runtime_database_path(),
            retention=current_app.config["BACKUP_RETENTION"],
            backup_directory=_backup_directory(),
            key_path=current_app.config.get("BACKUP_KEY_PATH"),
        )
        if not path:
            raise RuntimeError("La base todavía no contiene datos para respaldar.")
        AuditLog.record("backup.create", entity_type="database", metadata={"archivo": path.name})
        db.session.commit()
        flash(f"Copia de seguridad creada correctamente: {path.name}", "success")
    except (OSError, RuntimeError, sqlite3.DatabaseError):
        db.session.rollback()
        logger.exception("No fue posible crear el respaldo manual")
        flash("No se pudo crear la copia de seguridad. Tu información actual no cambió.", "error")
    return redirect(url_for("auth.respaldos"))


@auth.route("/administracion/respaldos/<string:filename>/verificar", methods=["POST"])
@admin_required
def verificar_respaldo(filename):
    path = _requested_backup(filename)
    try:
        verify_backup(
            path,
            database_path=_runtime_database_path(),
            key_path=current_app.config.get("BACKUP_KEY_PATH"),
        )
        AuditLog.record("backup.verify", entity_type="database", metadata={"archivo": path.name})
        db.session.commit()
        flash("La copia de seguridad está lista para usarse.", "success")
        return redirect(url_for("auth.respaldos"))
    except (sqlite3.DatabaseError, BackupSecurityError):
        AuditLog.record("backup.verify", entity_type="database", outcome="failure", metadata={"archivo": path.name})
        db.session.commit()
        flash("Esta copia está dañada o incompleta y no puede usarse.", "error")
        return redirect(url_for("auth.respaldos")), 422


@auth.route("/administracion/respaldos/<string:filename>/descargar")
@admin_required
def descargar_respaldo(filename):
    path = _requested_backup(filename)
    AuditLog.record("backup.export", entity_type="database", metadata={"archivo": path.name})
    db.session.commit()
    mimetype = "application/octet-stream" if path.suffix == ".sgpnbak" else "application/vnd.sqlite3"
    response = send_file(path, as_attachment=True, download_name=path.name, mimetype=mimetype)
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@auth.route("/administracion/respaldos/<string:filename>/restaurar", methods=["POST"])
@admin_required
def restaurar_respaldo(filename):
    path = _requested_backup(filename)
    phrase = str(request.form.get("confirmation_phrase", ""))[:20]
    password = str(request.form.get("admin_password", ""))[:128]
    if phrase != "RESTAURAR" or not current_user.check_password(password):
        AuditLog.record(
            "backup.restore", entity_type="database", outcome="denied",
            metadata={"archivo": path.name, "frase_valida": phrase == "RESTAURAR"},
            description="Restauración rechazada por confirmación inválida",
        )
        db.session.commit()
        flash("No se pudo confirmar. Revisa tu contraseña y escribe RESTAURAR.", "error")
        return redirect(url_for("auth.respaldos")), 422
    try:
        verify_backup(
            path,
            database_path=_runtime_database_path(),
            key_path=current_app.config.get("BACKUP_KEY_PATH"),
        )
    except (sqlite3.DatabaseError, BackupSecurityError):
        AuditLog.record("backup.restore", entity_type="database", outcome="failure", metadata={"archivo": path.name})
        db.session.commit()
        flash("Esta copia está dañada, incompleta o pertenece a otro sistema. Tu información actual no cambió.", "error")
        return redirect(url_for("auth.respaldos")), 422

    actor_id = current_user.id
    destination = _runtime_database_path()
    pre_restore = respaldar_db(
        destination,
        retention=current_app.config["BACKUP_RETENTION"] + 1,
        backup_directory=_backup_directory(),
        key_path=current_app.config.get("BACKUP_KEY_PATH"),
    )
    db.session.remove()
    db.engine.dispose()
    try:
        restore_sqlite_database(path, destination, key_path=current_app.config.get("BACKUP_KEY_PATH"))
    except (OSError, sqlite3.DatabaseError, BackupSecurityError):
        logger.exception("Falló la restauración del respaldo %s", path.name)
        flash("No se pudo recuperar la copia. Tu información actual no cambió.", "error")
        return redirect(url_for("auth.respaldos")), 422
    finally:
        db.engine.dispose()

    try:
        prune_backups(_backup_directory(), retention=current_app.config["BACKUP_RETENTION"])
    except OSError:
        logger.exception("No fue posible aplicar la retención después de restaurar")

    restored_actor = db.session.get(Usuario, actor_id)
    AuditLog.record(
        "backup.restore", entity_type="database", user_id=restored_actor.id if restored_actor else None,
        metadata={"archivo": path.name, "respaldo_previo": pre_restore.name if pre_restore else None},
    )
    db.session.commit()
    session.clear()
    logout_user()
    flash("La información se recuperó correctamente. Inicia sesión de nuevo para continuar.", "success")
    return redirect(url_for("auth.login"))


@auth.route("/administracion/respaldos/proteger-anteriores", methods=["POST"])
@admin_required
def proteger_respaldos_anteriores():
    phrase = str(request.form.get("confirmation_phrase", ""))[:20]
    password = str(request.form.get("admin_password", ""))[:128]
    if phrase != "PROTEGER" or not current_user.check_password(password):
        AuditLog.record(
            "backup.protect_legacy",
            entity_type="database",
            outcome="denied",
            metadata={"frase_valida": phrase == "PROTEGER"},
        )
        db.session.commit()
        flash("No se pudo confirmar. Revisa tu contraseña y escribe PROTEGER.", "error")
        return redirect(url_for("auth.respaldos")), 422
    result = protect_legacy_backups(
        _runtime_database_path(),
        backup_directory=_backup_directory(),
        key_path=current_app.config.get("BACKUP_KEY_PATH"),
    )
    AuditLog.record("backup.protect_legacy", entity_type="database", metadata=result)
    db.session.commit()
    if result["failed"]:
        flash(
            "Algunas copias anteriores no pudieron protegerse. Se conservaron sin cambios para evitar perder información.",
            "warning",
        )
    elif result["protected"]:
        flash(f"Se protegieron {result['protected']} copia(s) anterior(es).", "success")
    else:
        flash("No hay copias anteriores pendientes de proteger.", "info")
    return redirect(url_for("auth.respaldos"))


@auth.route("/administracion/respaldos/llave-recuperacion", methods=["POST"])
@admin_required
def descargar_llave_recuperacion():
    phrase = str(request.form.get("confirmation_phrase", ""))[:20]
    password = str(request.form.get("admin_password", ""))[:128]
    if phrase != "DESCARGAR" or not current_user.check_password(password):
        AuditLog.record(
            "backup.export_key",
            entity_type="security_key",
            outcome="denied",
            metadata={"frase_valida": phrase == "DESCARGAR"},
        )
        db.session.commit()
        flash("No se pudo confirmar. Revisa tu contraseña y escribe DESCARGAR.", "error")
        return redirect(url_for("auth.respaldos")), 422
    try:
        key, source = load_or_create_backup_key(
            database_path=_runtime_database_path(),
            key_path=current_app.config.get("BACKUP_KEY_PATH"),
        )
        if source != "file":
            raise BackupSecurityError("La llave administrada externamente no puede descargarse desde SGPN.")
        status = backup_key_status(
            database_path=_runtime_database_path(),
            key_path=current_app.config.get("BACKUP_KEY_PATH"),
        )
        AuditLog.record(
            "backup.export_key",
            entity_type="security_key",
            metadata={"fingerprint": status["fingerprint"]},
        )
        db.session.commit()
        response = send_file(
            BytesIO(recovery_key_document(key)),
            as_attachment=True,
            download_name=f"SGPN_llave_recuperacion_{status['fingerprint']}.txt",
            mimetype="text/plain",
        )
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["Pragma"] = "no-cache"
        return response
    except BackupSecurityError:
        db.session.rollback()
        logger.exception("No fue posible exportar la llave de recuperación")
        flash("La llave se administra fuera de SGPN y no puede descargarse desde esta pantalla.", "warning")
        return redirect(url_for("auth.respaldos")), 422
