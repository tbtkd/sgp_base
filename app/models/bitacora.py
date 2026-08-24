import json
from datetime import timedelta

from flask import g, has_request_context, request
from flask_login import current_user
from sqlalchemy import text

from app import db_orm as db
from app.core.time import utcnow_naive

EVENT_NAMES = {
    "auth.login": "LOGIN",
    "auth.logout": "LOGOUT",
    "system.bootstrap_admin": "CREAR_ADMIN_INICIAL",
    "usuario.create": "CREAR_USUARIO",
    "usuario.update": "ACTUALIZAR_USUARIO",
    "usuario.status": "CAMBIAR_ESTADO_USUARIO",
    "paciente.create": "CREAR_PACIENTE",
    "paciente.update": "ACTUALIZAR_PACIENTE",
    "paciente.status": "CAMBIAR_ESTADO_PACIENTE",
    "historial.create": "CREAR_HISTORIAL",
    "historial.update": "ACTUALIZAR_HISTORIAL",
    "valoracion.create": "CREAR_CONSULTA",
    "valoracion.update": "ACTUALIZAR_CONSULTA",
    "valoracion.delete": "ELIMINAR_CONSULTA",
    "valoracion.import": "IMPORTAR_CONSULTAS",
    "receta.create": "CREAR_RECETA",
    "receta.additional": "CREAR_RECETA_ADICIONAL",
    "receta.replace": "SUSTITUIR_RECETA",
    "usuario.password_change": "CAMBIAR_CONTRASENA",
    "usuario.password_reset": "RESTABLECER_CONTRASENA",
    "usuario.password_reset_offline": "RESTABLECER_CONTRASENA_LOCAL",
    "pago.create": "REGISTRAR_PAGO",
    "cita.create": "CREAR_CITA",
    "cita.update": "ACTUALIZAR_CITA",
    "cita.status": "CAMBIAR_ESTADO_CITA",
}


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(
        db.DateTime, nullable=False, default=utcnow_naive, server_default=text("CURRENT_TIMESTAMP"), index=True
    )
    request_id = db.Column(db.String(36), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True, index=True)
    module = db.Column(db.String(50), nullable=True, index=True)
    action = db.Column(db.String(80), nullable=False, index=True)
    description = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True, index=True)
    entity_type = db.Column(db.String(50), nullable=True)
    entity_id = db.Column(db.Integer, nullable=True)
    outcome = db.Column(db.String(20), nullable=False, default="success", server_default=text("'success'"))
    metadata_json = db.Column(db.Text, nullable=True)

    usuario = db.relationship("Usuario", backref=db.backref("eventos_auditoria", lazy=True))

    @staticmethod
    def record(
        action,
        *,
        entity_type=None,
        entity_id=None,
        outcome="success",
        metadata=None,
        user_id=None,
        module=None,
        description=None,
    ):
        raw_action = str(action)[:80]
        event_action = EVENT_NAMES.get(raw_action, raw_action.replace(".", "_").upper())[:80]
        resolved_module = module or raw_action.split(".", 1)[0]
        entry = AuditLog(
            request_id=getattr(g, "request_id", None) if has_request_context() else None,
            user_id=user_id
            if user_id is not None
            else (current_user.id if getattr(current_user, "is_authenticated", False) else None),
            module=str(resolved_module)[:50],
            action=event_action,
            description=str(description or event_action.replace("_", " ").title())[:500],
            ip_address=(request.remote_addr or "unknown")[:45] if has_request_context() else None,
            entity_type=str(entity_type)[:50] if entity_type else None,
            entity_id=entity_id,
            outcome=outcome if outcome in {"success", "failure", "denied"} else "failure",
            metadata_json=json.dumps(metadata or {}, ensure_ascii=False, separators=(",", ":"))[:2000],
        )
        db.session.add(entry)
        return entry

    @staticmethod
    def purge_older_than(days=365):
        cutoff = utcnow_naive() - timedelta(days=days)
        return AuditLog.query.filter(AuditLog.created_at < cutoff).delete()


class BitacoraContacto(db.Model):
    __tablename__ = "bitacora_contactos"

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False, index=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True, index=True)
    mensaje = db.Column(db.Text, nullable=False)
    fecha_envio = db.Column(
        db.DateTime, nullable=False, default=utcnow_naive, server_default=text("CURRENT_TIMESTAMP"), index=True
    )

    usuario = db.relationship("Usuario", backref=db.backref("bitacoras_enviadas", lazy=True))
    paciente = db.relationship("Paciente", backref=db.backref("bitacoras", cascade="all, delete-orphan", lazy=True))
