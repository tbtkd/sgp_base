from flask_login import UserMixin
from datetime import datetime
from app import db_orm

class Usuario(db_orm.Model, UserMixin):
    __tablename__ = 'usuarios'
    
    id = db_orm.Column(db_orm.Integer, primary_key=True)
    username = db_orm.Column(db_orm.String(50), nullable=False)
    password_hash = db_orm.Column(db_orm.String(256), nullable=False)
    nombre = db_orm.Column(db_orm.String(50), nullable=True)
    email = db_orm.Column(db_orm.String(120), nullable=True)
    cedula_profesional = db_orm.Column(db_orm.String(30), nullable=True)
    rol = db_orm.Column(db_orm.String(20), default='nutriologa')
    apellido_paterno = db_orm.Column(db_orm.String(50), nullable=True)
    apellido_materno = db_orm.Column(db_orm.String(50), nullable=True)
    status = db_orm.Column(db_orm.String(20), default='activo')

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}"

    @staticmethod
    def get(user_id):
        return Usuario.query.get(int(user_id))

    @staticmethod
    def find_by_username(username):
        return Usuario.query.filter_by(username=username).first()

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def create(username, password, nombre, apellido_paterno, apellido_materno, email, rol, cedula_profesional=None):
        try:
            from werkzeug.security import generate_password_hash
            nuevo_usuario = Usuario(
                username=username,
                password_hash=generate_password_hash(password),
                nombre=nombre,
                apellido_paterno=apellido_paterno,
                apellido_materno=apellido_materno,
                email=email,
                rol=rol,
                cedula_profesional=cedula_profesional if cedula_profesional else None,
                status='activo'
            )
            db_orm.session.add(nuevo_usuario)
            db_orm.session.commit()
            return True
        except Exception as e:
            db_orm.session.rollback()
            print(f"Error al crear usuario: {e}")
            return False

    @staticmethod
    def obtener_todos():
        return Usuario.query.all()

    @staticmethod
    def actualizar(id, nombre, apellido_paterno, apellido_materno, email, rol, cedula_profesional, status):
        try:
            usuario = Usuario.query.get(id)
            if usuario:
                usuario.nombre = nombre
                usuario.apellido_paterno = apellido_paterno
                usuario.apellido_materno = apellido_materno
                usuario.email = email
                usuario.rol = rol
                usuario.cedula_profesional = cedula_profesional if cedula_profesional else None
                usuario.status = status
                db_orm.session.commit()
                return True
            return False
        except Exception as e:
            db_orm.session.rollback()
            print(f"Error al actualizar usuario: {e}")
            return False

    @staticmethod
    def cambiar_estatus(id):
        try:
            usuario = Usuario.query.get(id)
            if usuario:
                nuevo_estado = 'inactivo' if usuario.status == 'activo' else 'activo'
                usuario.status = nuevo_estado
                db_orm.session.commit()
                return True, nuevo_estado
            return False, 'Usuario no encontrado'
        except Exception as e:
            db_orm.session.rollback()
            return False, str(e)
