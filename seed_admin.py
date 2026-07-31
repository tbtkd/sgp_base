import os
import sys
from app import create_app, db_orm
from app.models.usuario import Usuario
from werkzeug.security import generate_password_hash

def seed_admin():
    app = create_app()
    with app.app_context():
        try:
            db_orm.create_all()
            
            # Verificar si ya existe un usuario con email 'admin@sistema.local' o username 'admin'
            admin_existente = Usuario.query.filter(
                (Usuario.email == 'sadmin@sistema.local') | (Usuario.username == 'sadmin')
            ).first()

            if admin_existente:
                print("[ADVERTENCIA] El usuario administrador ('admin@sistema.local' / 'admin') ya existe en la base de datos.")
                print("              No fue necesario volver a crearlo.")
                return

            nuevo_admin = Usuario(
                username="sadmin",
                email="admin@sistema.local",
                nombre="Administrador Sistema",
                apellido_paterno="",
                apellido_materno="",
                password_hash=generate_password_hash("Admin123*"),
                rol="Admin",
                status="activo"
            )
            db_orm.session.add(nuevo_admin)
            db_orm.session.commit()
            print("[EXITO] ¡Usuario Administrador creado correctamente mediante seed_admin.py!")
            print("        Email / Usuario: sadmin / admin@sistema.local")
            print("        Password:        Admin123*")
            print("        Rol:             Admin")
        except Exception as e:
            db_orm.session.rollback()
            print(f"[ERROR] Ocurrió un error al crear el usuario administrador: {e}")
            sys.exit(1)

if __name__ == '__main__':
    print("========================================================")
    print("      SCRIPT DE SEEDING: USUARIO ADMINISTRADOR         ")
    print("========================================================")
    seed_admin()
