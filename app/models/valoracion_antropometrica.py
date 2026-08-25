from datetime import date, timedelta
from threading import Lock

from sqlalchemy import asc, desc, func, text
from sqlalchemy.orm import joinedload

from app import db_orm as db
from app.core.time import utcnow_naive

_DAILY_CONSULTATION_SEQUENCE_LOCK = Lock()


class ValoracionAntropometrica(db.Model):
    __tablename__ = "valoracion_antropometrica"
    __table_args__ = (
        db.UniqueConstraint("fecha", "numero_cita", name="uq_valoracion_fecha_numero_cita"),
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

    @staticmethod
    def bloqueo_numeracion_diaria():
        """Serializa la asignación del consecutivo en la instancia local."""
        return _DAILY_CONSULTATION_SEQUENCE_LOCK

    @staticmethod
    def siguiente_numero_diario(fecha_consulta):
        """Obtiene el siguiente turno global de la fecha indicada."""
        current = (
            db.session.query(db.func.max(ValoracionAntropometrica.numero_cita))
            .filter(ValoracionAntropometrica.fecha == fecha_consulta)
            .scalar()
        )
        return int(current or 0) + 1

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
            .order_by(ValoracionAntropometrica.fecha.desc(), ValoracionAntropometrica.numero_cita.desc())
            .all()
        )

    @staticmethod
    def obtener_todas():
        return (
            ValoracionAntropometrica.query.order_by(
                ValoracionAntropometrica.fecha.desc(), ValoracionAntropometrica.numero_cita.desc()
            )
            .limit(1000)
            .all()
        )

    @staticmethod
    def buscar_ultimas_por_paciente(busqueda="", orden="fecha_desc", pagina=1, por_pagina=25):
        """Devuelve una sola consulta, la más reciente, por cada paciente.

        La selección se resuelve en SQLite de forma determinista por fecha,
        turno diario e ID. El filtrado y la paginación también se ejecutan en
        servidor para no exponer ni cargar el historial completo en el cliente.
        """
        from app.core.text import search_key
        from app.models.paciente import Paciente

        ranked = (
            db.session.query(
                ValoracionAntropometrica.id.label("valoracion_id"),
                func.row_number()
                .over(
                    partition_by=ValoracionAntropometrica.paciente_id,
                    order_by=(
                        ValoracionAntropometrica.fecha.desc(),
                        ValoracionAntropometrica.numero_cita.desc(),
                        ValoracionAntropometrica.id.desc(),
                    ),
                )
                .label("posicion"),
            )
            .subquery()
        )
        query = (
            ValoracionAntropometrica.query.options(joinedload(ValoracionAntropometrica.paciente))
            .join(ranked, ranked.c.valoracion_id == ValoracionAntropometrica.id)
            .join(ValoracionAntropometrica.paciente)
            .filter(ranked.c.posicion == 1)
        )

        full_name = func.sgpn_search_key(
            func.trim(
                Paciente.nombre
                + " "
                + Paciente.apellido_paterno
                + " "
                + func.coalesce(Paciente.apellido_materno, "")
            )
        )
        for term in search_key(busqueda).split():
            query = query.filter(full_name.contains(term))

        descending = orden != "fecha_asc"
        direction = desc if descending else asc
        query = query.order_by(
            direction(ValoracionAntropometrica.fecha),
            direction(ValoracionAntropometrica.numero_cita),
            direction(ValoracionAntropometrica.id),
        )
        total = query.count()
        safe_page = max(int(pagina), 1)
        safe_size = min(max(int(por_pagina), 1), 100)
        items = query.offset((safe_page - 1) * safe_size).limit(safe_size).all()
        return items, total

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
