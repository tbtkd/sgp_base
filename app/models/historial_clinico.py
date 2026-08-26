from app import db_orm as db


class HistorialClinico(db.Model):
    __tablename__ = "historial_clinico"

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(
        db.Integer, db.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    enfermedades_previas = db.Column(db.Text, nullable=True)
    cirugias = db.Column(db.Text, nullable=True)
    antecedentes_familiares = db.Column(db.Text, nullable=True)
    antecedente_diabetes = db.Column(db.Boolean, nullable=True, default=False)
    antecedente_hipertension = db.Column(db.Boolean, nullable=True, default=False)
    antecedente_cardiopatias = db.Column(db.Boolean, nullable=True, default=False)
    antecedente_cancer = db.Column(db.Boolean, nullable=True, default=False)
    antecedente_asma_epoc = db.Column(db.Boolean, nullable=True, default=False)
    antecedente_enfermedad_renal = db.Column(db.Boolean, nullable=True, default=False)
    antecedente_enfermedad_hepatica = db.Column(db.Boolean, nullable=True, default=False)
    antecedente_tiroides = db.Column(db.Boolean, nullable=True, default=False)
    antecedente_neurologicos = db.Column(db.Boolean, nullable=True, default=False)
    antecedente_psiquiatricos = db.Column(db.Boolean, nullable=True, default=False)
    antecedente_autoinmunes = db.Column(db.Boolean, nullable=True, default=False)
    antecedente_dislipidemia = db.Column(db.Boolean, nullable=True, default=False)
    antecedente_obesidad = db.Column(db.Boolean, nullable=True, default=False)

    alergias_medicamentosas = db.Column(db.Text, nullable=True)
    alergias_alimentarias = db.Column(db.Text, nullable=True)
    medicamentos_actuales = db.Column(db.Text, nullable=True)
    tratamientos_actuales = db.Column(db.Text, nullable=True)

    actividad_fisica = db.Column(db.String(300), nullable=True)
    motivo_consulta_habitual = db.Column(db.Text, nullable=True)
    notas_generales = db.Column(db.Text, nullable=True)

    paciente = db.relationship(
        "Paciente", backref=db.backref("historial_clinico", uselist=False, cascade="all, delete-orphan")
    )

    @property
    def antecedentes_frecuentes_etiquetas(self):
        labels = (
            ("antecedente_diabetes", "Diabetes"),
            ("antecedente_hipertension", "Hipertensión"),
            ("antecedente_cardiopatias", "Enfermedad del corazón"),
            ("antecedente_cancer", "Cáncer"),
            ("antecedente_asma_epoc", "Asma o enfermedad pulmonar"),
            ("antecedente_enfermedad_renal", "Enfermedad renal"),
            ("antecedente_enfermedad_hepatica", "Enfermedad hepática"),
            ("antecedente_tiroides", "Trastornos de tiroides"),
            ("antecedente_neurologicos", "Trastornos neurológicos"),
            ("antecedente_psiquiatricos", "Salud mental"),
            ("antecedente_autoinmunes", "Enfermedad autoinmune"),
            ("antecedente_dislipidemia", "Colesterol o triglicéridos altos"),
            ("antecedente_obesidad", "Obesidad"),
        )
        return [label for field, label in labels if getattr(self, field, False)]

    @staticmethod
    def obtener_por_paciente_id(paciente_id):
        return HistorialClinico.query.filter_by(paciente_id=paciente_id).first()
