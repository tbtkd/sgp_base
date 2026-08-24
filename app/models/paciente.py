from datetime import datetime, timedelta

from sqlalchemy import asc, desc, func, text

from app import db_orm as db
from app.core.time import utcnow_naive


class Paciente(db.Model):
    __tablename__ = "pacientes"
    __table_args__ = (
        db.CheckConstraint("status IN ('activo','inactivo')", name="ck_pacientes_status"),
        db.CheckConstraint("genero IN ('hombre','mujer','otro','prefiero_no_decir')", name="ck_pacientes_genero"),
    )

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(60), nullable=False, index=True)
    apellido_paterno = db.Column(db.String(60), nullable=False, index=True)
    apellido_materno = db.Column(db.String(60), nullable=True)
    genero = db.Column(db.String(30), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    telefono = db.Column(db.String(10), nullable=False, index=True)
    correo = db.Column(db.String(254), nullable=True)
    ciudad = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(250), nullable=True)
    ocupacion = db.Column(db.String(120), nullable=True)
    contacto_emergencia = db.Column(db.String(120), nullable=True)
    telefono_emergencia = db.Column(db.String(10), nullable=True)
    fecha_registro = db.Column(
        db.DateTime, nullable=False, default=utcnow_naive, server_default=text("CURRENT_TIMESTAMP")
    )
    status = db.Column(
        db.String(20), nullable=False, default="activo", server_default=text("'activo'"), index=True
    )

    @property
    def nombre_completo(self):
        return " ".join(filter(None, [self.nombre, self.apellido_paterno, self.apellido_materno]))

    @property
    def edad(self):
        today = datetime.now().date()
        born = self.fecha_nacimiento
        if not born:
            return None
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    @property
    def whatsapp_url(self):
        from urllib.parse import quote

        message = quote(f"Hola {self.nombre}, te contactamos desde tu consultorio.")
        return f"https://wa.me/52{self.telefono}?text={message}"

    @staticmethod
    def crear(**data):
        patient = Paciente(**data)
        db.session.add(patient)
        return patient

    @staticmethod
    def contar_activos():
        return Paciente.query.filter_by(status="activo").count()

    @staticmethod
    def calcular_crecimiento_mensual():
        start = utcnow_naive().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return Paciente.query.filter(Paciente.fecha_registro >= start).count()

    @staticmethod
    def contar_en_seguimiento():
        return Paciente.query.filter_by(status="activo").count()

    @staticmethod
    def buscar(busqueda, status="activo", ordenar_por="id", orden="desc"):
        from app.models.valoracion_antropometrica import ValoracionAntropometrica

        latest = (
            db.session.query(
                ValoracionAntropometrica.paciente_id,
                func.max(ValoracionAntropometrica.fecha).label("ultima_val"),
            )
            .group_by(ValoracionAntropometrica.paciente_id)
            .subquery()
        )
        query = (
            db.session.query(Paciente, latest.c.ultima_val.label("ultima_consulta"))
            .outerjoin(latest, Paciente.id == latest.c.paciente_id)
            .filter(Paciente.status == status)
        )
        cleaned = str(busqueda or "").strip()[:100]
        if cleaned:
            query = query.filter(
                Paciente.nombre.contains(cleaned)
                | Paciente.apellido_paterno.contains(cleaned)
                | Paciente.apellido_materno.contains(cleaned)
                | Paciente.telefono.contains(cleaned)
                | Paciente.correo.contains(cleaned)
            )
        columns = {
            "id": Paciente.id,
            "nombre": Paciente.nombre,
            "apellidos": Paciente.apellido_paterno,
            "ultima_consulta": latest.c.ultima_val,
        }
        column = columns.get(ordenar_por, Paciente.id)
        query = query.order_by(asc(column) if orden == "asc" else desc(column))
        result = []
        for patient, latest_date in query.limit(500).all():
            patient.ultima_consulta = latest_date
            result.append(patient)
        return result

    @staticmethod
    def obtener_por_id(patient_id):
        return db.session.get(Paciente, patient_id)

    @staticmethod
    def obtener_pendientes_por_agendar():
        query = text("""
            SELECT p.id, p.nombre, p.apellido_paterno, p.apellido_materno,
                   MAX(c.fecha) AS ultima_cita,
                   (JULIANDAY('now') - JULIANDAY(MAX(c.fecha))) AS dias_transcurridos
            FROM pacientes p LEFT JOIN citas c ON p.id = c.paciente_id
            WHERE p.status = 'activo'
            GROUP BY p.id
            HAVING MAX(c.fecha) < DATE('now', '-30 days') OR MAX(c.fecha) IS NULL
            LIMIT 500
        """)
        return db.session.execute(query).fetchall()

    @staticmethod
    def obtener_sin_valoracion_reciente(dias=30):
        cutoff = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
        query = text("""
            SELECT p.id, p.nombre, p.apellido_paterno, p.apellido_materno,
                   MAX(v.fecha) AS ultima_valoracion,
                   (JULIANDAY('now') - JULIANDAY(MAX(v.fecha))) AS dias_transcurridos
            FROM pacientes p JOIN valoracion_antropometrica v ON p.id = v.paciente_id
            WHERE p.status = 'activo'
            GROUP BY p.id HAVING MAX(v.fecha) < :cutoff LIMIT 500
        """)
        return db.session.execute(query, {"cutoff": cutoff}).fetchall()
