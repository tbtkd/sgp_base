from threading import Lock

from sqlalchemy import text

from app import db_orm as db
from app.core.time import utcnow_naive

_ADDENDUM_SEQUENCE_LOCK = Lock()


class NotaCierreClinico(db.Model):
    __tablename__ = "nota_cierres_clinicos"

    id = db.Column(db.Integer, primary_key=True)
    valoracion_id = db.Column(
        db.Integer,
        db.ForeignKey("valoracion_antropometrica.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )
    cerrado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    responsable_nombre = db.Column(db.String(200), nullable=False)
    responsable_perfil = db.Column(db.String(100), nullable=True)
    operation_key = db.Column(db.String(36), nullable=False, unique=True, index=True)
    cerrado_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utcnow_naive,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    valoracion = db.relationship("ValoracionAntropometrica", back_populates="cierre_nota")
    responsable = db.relationship("Usuario", foreign_keys=[cerrado_por_id])
    aclaraciones = db.relationship(
        "AclaracionNotaClinica",
        back_populates="cierre",
        order_by="AclaracionNotaClinica.numero.asc()",
        passive_deletes=True,
    )


class AclaracionNotaClinica(db.Model):
    __tablename__ = "aclaraciones_notas_clinicas"
    __table_args__ = (
        db.UniqueConstraint("cierre_id", "numero", name="uq_aclaracion_cierre_numero"),
        db.CheckConstraint("numero >= 1", name="ck_aclaracion_numero_positivo"),
    )

    id = db.Column(db.Integer, primary_key=True)
    cierre_id = db.Column(
        db.Integer,
        db.ForeignKey("nota_cierres_clinicos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    numero = db.Column(db.Integer, nullable=False)
    autor_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    autor_nombre = db.Column(db.String(200), nullable=False)
    autor_perfil = db.Column(db.String(100), nullable=True)
    motivo = db.Column(db.String(500), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    operation_key = db.Column(db.String(36), nullable=False, unique=True, index=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utcnow_naive,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    cierre = db.relationship("NotaCierreClinico", back_populates="aclaraciones")
    autor = db.relationship("Usuario", foreign_keys=[autor_id])

    @staticmethod
    def bloqueo_numeracion():
        return _ADDENDUM_SEQUENCE_LOCK

    @staticmethod
    def siguiente_numero(cierre_id):
        current = (
            db.session.query(db.func.max(AclaracionNotaClinica.numero))
            .filter(AclaracionNotaClinica.cierre_id == cierre_id)
            .scalar()
        )
        return int(current or 0) + 1
