import unittest
from datetime import date
from app import create_app, db_orm as db
from app.models.plantilla import PlantillaMensaje
from app.models.paciente import Paciente

class SistemaPacientesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_plantilla_activa_por_defecto(self):
        with self.app.app_context():
            p1 = PlantillaMensaje(titulo='Plantilla Defecto', contenido='Hola {nombre}', esta_activa=True)
            db.session.add(p1)
            db.session.commit()

            plantilla = PlantillaMensaje.obtener_activa()
            self.assertIsNotNone(plantilla)
            self.assertTrue(plantilla.esta_activa)

    def test_crear_y_activar_plantilla(self):
        with self.app.app_context():
            p1 = PlantillaMensaje(titulo='Plantilla 1', contenido='Hola {nombre}', esta_activa=True)
            db.session.add(p1)
            db.session.commit()

            p2 = PlantillaMensaje(titulo='Plantilla 2', contenido='Saludos {nombre}, {dias}', esta_activa=False)
            db.session.add(p2)
            db.session.commit()

            # Método activar en plantilla
            p2.esta_activa = True
            p1.esta_activa = False
            db.session.commit()

            activa = PlantillaMensaje.obtener_activa()
            self.assertEqual(activa.id, p2.id)
            self.assertTrue(p2.esta_activa)
            self.assertFalse(p1.esta_activa)

    def test_modelo_paciente(self):
        with self.app.app_context():
            paciente = Paciente(
                nombre='Juan',
                apellido_paterno='Pérez',
                apellido_materno='Gómez',
                genero='Masculino',
                fecha_nacimiento=date(1994, 5, 15),
                telefono='5512345678',
                correo='juan@example.com',
                ciudad='CDMX'
            )
            db.session.add(paciente)
            db.session.commit()

            encontrado = Paciente.query.filter_by(nombre='Juan').first()
            self.assertIsNotNone(encontrado)
            self.assertEqual(encontrado.nombre_completo, 'Juan Pérez Gómez')

if __name__ == '__main__':
    unittest.main()
