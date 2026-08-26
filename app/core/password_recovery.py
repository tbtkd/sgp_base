import secrets

from app import db_orm as db
from app.core.audit import AuditLog
from app.core.validators import ValidationError, password
from app.models.usuario import Usuario


def generate_temporary_password():
    """Genera una credencial de un solo uso que cumple la política local."""
    return f"Tmp!9a{secrets.token_urlsafe(14)}"


def reset_user_password(user, *, temporary_password=None):
    if temporary_password is not None:
        credential = temporary_password
        password(credential, user=user.username, email=user.email)
    else:
        for _ in range(20):
            credential = generate_temporary_password()
            try:
                password(credential, user=user.username, email=user.email)
                break
            except ValidationError:
                continue
        else:
            raise RuntimeError("No fue posible generar una contraseña temporal segura.")
    user.replace_password(credential, temporary=True)
    return credential


def reset_password_offline(username, recovery_password):
    """Recuperación local para el propietario del equipo cuando no existe otra sesión admin."""
    user = Usuario.find_by_username(username)
    if not user:
        raise ValidationError("No existe una cuenta con ese nombre de usuario.")
    if user.rol_clinico != "admin":
        raise ValidationError("La recuperación local sólo puede restablecer una cuenta administradora.")
    password(recovery_password, user=user.username, email=user.email)
    user.replace_password(recovery_password, temporary=True)
    user.status = "activo"
    AuditLog.record(
        "usuario.password_reset_offline",
        entity_type="usuario",
        entity_id=user.id,
        user_id=user.id,
        metadata={"metodo": "equipo_local", "sesiones_invalidadas": True},
    )
    db.session.commit()
    return user


def recover_admin_offline(username, recovery_password):
    """Recupera Administración sólo cuando no queda otra cuenta admin activa."""
    if Usuario.active_admin_count() > 0:
        raise ValidationError(
            "Todavía existe una cuenta de Administración activa. Usa esa cuenta para realizar el cambio."
        )
    user = Usuario.find_by_username(username)
    if not user:
        raise ValidationError("No existe una cuenta con ese nombre de usuario.")
    password(recovery_password, user=user.username, email=user.email)
    user.rol = Usuario.role_for_storage("admin")
    user.status = "activo"
    user.replace_password(recovery_password, temporary=True)
    AuditLog.record(
        "usuario.admin_recovery_offline",
        entity_type="usuario",
        entity_id=user.id,
        user_id=user.id,
        metadata={"metodo": "equipo_local", "sesiones_invalidadas": True},
    )
    db.session.commit()
    return user
