from app import db_orm

class PlantillaMensaje(db_orm.Model):
    __tablename__ = 'plantillas_mensajes'

    id = db_orm.Column(db_orm.Integer, primary_key=True)
    titulo = db_orm.Column(db_orm.String(100), nullable=False)
    contenido = db_orm.Column(db_orm.Text, nullable=False)
    esta_activa = db_orm.Column(db_orm.Boolean, default=False)

    @staticmethod
    def obtener_activa():
        return PlantillaMensaje.query.filter_by(esta_activa=True).first()
