from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.orm import joinedload

from app import db_orm as db
from app.core.time import utcnow_naive


class ValoracionAntropometrica(db.Model):
    __tablename__ = "valoracion_antropometrica"
    __table_args__ = (
        db.UniqueConstraint("paciente_id", "numero_cita", "fecha", name="uq_valoracion_paciente_cita_fecha"),
    )

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False, index=True)
    profesional_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)
    profesional_nombre = db.Column(db.String(200), nullable=True)
    profesional_cedula = db.Column(db.String(30), nullable=True)
    profesional_perfil = db.Column(db.String(30), nullable=True)
    numero_cita = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.Date, nullable=False, index=True)
    motivo_consulta = db.Column(db.Text, nullable=True)
    sintomas = db.Column(db.Text, nullable=True)
    impresion_diagnostica = db.Column(db.Text, nullable=True)
    plan_tratamiento = db.Column(db.Text, nullable=True)
    prescripcion = db.Column(db.Text, nullable=True)

    tension_arterial = db.Column(db.String(7), nullable=True)
    frecuencia_cardiaca = db.Column(db.Integer, nullable=True)
    frecuencia_respiratoria = db.Column(db.Integer, nullable=True)
    temperatura = db.Column(db.Float, nullable=True)
    saturacion_oxigeno = db.Column(db.Integer, nullable=True)
    estatura = db.Column(db.Float, nullable=True)
    peso = db.Column(db.Float, nullable=True)
    imc = db.Column(db.Float, nullable=True)

    grasa = db.Column(db.Float, nullable=True)
    cintura = db.Column(db.Float, nullable=True)
    torax = db.Column(db.Float, nullable=True)
    brazo = db.Column(db.Float, nullable=True)
    cadera = db.Column(db.Float, nullable=True)
    pierna = db.Column(db.Float, nullable=True)
    pantorrilla = db.Column(db.Float, nullable=True)
    bicep = db.Column(db.Float, nullable=True)
    tricep = db.Column(db.Float, nullable=True)
    suprailiaco = db.Column(db.Float, nullable=True)
    subescapular = db.Column(db.Float, nullable=True)
    femoral = db.Column(db.Float, nullable=True)
    porcentaje_grasa = db.Column(db.Float, nullable=True)
    ultima_dieta = db.Column(db.String(100), nullable=True)
    seguimiento_15d_enviado = db.Column(db.Boolean, nullable=False, default=False, server_default=text("0"))
    fecha_seguimiento_15d = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=True, default=utcnow_naive)

    paciente = db.relationship(
        "Paciente", backref=db.backref("valoraciones_lista", cascade="all, delete-orphan", lazy=True)
    )
    profesional = db.relationship("Usuario", foreign_keys=[profesional_id])

    @staticmethod
    def crear(paciente_id, datos, profesional=None):
        professional_data = {}
        if profesional is not None:
            professional_data = {
                "profesional_id": profesional.id,
                "profesional_nombre": profesional.nombre_completo,
                "profesional_cedula": profesional.cedula_profesional or None,
                "profesional_perfil": profesional.perfil_profesional_clinico,
            }
        assessment = ValoracionAntropometrica(paciente_id=paciente_id, **professional_data, **datos)
        db.session.add(assessment)
        return assessment

    @property
    def profesional_nombre_mostrado(self):
        return self.profesional_nombre or (self.profesional.nombre_completo if self.profesional else "")

    @property
    def profesional_cedula_mostrada(self):
        if self.profesional_nombre:
            return self.profesional_cedula or ""
        return self.profesional.cedula_profesional if self.profesional else ""

    @property
    def profesional_perfil_mostrado(self):
        if self.profesional_nombre:
            return self.profesional_perfil
        return self.profesional.perfil_profesional_clinico if self.profesional else None

    @property
    def profesional_perfil_etiqueta(self):
        labels = {
            "medico_general": "Medicina general",
            "dentista": "Odontología / Dentista",
            "nutricion": "Nutrición",
        }
        return labels.get(self.profesional_perfil_mostrado, "")

    @property
    def etiqueta_prescripcion(self):
        if self.profesional_perfil_mostrado == "nutricion":
            return "Indicaciones nutricionales / plan alimentario"
        if self.profesional_perfil_mostrado in {"medico_general", "dentista"}:
            return "Indicaciones terapéuticas en la nota clínica"
        return "Indicaciones clínicas"

    @staticmethod
    def obtener_por_id(valoracion_id):
        return db.session.get(ValoracionAntropometrica, valoracion_id)

    @staticmethod
    def obtener_por_paciente(paciente_id):
        return (
            ValoracionAntropometrica.query.filter_by(paciente_id=paciente_id)
            .order_by(ValoracionAntropometrica.fecha.desc())
            .all()
        )

    @staticmethod
    def obtener_todas():
        return ValoracionAntropometrica.query.order_by(ValoracionAntropometrica.fecha.desc()).limit(1000).all()

    @staticmethod
    def contar_mes_vigente():
        start = utcnow_naive().replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()
        return ValoracionAntropometrica.query.filter(ValoracionAntropometrica.fecha >= start).count()

    @staticmethod
    def obtener_recientes(limite=10):
        return (
            ValoracionAntropometrica.query.options(joinedload(ValoracionAntropometrica.paciente))
            .order_by(ValoracionAntropometrica.fecha.desc())
            .limit(min(max(int(limite), 1), 100))
            .all()
        )

    @staticmethod
    def obtener_por_rango(fecha_inicio, fecha_fin):
        return (
            ValoracionAntropometrica.query.filter(ValoracionAntropometrica.fecha.between(fecha_inicio, fecha_fin))
            .order_by(ValoracionAntropometrica.fecha.desc())
            .limit(1000)
            .all()
        )

    @staticmethod
    def obtener_seguimiento_14_15_dias():
        today = date.today()
        start, end = today - timedelta(days=15), today - timedelta(days=14)
        return (
            ValoracionAntropometrica.query.options(joinedload(ValoracionAntropometrica.paciente))
            .filter(
                ValoracionAntropometrica.fecha.between(start, end),
                ValoracionAntropometrica.seguimiento_15d_enviado.is_(False),
            )
            .order_by(ValoracionAntropometrica.fecha)
            .all()
        )

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
