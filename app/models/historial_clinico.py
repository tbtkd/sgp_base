from app import db_orm as db

class HistorialClinico(db.Model):
    __tablename__ = 'historial_clinico'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    cirugias = db.Column(db.Text)
    padecimientos = db.Column(db.Text)
    medicamentos = db.Column(db.Text)
    suplementos = db.Column(db.Text)
    enfermedades_previas = db.Column(db.Text)
    enfermedades_actuales = db.Column(db.Text)
    tipo_actividad_fisica = db.Column(db.Text)
    frecuencia_actividad_fisica = db.Column(db.Text)
    tiempo_actividad_fisica = db.Column(db.Text)
    numero_comidas_diarias = db.Column(db.Integer)
    alimentos_normales = db.Column(db.Text)
    alimentos_no_gustados = db.Column(db.Text)
    
    paciente = db.relationship('Paciente', backref=db.backref('historial_clinico', uselist=False, lazy=True))

    @staticmethod
    def obtener_por_paciente_id(paciente_id):
        return HistorialClinico.query.filter_by(paciente_id=paciente_id).first()

    @staticmethod
    def actualizar(paciente_id, datos):
        try:
            historial = HistorialClinico.query.filter_by(paciente_id=paciente_id).first()
            if not historial:
                historial = HistorialClinico(paciente_id=paciente_id)
                db.session.add(historial)
            
            historial.cirugias = datos.get('cirugias')
            historial.padecimientos = datos.get('padecimientos')
            historial.medicamentos = datos.get('medicamentos')
            historial.suplementos = datos.get('suplementos')
            historial.enfermedades_previas = datos.get('enfermedades_previas')
            historial.enfermedades_actuales = datos.get('enfermedades_actuales')
            historial.tipo_actividad_fisica = datos.get('tipo_actividad_fisica')
            historial.frecuencia_actividad_fisica = datos.get('frecuencia_actividad_fisica')
            historial.tiempo_actividad_fisica = datos.get('tiempo_actividad_fisica')
            
            comidas = datos.get('numero_comidas_diarias')
            historial.numero_comidas_diarias = int(comidas) if comidas and str(comidas).isdigit() else None
            
            historial.alimentos_normales = datos.get('alimentos_normales')
            historial.alimentos_no_gustados = datos.get('alimentos_no_gustados')
            
            db.session.commit()
            return True, "Historial clínico actualizado exitosamente."
        except Exception as e:
            db.session.rollback()
            return False, str(e)
