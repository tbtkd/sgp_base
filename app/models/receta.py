import secrets
from datetime import date

from sqlalchemy import text

from app import db_orm as db
from app.core.time import utcnow_naive


class Receta(db.Model):
    """Documento emitido inmutable; las correcciones generan una sustitución trazable."""

    __tablename__ = "recetas"

    id = db.Column(db.Integer, primary_key=True)
    folio = db.Column(db.String(40), nullable=False, unique=True, index=True)
    __table_args__ = (
        db.UniqueConstraint("valoracion_id", "version", name="uq_recetas_valoracion_version"),
        db.UniqueConstraint("receta_sustituida_id", name="uq_recetas_receta_sustituida"),
        db.CheckConstraint("tipo IN ('original','adicional','sustitucion')", name="ck_recetas_tipo"),
        db.CheckConstraint("estado IN ('vigente','sustituida')", name="ck_recetas_estado"),
        db.CheckConstraint("version >= 1", name="ck_recetas_version"),
    )

    valoracion_id = db.Column(
        db.Integer,
        db.ForeignKey("valoracion_antropometrica.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    paciente_id = db.Column(db.Integer, db.ForeignKey("pacientes.id", ondelete="RESTRICT"), nullable=False, index=True)
    profesional_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)
    fecha_emision = db.Column(db.Date, nullable=False, default=date.today, server_default=text("CURRENT_DATE"), index=True)
    created_at = db.Column(
        db.DateTime, nullable=False, default=utcnow_naive, server_default=text("CURRENT_TIMESTAMP")
    )
    tipo = db.Column(db.String(20), nullable=False, default="original", server_default=text("'original'"))
    version = db.Column(db.Integer, nullable=False, default=1, server_default=text("1"))
    estado = db.Column(db.String(20), nullable=False, default="vigente", server_default=text("'vigente'"))
    receta_sustituida_id = db.Column(
        db.Integer, db.ForeignKey("recetas.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    motivo_cambio = db.Column(db.String(500), nullable=True)
    sustituida_at = db.Column(db.DateTime, nullable=True)
    sustituida_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)

    paciente_nombre = db.Column(db.String(200), nullable=False)
    paciente_fecha_nacimiento = db.Column(db.Date, nullable=False)
    paciente_genero = db.Column(db.String(30), nullable=True)
    alergias_conocidas = db.Column(db.Text, nullable=True)

    profesional_nombre = db.Column(db.String(200), nullable=False)
    profesional_cedula = db.Column(db.String(30), nullable=False)
    profesional_perfil = db.Column(db.String(30), nullable=False)
    domicilio_profesional = db.Column(db.String(300), nullable=False)
    nombre_establecimiento = db.Column(db.String(160), nullable=True)
    observaciones = db.Column(db.Text, nullable=True)

    paciente = db.relationship("Paciente", foreign_keys=[paciente_id])
    profesional = db.relationship("Usuario", foreign_keys=[profesional_id])
    sustituida_por = db.relationship("Usuario", foreign_keys=[sustituida_por_id])
    receta_sustituida = db.relationship(
        "Receta",
        remote_side=[id],
        foreign_keys=[receta_sustituida_id],
        backref=db.backref("receta_reemplazo", uselist=False),
    )
    valoracion = db.relationship(
        "ValoracionAntropometrica",
        backref=db.backref("recetas", lazy=True, order_by="Receta.version"),
    )
    medicamentos = db.relationship(
        "RecetaMedicamento",
        back_populates="receta",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RecetaMedicamento.id",
    )

    @staticmethod
    def generar_folio():
        return f"RX-{date.today():%Y%m%d}-{secrets.token_hex(4).upper()}"

    @staticmethod
    def crear(
        valoracion,
        paciente,
        profesional,
        datos,
        alergias_conocidas=None,
        *,
        tipo="original",
        version=1,
        receta_sustituida=None,
        motivo_cambio=None,
    ):
        receta = Receta(
            folio=Receta.generar_folio(),
            valoracion_id=valoracion.id,
            paciente_id=paciente.id,
            profesional_id=profesional.id,
            paciente_nombre=paciente.nombre_completo,
            paciente_fecha_nacimiento=paciente.fecha_nacimiento,
            paciente_genero=paciente.genero,
            alergias_conocidas=alergias_conocidas or None,
            profesional_nombre=profesional.nombre_completo,
            profesional_cedula=profesional.cedula_profesional,
            profesional_perfil=profesional.perfil_profesional_clinico,
            domicilio_profesional=profesional.domicilio_profesional,
            nombre_establecimiento=profesional.nombre_establecimiento or None,
            observaciones=datos.get("observaciones") or None,
            tipo=tipo,
            version=version,
            estado="vigente",
            receta_sustituida=receta_sustituida,
            motivo_cambio=motivo_cambio or None,
        )
        receta.medicamentos = [RecetaMedicamento(**item) for item in datos["medicamentos"]]
        db.session.add(receta)
        return receta

    @staticmethod
    def siguiente_version(valoracion_id):
        current = db.session.query(db.func.max(Receta.version)).filter_by(valoracion_id=valoracion_id).scalar()
        return int(current or 0) + 1

    def marcar_sustituida(self, usuario):
        if self.estado != "vigente":
            raise ValueError("La receta ya no se encuentra vigente.")
        self.estado = "sustituida"
        self.sustituida_at = utcnow_naive()
        self.sustituida_por_id = usuario.id

    @property
    def tipo_etiqueta(self):
        return {
            "original": "Original",
            "adicional": "Adicional",
            "sustitucion": "Sustitución",
        }.get(self.tipo, "Receta")

    @property
    def esta_vigente(self):
        return self.estado == "vigente"

    @property
    def profesional_perfil_etiqueta(self):
        return {
            "medico_general": "Medicina general",
            "dentista": "Odontología / Cirujano dentista",
        }.get(self.profesional_perfil, "Profesional de la salud")

    @property
    def paciente_edad_al_emitir(self):
        born = self.paciente_fecha_nacimiento
        issued = self.fecha_emision
        return issued.year - born.year - ((issued.month, issued.day) < (born.month, born.day))


class RecetaMedicamento(db.Model):
    __tablename__ = "receta_medicamentos"

    id = db.Column(db.Integer, primary_key=True)
    receta_id = db.Column(db.Integer, db.ForeignKey("recetas.id", ondelete="CASCADE"), nullable=False, index=True)
    denominacion_generica = db.Column(db.String(160), nullable=False)
    denominacion_distintiva = db.Column(db.String(160), nullable=True)
    presentacion = db.Column(db.String(160), nullable=False)
    dosis = db.Column(db.String(160), nullable=False)
    via_administracion = db.Column(db.String(100), nullable=False)
    frecuencia = db.Column(db.String(160), nullable=False)
    duracion = db.Column(db.String(160), nullable=False)
    cantidad = db.Column(db.String(100), nullable=True)
    indicaciones = db.Column(db.String(500), nullable=True)

    receta = db.relationship("Receta", back_populates="medicamentos")
