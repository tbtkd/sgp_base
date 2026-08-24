"""Inicialización segura del primer administrador del sistema."""

import getpass
import os
import secrets
import sys

from app import create_app
from app import db_orm as db
from app.core.audit import AuditLog
from app.core.validators import ValidationError, email_address, name, password, username
from app.models.usuario import Usuario


def create_initial_admin(*, user_name, raw_password, first_name, last_name, email, maternal_name=""):
    app = create_app(os.environ.get("SGPN_ENV", "default"))
    with app.app_context():
        if Usuario.active_admin_count() > 0:
            return None
        normalized_username = username(user_name)
        normalized_email = email_address(email)
        validated_password = password(raw_password, user=normalized_username, email=normalized_email)
        user = Usuario.create(
            username=normalized_username,
            password=validated_password,
            nombre=name(first_name, "Nombre"),
            apellido_paterno=name(last_name, "Apellido paterno"),
            apellido_materno=name(maternal_name, "Apellido materno", required=False),
            email=normalized_email,
            rol="admin",
        )
        db.session.flush()
        AuditLog.record("system.bootstrap_admin", entity_type="usuario", entity_id=user.id, user_id=user.id)
        db.session.commit()
        return user.id


def _values_from_environment_or_prompt():
    values = {
        "user_name": os.environ.get("SGPN_ADMIN_USERNAME"),
        "first_name": os.environ.get("SGPN_ADMIN_NAME"),
        "last_name": os.environ.get("SGPN_ADMIN_LASTNAME"),
        "maternal_name": os.environ.get("SGPN_ADMIN_MATERNAL", ""),
        "email": os.environ.get("SGPN_ADMIN_EMAIL"),
        "raw_password": os.environ.get("SGPN_ADMIN_PASSWORD"),
    }
    if sys.stdin.isatty():
        values["user_name"] = values["user_name"] or input("Usuario administrador: ")
        values["first_name"] = values["first_name"] or input("Nombre(s): ")
        values["last_name"] = values["last_name"] or input("Apellido paterno: ")
        values["maternal_name"] = values["maternal_name"] or input("Apellido materno (opcional): ")
        values["email"] = values["email"] or input("Correo: ")
        values["raw_password"] = values["raw_password"] or getpass.getpass("Contraseña segura: ")
        if getpass.getpass("Confirmar contraseña: ") != values["raw_password"]:
            raise ValidationError("Las contraseñas no coinciden.")
    else:
        values["user_name"] = values["user_name"] or "administrador"
        values["first_name"] = values["first_name"] or "Administrador"
        values["last_name"] = values["last_name"] or "Sistema"
        values["email"] = values["email"] or "admin@localhost.invalid"
        if not values["raw_password"]:
            values["raw_password"] = f"Aa1!{secrets.token_urlsafe(18)}"
            print(f"Contraseña inicial generada (guárdala ahora): {values['raw_password']}")
    return values


def main():
    try:
        user_id = create_initial_admin(**_values_from_environment_or_prompt())
        if user_id is None:
            print("Ya existe un administrador activo; no se realizaron cambios.")
        else:
            print(f"Administrador inicial creado con ID {user_id}.")
    except ValidationError as error:
        print(f"No fue posible crear el administrador: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
