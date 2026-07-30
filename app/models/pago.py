from app import db_orm as db
from datetime import datetime

class Pago(db.Model):
    __tablename__ = 'pagos'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    fecha_pago = db.Column(db.Date, nullable=False)
    
    paciente = db.relationship('Paciente', backref=db.backref('pagos', lazy=True))

    @staticmethod
    def registrar(paciente_id, fecha_pago):
        try:
            nuevo_pago = Pago(
                paciente_id=paciente_id,
                fecha_pago=datetime.strptime(fecha_pago, '%Y-%m-%d').date()
            )
            db.session.add(nuevo_pago)
            db.session.commit()
            return True, "Pago registrado exitosamente"
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def obtener_ultimo_pago(paciente_id):
        return Pago.query.filter_by(paciente_id=paciente_id).order_by(Pago.fecha_pago.desc()).first()
