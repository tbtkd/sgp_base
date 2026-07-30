from app import db_orm as db
from datetime import datetime

class BitacoraContacto(db.Model):
    __tablename__ = 'bitacora_contactos'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    mensaje = db.Column(db.Text, nullable=False)
    fecha_envio = db.Column(db.DateTime, default=datetime.utcnow)
    
    usuario = db.relationship('Usuario', backref=db.backref('bitacoras_enviadas', lazy=True))
    paciente = db.relationship('Paciente', backref=db.backref('bitacoras', cascade="all, delete-orphan", lazy=True))

    @staticmethod
    def registrar(paciente_id, usuario_id, mensaje):
        try:
            nueva = BitacoraContacto(
                paciente_id=paciente_id,
                usuario_id=usuario_id,
                mensaje=mensaje
            )
            db.session.add(nueva)
            db.session.commit()
            return True, "Bitácora registrada con éxito."
        except Exception as e:
            db.session.rollback()
            return False, str(e)
