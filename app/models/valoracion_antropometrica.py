from app import db_orm as db
from datetime import datetime, date

class ValoracionAntropometrica(db.Model):
    __tablename__ = 'valoracion_antropometrica'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    numero_cita = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    estatura = db.Column(db.Float, nullable=False)
    peso = db.Column(db.Float, nullable=False)
    imc = db.Column(db.Float, nullable=False)
    grasa = db.Column(db.Float, nullable=False)
    cintura = db.Column(db.Float, nullable=False)
    torax = db.Column(db.Float, nullable=False)
    brazo = db.Column(db.Float, nullable=False)
    cadera = db.Column(db.Float, nullable=False)
    pierna = db.Column(db.Float, nullable=False)
    pantorrilla = db.Column(db.Float, nullable=False)
    tension_arterial = db.Column(db.String(50), nullable=False)
    frecuencia_cardiaca = db.Column(db.Integer, nullable=False)
    bicep = db.Column(db.Float, nullable=False)
    tricep = db.Column(db.Float, nullable=False)
    suprailiaco = db.Column(db.Float, nullable=False)
    subescapular = db.Column(db.Float, nullable=False)
    femoral = db.Column(db.Float)
    porcentaje_grasa = db.Column(db.String(50), nullable=False)
    ultima_dieta = db.Column(db.Text)
    seguimiento_15d_enviado = db.Column(db.Boolean, default=False)
    fecha_seguimiento_15d = db.Column(db.Date, nullable=False, default=lambda: date(1900, 1, 1))
    
    paciente = db.relationship('Paciente', backref=db.backref('valoraciones_lista', cascade="all, delete-orphan", lazy=True))

    @staticmethod
    def crear(paciente_id, datos):
        try:
            fecha_val = datos['fecha']
            if isinstance(fecha_val, str):
                fecha_obj = datetime.strptime(fecha_val, '%Y-%m-%d').date()
            elif isinstance(fecha_val, datetime):
                fecha_obj = fecha_val.date()
            elif isinstance(fecha_val, date):
                fecha_obj = fecha_val
            else:
                fecha_obj = datetime.strptime(str(fecha_val), '%Y-%m-%d').date()

            nueva_valoracion = ValoracionAntropometrica(
                paciente_id=paciente_id,
                numero_cita=datos.get('numero_cita', 1),
                fecha=fecha_obj,
                estatura=datos['estatura'],
                peso=datos['peso'],
                imc=datos['imc'],
                grasa=datos['grasa'],
                cintura=datos['cintura'],
                torax=datos['torax'],
                brazo=datos['brazo'],
                cadera=datos['cadera'],
                pierna=datos['pierna'],
                pantorrilla=datos['pantorrilla'],
                tension_arterial=datos['tension_arterial'],
                frecuencia_cardiaca=datos['frecuencia_cardiaca'],
                bicep=datos['bicep'],
                tricep=datos['tricep'],
                suprailiaco=datos['suprailiaco'],
                subescapular=datos['subescapular'],
                femoral=datos.get('femoral'),
                porcentaje_grasa=datos['porcentaje_grasa'],
                ultima_dieta=datos.get('ultima_dieta')
            )
            db.session.add(nueva_valoracion)
            db.session.commit()
            return True, "Valoración antropométrica registrada correctamente."
        except Exception as e:
            db.session.rollback()
            return False, f"Error al registrar la valoración antropométrica: {str(e)}"

    @staticmethod
    def actualizar(valoracion_id, datos):
        try:
            valoracion = ValoracionAntropometrica.query.get(valoracion_id)
            if not valoracion:
                return False, "Valoración no encontrada."
            
            fecha_val = datos['fecha']
            if isinstance(fecha_val, str):
                valoracion.fecha = datetime.strptime(fecha_val, '%Y-%m-%d').date()
            elif isinstance(fecha_val, datetime):
                valoracion.fecha = fecha_val.date()
            elif isinstance(fecha_val, date):
                valoracion.fecha = fecha_val
            else:
                valoracion.fecha = datetime.strptime(str(fecha_val), '%Y-%m-%d').date()
            valoracion.estatura = datos['estatura']
            valoracion.peso = datos['peso']
            valoracion.imc = datos['imc']
            valoracion.grasa = datos['grasa']
            valoracion.cintura = datos['cintura']
            valoracion.torax = datos['torax']
            valoracion.brazo = datos['brazo']
            valoracion.cadera = datos['cadera']
            valoracion.pierna = datos['pierna']
            valoracion.pantorrilla = datos['pantorrilla']
            valoracion.bicep = datos['bicep']
            valoracion.tricep = datos['tricep']
            valoracion.suprailiaco = datos['suprailiaco']
            valoracion.subescapular = datos['subescapular']
            valoracion.femoral = datos.get('femoral')
            valoracion.porcentaje_grasa = datos['porcentaje_grasa']
            valoracion.ultima_dieta = datos.get('ultima_dieta', '')
            
            db.session.commit()
            return True, "Valoración antropométrica actualizada correctamente."
        except Exception as e:
            db.session.rollback()
            return False, f"Error al actualizar la valoración antropométrica: {str(e)}"

    @staticmethod
    def actualizar_ultima_dieta(paciente_id, ultima_dieta):
        try:
            valoraciones = ValoracionAntropometrica.query.filter_by(paciente_id=paciente_id).order_by(ValoracionAntropometrica.fecha.desc()).all()
            if not valoraciones:
                return False, "No se encontraron valoraciones para este paciente."
            ultima = valoraciones[0]
            ultima.ultima_dieta = ultima_dieta
            db.session.commit()
            return True, "Última dieta actualizada exitosamente."
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def obtener_por_id(valoracion_id):
        return ValoracionAntropometrica.query.get(valoracion_id)

    @staticmethod
    def obtener_por_paciente(paciente_id):
        return ValoracionAntropometrica.query.filter_by(paciente_id=paciente_id).order_by(ValoracionAntropometrica.fecha.desc()).all()

    @staticmethod
    def obtener_todas():
        return ValoracionAntropometrica.query.order_by(ValoracionAntropometrica.fecha.desc()).all()

    @staticmethod
    def contar_mes_vigente():
        inicio_mes = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return ValoracionAntropometrica.query.filter(ValoracionAntropometrica.fecha >= inicio_mes.date()).count()

    @staticmethod
    def obtener_recientes(limite=10):
        try:
            return ValoracionAntropometrica.query.filter(
                ValoracionAntropometrica.fecha.isnot(None),
                ValoracionAntropometrica.fecha != ''
            ).order_by(ValoracionAntropometrica.fecha.desc()).limit(limite).all()
        except Exception as e:
            print(f"Error en obtener_recientes: {e}")
            return []

    @staticmethod
    def obtener_por_rango(fecha_inicio, fecha_fin):
        fi = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        ff = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        return ValoracionAntropometrica.query.filter(ValoracionAntropometrica.fecha >= fi, ValoracionAntropometrica.fecha <= ff).order_by(ValoracionAntropometrica.fecha.desc()).all()

    @staticmethod
    def obtener_seguimiento_14_15_dias():
        from datetime import date, timedelta
        from sqlalchemy.orm import joinedload
        from sqlalchemy import and_, or_
        hoy = date.today()
        # Rango de fechas: fecha_inicio = hoy - 15 días, fecha_fin = hoy - 14 días
        fecha_inicio = hoy - timedelta(days=15)
        fecha_fin = hoy - timedelta(days=14)
        
        try:
            fecha_defecto = date(1900, 1, 1)
            return ValoracionAntropometrica.query.options(joinedload(ValoracionAntropometrica.paciente)).filter(
                and_(
                    ValoracionAntropometrica.fecha.isnot(None),
                    ValoracionAntropometrica.fecha != '',
                    ValoracionAntropometrica.fecha >= fecha_inicio,
                    ValoracionAntropometrica.fecha <= fecha_fin,
                    or_(
                        ValoracionAntropometrica.seguimiento_15d_enviado == False,
                        ValoracionAntropometrica.fecha_seguimiento_15d == fecha_defecto
                    )
                )
            ).order_by(ValoracionAntropometrica.fecha.asc()).all()
        except Exception as e:
            print(f"Error en obtener_seguimiento_14_15_dias: {e}")
            return []

    def to_dict(self):
        return {
            'id': self.id,
            'paciente_id': self.paciente_id,
            'numero_cita': self.numero_cita,
            'fecha': self.fecha.strftime('%Y-%m-%d') if self.fecha else None,
            'estatura': self.estatura,
            'peso': self.peso,
            'imc': self.imc,
            'grasa': self.grasa,
            'cintura': self.cintura,
            'torax': self.torax,
            'brazo': self.brazo,
            'cadera': self.cadera,
            'pierna': self.pierna,
            'pantorrilla': self.pantorrilla,
            'tension_arterial': self.tension_arterial,
            'frecuencia_cardiaca': self.frecuencia_cardiaca,
            'bicep': self.bicep,
            'tricep': self.tricep,
            'suprailiaco': self.suprailiaco,
            'subescapular': self.subescapular,
            'femoral': self.femoral,
            'porcentaje_grasa': self.porcentaje_grasa,
            'ultima_dieta': self.ultima_dieta
        }
