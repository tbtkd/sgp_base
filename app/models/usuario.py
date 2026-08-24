from datetime import timedelta

from flask_login import UserMixin
from sqlalchemy import text
from werkzeug.security import check_password_hash, generate_password_hash

from app import db_orm as db
from app.core.time import utcnow_naive


class Usuario(db.Model, UserMixin):
    PROFESSIONAL_PROFILE_LABELS = {
        "medico_general": "Medicina general",
        "dentista": "Odontología / Dentista",
        "nutricion": "Nutrición",
    }
    __tablename__ = "usuarios"
    __table_args__ = (
        db.CheckConstraint("rol IN ('admin','medico','recepcion')", name="ck_usuarios_rol"),
        db.CheckConstraint("status IN ('activo','inactivo')", name="ck_usuarios_status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(512), nullable=False)
    nombre = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(254), nullable=False, unique=True, index=True)
    cedula_profesional = db.Column(db.String(30), nullable=True)
    perfil_profesional = db.Column(db.String(30), nullable=True)
    nombre_establecimiento = db.Column(db.String(160), nullable=True)
    domicilio_profesional = db.Column(db.String(300), nullable=True)
    rol = db.Column(db.String(20), nullable=False, default="recepcion", server_default=text("'recepcion'"))
    apellido_paterno = db.Column(db.String(60), nullable=False)
    apellido_materno = db.Column(db.String(60), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="activo", server_default=text("'activo'"))
    failed_login_attempts = db.Column(db.Integer, nullable=False, default=0, server_default=text("0"))
    locked_until = db.Column(db.DateTime, nullable=True)
    last_login_at = db.Column(db.DateTime, nullable=True)
    must_change_password = db.Column(db.Boolean, nullable=False, default=False, server_default=text("0"))
    auth_version = db.Column(db.Integer, nullable=False, default=0, server_default=text("0"))
    password_changed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow_naive, server_default=text("CURRENT_TIMESTAMP"))

    @property
    def nombre_completo(self):
        return " ".join(filter(None, [self.nombre, self.apellido_paterno, self.apellido_materno]))

    @property
    def uses_temporary_email(self):
        return str(self.email or "").lower().endswith("@local.invalid")

    @property
    def rol_clinico(self):
        return {
            "Admin": "admin",
            "Nutricionista": "medico",
            "Asistente": "recepcion",
        }.get(self.rol, self.rol)

    @property
    def perfil_profesional_clinico(self):
        if self.perfil_profesional in self.PROFESSIONAL_PROFILE_LABELS:
            return self.perfil_profesional
        # Las cuentas legadas usaban el rol Nutricionista sin un campo separado.
        return "nutricion" if self.rol == "Nutricionista" else None

    @property
    def perfil_profesional_etiqueta(self):
        return self.PROFESSIONAL_PROFILE_LABELS.get(self.perfil_profesional_clinico, "")

    @property
    def rol_etiqueta(self):
        return {
            "admin": "Administrador",
            "medico": "Profesional clínico",
            "recepcion": "Recepción",
        }.get(self.rol_clinico, "Usuario")

    @property
    def puede_capturar_antropometria(self):
        return self.perfil_profesional_clinico == "nutricion"

    @property
    def puede_prescribir_medicamentos(self):
        return self.perfil_profesional_clinico in {"medico_general", "dentista"}

    @property
    def puede_emitir_receta_ordinaria(self):
        return self.rol_clinico in {"admin", "medico"} and self.puede_prescribir_medicamentos

    @property
    def requisitos_receta_faltantes(self):
        if not self.puede_emitir_receta_ordinaria:
            return ["perfil autorizado (Medicina general u Odontología)"]
        missing = []
        if not self.cedula_profesional:
            missing.append("cédula profesional")
        if not self.domicilio_profesional:
            missing.append("domicilio profesional completo")
        return missing

    @property
    def puede_firmar_receta_ordinaria(self):
        return self.puede_emitir_receta_ordinaria and not self.requisitos_receta_faltantes

    @property
    def etiqueta_prescripcion(self):
        if self.perfil_profesional_clinico == "nutricion":
            return "Indicaciones nutricionales / plan alimentario"
        if self.puede_prescribir_medicamentos:
            return "Indicaciones terapéuticas en la nota clínica"
        return "Indicaciones clínicas"

    @property
    def is_active(self):
        return self.status == "activo"

    @property
    def is_locked(self):
        return bool(self.locked_until and self.locked_until > utcnow_naive())

    @staticmethod
    def get(user_id):
        try:
            return db.session.get(Usuario, int(user_id))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def find_by_username(value):
        return Usuario.query.filter(db.func.lower(Usuario.username) == str(value or "").strip().lower()).first()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="scrypt")
        self.password_changed_at = utcnow_naive()

    def replace_password(self, password, *, temporary=False):
        """Reemplaza la credencial e invalida todas las sesiones anteriores."""
        self.set_password(password)
        self.must_change_password = bool(temporary)
        self.auth_version = int(self.auth_version or 0) + 1
        self.failed_login_attempts = 0
        self.locked_until = None

    def check_password(self, password):
        try:
            return check_password_hash(self.password_hash, str(password or ""))
        except (ValueError, TypeError):
            return False

    def record_failed_login(self, limit=5, lock_minutes=5):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= limit:
            self.locked_until = utcnow_naive() + timedelta(minutes=lock_minutes)
            self.failed_login_attempts = 0

    def record_successful_login(self):
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login_at = utcnow_naive()

    @staticmethod
    def active_admin_count():
        return Usuario.query.filter(Usuario.rol.in_({"admin", "Admin"}), Usuario.status == "activo").count()

    @staticmethod
    def role_for_storage(role):
        """Conserva compatibilidad con bases antiguas que tenían un CHECK de roles legado."""
        schema = db.session.execute(
            text("SELECT sql FROM sqlite_master WHERE type='table' AND name='usuarios'")
        ).scalar()
        if schema and "'Admin'" in schema and "'admin'" not in schema:
            return {"admin": "Admin", "medico": "Nutricionista", "recepcion": "Asistente"}[role]
        return role

    @staticmethod
    def obtener_todos():
        return Usuario.query.order_by(Usuario.username.asc()).all()

    @staticmethod
    def create(
        username,
        password,
        nombre,
        apellido_paterno,
        apellido_materno,
        email,
        rol,
        cedula_profesional=None,
        perfil_profesional=None,
        nombre_establecimiento=None,
        domicilio_profesional=None,
    ):
        user = Usuario(
            username=username,
            nombre=nombre,
            apellido_paterno=apellido_paterno,
            apellido_materno=apellido_materno or None,
            email=email,
            rol=Usuario.role_for_storage(rol),
            cedula_profesional=cedula_profesional or None,
            perfil_profesional=perfil_profesional or None,
            nombre_establecimiento=nombre_establecimiento or None,
            domicilio_profesional=domicilio_profesional or None,
            status="activo",
        )
        user.set_password(password)
        db.session.add(user)
        return user
