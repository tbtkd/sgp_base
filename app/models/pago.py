from decimal import Decimal
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import joinedload

from app import db_orm as db
from app.core.time import utcnow_naive


class Pago(db.Model):
    __tablename__ = "pagos"
    __table_args__ = (
        db.CheckConstraint(
            "estatus IN ('vigente','cancelado','requiere_revision')",
            name="ck_pagos_estatus",
        ),
        db.CheckConstraint("monto_centavos >= 0", name="ck_pagos_monto_centavos"),
        db.CheckConstraint(
            "estatus != 'vigente' OR monto_centavos > 0",
            name="ck_pagos_vigente_monto_positivo",
        ),
        db.CheckConstraint("moneda = 'MXN'", name="ck_pagos_moneda"),
    )

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(
        db.Integer,
        db.ForeignKey("pacientes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    fecha_pago = db.Column(db.Date, nullable=False, index=True)

    # Espejo de compatibilidad para instalaciones anteriores. Los cálculos y
    # reportes utilizan exclusivamente monto_centavos.
    monto = db.Column(db.Float, nullable=True)
    monto_centavos = db.Column(db.Integer, nullable=False)
    moneda = db.Column(db.String(3), nullable=False, default="MXN", server_default=text("'MXN'"))
    concepto = db.Column(db.String(200), nullable=False)
    metodo_pago = db.Column(db.String(30), nullable=False, index=True)
    folio = db.Column(db.String(40), nullable=False, unique=True, index=True)
    operation_key = db.Column(db.String(36), nullable=False, unique=True, index=True)
    usuario_registro_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    cita_id = db.Column(
        db.Integer,
        db.ForeignKey("citas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    estatus = db.Column(
        db.String(30),
        nullable=False,
        default="vigente",
        server_default=text("'vigente'"),
        index=True,
    )
    cancelado_at = db.Column(db.DateTime, nullable=True)
    cancelado_por_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    motivo_cancelacion = db.Column(db.String(500), nullable=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utcnow_naive,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    paciente = db.relationship("Paciente", backref=db.backref("pagos", lazy=True))
    cita = db.relationship("Cita", backref=db.backref("pagos", lazy=True))
    usuario_registro = db.relationship(
        "Usuario",
        foreign_keys=[usuario_registro_id],
        backref=db.backref("pagos_registrados", lazy=True),
    )
    usuario_cancelacion = db.relationship(
        "Usuario",
        foreign_keys=[cancelado_por_id],
        backref=db.backref("pagos_cancelados", lazy=True),
    )

    @property
    def monto_decimal(self):
        return Decimal(int(self.monto_centavos or 0)) / Decimal(100)

    @property
    def estatus_etiqueta(self):
        return {
            "vigente": "Vigente",
            "cancelado": "Cancelado",
            "requiere_revision": "Requiere revisión",
        }.get(self.estatus, "Desconocido")

    @staticmethod
    def generar_folio(fecha_pago):
        return f"PAG-{fecha_pago.strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"

    @staticmethod
    def crear(paciente_id, data, *, usuario_id, cita_id=None):
        cents = int(data["monto_centavos"])
        payment = Pago(
            paciente_id=paciente_id,
            fecha_pago=data["fecha_pago"],
            monto=float(Decimal(cents) / Decimal(100)),
            monto_centavos=cents,
            moneda="MXN",
            concepto=data["concepto"],
            metodo_pago=data["metodo_pago"],
            folio=Pago.generar_folio(data["fecha_pago"]),
            operation_key=data["operation_key"],
            usuario_registro_id=usuario_id,
            cita_id=cita_id,
            estatus="vigente",
        )
        db.session.add(payment)
        return payment

    def cancelar(self, *, usuario_id, motivo):
        if self.estatus == "cancelado":
            raise ValueError("El pago ya se encuentra cancelado.")
        previous_status = self.estatus
        self.estatus = "cancelado"
        self.cancelado_at = utcnow_naive()
        self.cancelado_por_id = usuario_id
        self.motivo_cancelacion = motivo
        return previous_status

    @staticmethod
    def obtener_ultimo_pago(paciente_id):
        return (
            Pago.query.filter_by(paciente_id=paciente_id, estatus="vigente")
            .order_by(Pago.fecha_pago.desc(), Pago.created_at.desc(), Pago.id.desc())
            .first()
        )

    @staticmethod
    def obtener_historial_paciente(paciente_id, limite=50):
        return (
            Pago.query.options(
                joinedload(Pago.usuario_registro),
                joinedload(Pago.usuario_cancelacion),
                joinedload(Pago.cita),
            )
            .filter(Pago.paciente_id == paciente_id)
            .order_by(Pago.fecha_pago.desc(), Pago.created_at.desc(), Pago.id.desc())
            .limit(min(max(int(limite), 1), 100))
            .all()
        )
