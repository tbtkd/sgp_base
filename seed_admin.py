import sys
from app import db_orm
from app.models.usuario import Usuario
from werkzeug.security import generate_password_hash

def seed_admin():
    """
    Verifica si hay un usuario administrador.
    Si no existe, crea el usuario 'sadmin' por defecto.
    """
    try:
        # Verificar si ya existe el usuario 'sadmin' o 'admin@sistema.local'
        admin_existente = Usuario.query.filter(
            (Usuario.email == 'admin@sistema.local') | (Usuario.username == 'sadmin')
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
        print("[ÉXITO] Usuario Administrador por defecto verificado/creado correctamente.")
        print("        Email / Usuario: sadmin / admin@sistema.local")
        print("        Password:        Admin123*")
        print("        Rol:             Admin")
    except Exception as e:
        db_orm.session.rollback()
        print(f"[ERROR] Ocurrió un error al crear el usuario administrador: {e}")
        sys.exit(1)
            
        db_orm.session.rollback()
        print(f"[ERROR] Error durante la inicialización de usuarios por defecto: {e}")
