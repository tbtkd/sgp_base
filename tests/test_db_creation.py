import os
import sys
from datetime import datetime, date

# Añadir la ruta raíz al path para importar la app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db_orm as db
from app.models.usuario import Usuario
from app.models.paciente import Paciente
from app.models.cita import Cita
from app.models.pago import Pago
from app.models.historial_clinico import HistorialClinico
from app.models.valoracion_antropometrica import ValoracionAntropometrica

def run_integration_test():
    db_path = 'test_schema.db'
    if os.path.exists(db_path):
        os.remove(db_path)

    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['TESTING'] = True

    print("🚀 [PRUEBA] Inicializando contexto de aplicación para prueba de esquema...")
    with app.app_context():
        try:
            # Crear todas las tablas
            db.create_all()
            print("✅ [ÉXITO] Todas las tablas creadas correctamente en la base de datos de prueba.")

            # 1. Insertar Usuario
            import time
            from werkzeug.security import generate_password_hash
            unique_username = f"nutri_{int(time.time())}"
            usuario = Usuario(username=unique_username, nombre="Nutrióloga de Prueba", email="nutri@prueba.com", password_hash=generate_password_hash("password123"))
            db.session.add(usuario)
            db.session.commit()
            print(f"  -> Usuario insertado con ID: {usuario.id}")

            # 2. Insertar Paciente
            unique_correo = f"juan_{int(time.time())}@prueba.com"
            paciente = Paciente(
                nombre="Juan",
                apellido_paterno="Pérez",
                apellido_materno="García",
                genero="hombre",
                fecha_nacimiento=date(1996, 5, 15),
                telefono="5551234567",
                correo=unique_correo,
                ciudad="Ciudad de México"
            )
            db.session.add(paciente)
            db.session.commit()
            print(f"  -> Paciente insertado con ID: {paciente.id}")

            # 3. Insertar Cita
            from datetime import time
            cita = Cita(
                paciente_id=paciente.id,
                fecha=date.today(),
                hora=time(10, 0),
                estado="completada"
            )
            db.session.add(cita)
            db.session.commit()
            print(f"  -> Cita insertada con ID: {cita.id}")

            # 4. Insertar Pago
            pago = Pago(
                paciente_id=paciente.id,
                fecha_pago=date.today()
            )
            db.session.add(pago)
            db.session.commit()
            print(f"  -> Pago insertado con ID: {pago.id}")

            # 5. Insertar Historial Clínico
            historial = HistorialClinico(
                paciente_id=paciente.id,
                cirugias="Ninguna",
                padecimientos="Ninguno",
                medicamentos="Ninguno",
                suplementos="Proteína",
                enfermedades_previas="Ninguna",
                enfermedades_actuales="Ninguna",
                tipo_actividad_fisica="Gimnasio",
                frecuencia_actividad_fisica="4 días por semana",
                tiempo_actividad_fisica="60 minutos",
                numero_comidas_diarias=4,
                alimentos_normales="Pollo, arroz, verduras",
                alimentos_no_gustados="Pescado"
            )
            db.session.add(historial)
            db.session.commit()
            print(f"  -> Historial clínico insertado con ID: {historial.id}")

            # 6. Insertar Valoración Antropométrica
            valoracion = ValoracionAntropometrica(
                paciente_id=paciente.id,
                numero_cita=1,
                fecha=date.today(),
                estatura=1.75,
                peso=80.0,
                imc=26.1,
                grasa=18.5,
                cintura=85.0,
                torax=95.0,
                brazo=32.0,
                cadera=98.0,
                pierna=55.0,
                pantorrilla=38.0,
                tension_arterial="120/80",
                frecuencia_cardiaca=72,
                bicep=31.0,
                tricep=12.0,
                suprailiaco=15.0,
                subescapular=14.0,
                femoral=9.5,
                porcentaje_grasa="18.5%",
                ultima_dieta="Dieta alta en proteína"
            )
            db.session.add(valoracion)
            db.session.commit()
            print(f"  -> Valoración antropométrica insertada con ID: {valoracion.id}")

            # Verificación de relaciones
            print("\n🔍 Verificando relaciones ORM...")
            v_check = ValoracionAntropometrica.query.first()
            print(f"  * Relación Valoración -> Paciente Nombre: {v_check.paciente.nombre}")
            
            h_check = HistorialClinico.query.first()
            print(f"  * Relación Historial -> Paciente Nombre: {h_check.paciente.nombre}")

            p_check = Paciente.query.first()
            print(f"  * Conteo de valoraciones del paciente: {len(p_check.valoraciones_lista)}")
            print(f"  * Conteo de pagos del paciente: {len(p_check.pagos)}")

            print("\n🎉 [PRUEBA EXITOSA] Todas las tablas, llaves foráneas y relaciones ORM funcionan perfectamente.")

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ [ERROR CRÍTICO] Falló la prueba de integración: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

        finally:
            # Limpieza del archivo de base de datos de prueba
            if os.path.exists(db_path):
                os.remove(db_path)
                print(f"🧹 [LIMPIEZA] Archivo de prueba '{db_path}' eliminado exitosamente.")

if __name__ == '__main__':
    run_integration_test()
