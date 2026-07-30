from app import db_orm as db
from datetime import datetime

class Valoracion(db.Model):
    __tablename__ = 'valoracion'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    fecha_cita = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    numero_cita = db.Column(db.Integer, nullable=False)
    
    # Composición Corporal
    peso = db.Column(db.Float)
    estatura = db.Column(db.Float)
    imc = db.Column(db.Float)
    porcentaje_grasa = db.Column(db.Float)
    
    # Signos Vitales
    presion_arterial = db.Column(db.String(20))
    frecuencia_cardiaca = db.Column(db.Integer)
    
    # Perímetros (cm)
    torax = db.Column(db.Float)
    cintura = db.Column(db.Float)
    cadera = db.Column(db.Float)
    brazo = db.Column(db.Float)
    pierna = db.Column(db.Float)
    pantorrilla = db.Column(db.Float)
    
    # Pliegues (mm)
    biceps = db.Column(db.Float)
    triceps = db.Column(db.Float)
    suprailiaco = db.Column(db.Float)
    subescapular = db.Column(db.Float)
    
    notas_clinicas = db.Column(db.Text)
