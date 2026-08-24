from sqlalchemy import text

from app import db_orm as db
from app.core.time import utcnow_naive


class Pago(db.Model):
    __tablename__ = "pagos"

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False, index=True)
    fecha_pago = db.Column(db.Date, nullable=False, index=True)
    monto = db.Column(db.Float, nullable=True)
    concepto = db.Column(db.String(200), nullable=True)
    metodo_pago = db.Column(db.String(30), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow_naive, server_default=text("CURRENT_TIMESTAMP"))

    paciente = db.relationship("Paciente", backref=db.backref("pagos", cascade="all, delete-orphan", lazy=True))

    @staticmethod
    def obtener_ultimo_pago(paciente_id):
        return Pago.query.filter_by(paciente_id=paciente_id).order_by(Pago.fecha_pago.desc()).first()
