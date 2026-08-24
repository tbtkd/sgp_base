from datetime import datetime, time

from sqlalchemy import and_, or_, text
from sqlalchemy.orm import joinedload

from app import db_orm as db


class Cita(db.Model):
    __tablename__ = "citas"
    __table_args__ = (
        db.CheckConstraint("estatus IN ('Programada','Atendida','No Asistió','Cancelada')", name="ck_citas_estatus"),
    )

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False, index=True)
    fecha = db.Column(db.Date, nullable=False, index=True)
    hora = db.Column(db.Time, nullable=False)
    motivo = db.Column(db.String(500), nullable=True)
    estado = db.Column(db.String(20), nullable=False, default="pendiente", server_default=text("'pendiente'"))
    estatus = db.Column(db.String(30), nullable=False, default="Programada", server_default=text("'Programada'"))
    motivo_cancelacion = db.Column(db.String(500), nullable=True)

    paciente = db.relationship("Paciente", backref=db.backref("citas", cascade="all, delete-orphan", lazy=True))

    HORARIOS_ATENCION = tuple(
        time(hour, minute)
        for hour in range(9, 20)
        for minute in (0, 30)
        if not (hour == 19 and minute == 30)
    )

    @staticmethod
    def obtener_siguiente_cita(paciente_id):
        today = datetime.now().date()
        return (
            Cita.query.filter(Cita.paciente_id == paciente_id, Cita.fecha >= today, Cita.estatus == "Programada")
            .order_by(Cita.fecha, Cita.hora)
            .first()
        )

    @staticmethod
    def obtener_cita_pendiente(paciente_id):
        return (
            Cita.query.filter_by(paciente_id=paciente_id, estatus="Programada").order_by(Cita.fecha, Cita.hora).first()
        )

    @staticmethod
    def obtener_citas_del_dia(fecha=None):
        target = fecha or datetime.now().date()
        return Cita.query.options(joinedload(Cita.paciente)).filter_by(fecha=target).order_by(Cita.hora).all()

    @staticmethod
    def obtener_proximas(limite=5, momento=None):
        current = momento or datetime.now()
        return (
            Cita.query.options(joinedload(Cita.paciente))
            .filter(
                Cita.estatus == "Programada",
                or_(Cita.fecha > current.date(), and_(Cita.fecha == current.date(), Cita.hora >= current.time())),
            )
            .order_by(Cita.fecha.asc(), Cita.hora.asc())
            .limit(max(1, min(int(limite), 20)))
            .all()
        )

    @staticmethod
    def es_horario_disponible(fecha, hora, excluir_cita_id=None):
        query = Cita.query.filter_by(fecha=fecha, hora=hora, estatus="Programada")
        if excluir_cita_id:
            query = query.filter(Cita.id != excluir_cita_id)
        return query.first() is None

    @staticmethod
    def obtener_disponibilidad_dia(fecha, momento=None, excluir_cita_id=None):
        """Devuelve todos los bloques de atención con un estado explícito."""
        current = momento or datetime.now()
        query = Cita.query.with_entities(Cita.hora).filter_by(fecha=fecha, estatus="Programada")
        if excluir_cita_id:
            query = query.filter(Cita.id != excluir_cita_id)
        occupied = {row.hora for row in query.all()}
        availability = []
        for slot in Cita.HORARIOS_ATENCION:
            elapsed = datetime.combine(fecha, slot) <= current
            is_occupied = slot in occupied
            state = "transcurrido" if elapsed else "ocupado" if is_occupied else "disponible"
            availability.append(
                {
                    "hora": slot.strftime("%H:%M"),
                    "disponible": state == "disponible",
                    "estado": state,
                }
            )
        return availability
