import os
import sys
from app import create_app, db_orm
from app.models.usuario import Usuario
from werkzeug.security import generate_password_hash

def seed_admin():
    app = create_app()
    with app.app_context():
        try:
            # Asegurar que las tablas existan
            db_orm.create_all()

            # Verificar si ya existe un usuario con username 'admin' o email 'admin@sistema.local'
            existente = Usuario.query.filter((Usuario.username == "admin") | (Usuario.email == "admin@sistema.local")).first()
            if existente:
                print("[ADVERTENCIA] El usuario administrador 'admin' ya existe en la base de datos.")
                print("              No fue necesario volver a crearlo.")
                return

            admin_user = Usuario(
                username="admin",
                email="admin@sistema.local",
                nombre="Administrador Sistema",
                apellido_paterno="",
                apellido_materno="",
                password_hash=generate_password_hash("Admin123*"),
                rol="Admin",
                status="activo"
            )
            db_orm.session.add(admin_user)
            db_orm.session.commit()
            print("[INFO] ¡Usuario Administrador por defecto creado exitosamente mediante seed_admin.py!")
            print("       Email / Usuario: admin")
            print("       Password:        Admin123*")
            print("       Rol:             Admin")
        except Exception as e:
            db_orm.session.rollback()
            print(f"[ERROR] Ocurrió un error al crear el usuario administrador: {e}")
            sys.exit(1)

if __name__ == '__main__':
    print("========================================================")
    print("        SCRIPT DE CREACION DE ADMIN POR DEFECTO         ")
    print("========================================================")
    seed_admin()
