from sqlalchemy import text

from app import db_orm as db


class PlantillaMensaje(db.Model):
    __tablename__ = "plantillas_mensajes"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    esta_activa = db.Column(db.Boolean, nullable=False, default=False, server_default=text("0"))

    @staticmethod
    def obtener_activa():
        return PlantillaMensaje.query.filter_by(esta_activa=True).first()
