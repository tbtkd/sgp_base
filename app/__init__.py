import os
import sys
import shutil
from flask import Flask, send_from_directory
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.config import config
from app.core.error_handlers import register_error_handlers

# Renombramos la instancia de SQLAlchemy para evitar conflicto con app.db
db_orm = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def get_base_path():
    if getattr(sys, 'frozen', False):
        # Si corre como ejecutable empaquetado por PyInstaller
        return sys._MEIPASS
    # Si corre en modo desarrollo
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def get_database_path():
    if getattr(sys, 'frozen', False):
        # Ruta en la carpeta de datos de usuario de Windows (%LOCALAPPDATA%/SistemaPacientes)
        app_data_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'SistemaPacientes')
        os.makedirs(app_data_dir, exist_ok=True)
        db_path = os.path.join(app_data_dir, 'sgpn_nutricion.db')
        
        # Si la base de datos no existe en AppData, la inicializamos copiando la plantilla base empaquetada
        if not os.path.exists(db_path):
            base_resource_dir = sys._MEIPASS
            packed_db_path = os.path.join(base_resource_dir, 'instance', 'sgpn_nutricion.db')
            if os.path.exists(packed_db_path):
                shutil.copy2(packed_db_path, db_path)
            else:
                # Si por alguna razón no está en sys._MEIPASS, intentar ruta alternativa
                alt_packed = os.path.join(os.path.dirname(sys.executable), 'instance', 'sgpn_nutricion.db')
                if os.path.exists(alt_packed):
                    shutil.copy2(alt_packed, db_path)
        return db_path
    else:
        # Entorno de desarrollo local
        instance_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'instance')
        os.makedirs(instance_dir, exist_ok=True)
        return os.path.join(instance_dir, 'sgpn_nutricion.db')

def create_app(config_name=None):
    """
    Función factory para crear y configurar la aplicación Flask
    Args:
        config_name (str): Nombre de la configuración a utilizar (default, development, production)
    Returns:
        Flask: Aplicación Flask configurada
    """
    # Determinar la configuración a usar
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    base_path = get_base_path()
    
    if getattr(sys, 'frozen', False):
        template_dir = os.path.join(base_path, 'app', 'templates')
        static_dir = os.path.join(base_path, 'app', 'static')
    else:
        template_dir = os.path.join(base_path, 'app', 'templates')
        static_dir = os.path.join(base_path, 'app', 'static')

    # Inicialización de la aplicación Flask
    app = Flask(__name__,
                static_folder=static_dir,
                template_folder=template_dir) 
    
    # Cargar configuración
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Configuración de base de datos persistente en LOCALAPPDATA
    db_path = get_database_path()
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"

    # Inicialización de la base de datos
    db_orm.init_app(app)
    migrate.init_app(app, db_orm)
    
    # Registro de blueprints
    from app.controllers.main import main as main_blueprint
    from app.controllers.pacientes import pacientes as pacientes_blueprint
    from app.controllers.historial_clinico import historial_clinico as historial_blueprint
    from app.controllers.valoracion_antropometrica import valoracion as valoracion_blueprint
    from app.controllers.auth import auth as auth_blueprint
    from app.controllers.plantillas import plantillas_bp as plantillas_blueprint
    
    app.register_blueprint(main_blueprint)
    app.register_blueprint(plantillas_blueprint)
    app.register_blueprint(pacientes_blueprint)
    app.register_blueprint(historial_blueprint)
    app.register_blueprint(valoracion_blueprint)
    app.register_blueprint(auth_blueprint)
    
    # REGISTRO DE MANEJADORES GLOBALES DE ERROR
    register_error_handlers(app)
    
    # CONFIGURACIÓN DE LOGIN
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = None
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.usuario import Usuario
        return Usuario.get(user_id)
    
    # RESPALDO PREVENTIVO Y MIGRACIÓN AUTOMÁTICA DE ESQUEMA
    with app.app_context():
        # 1. Copia de respaldo automática de la base de datos si existe
        if os.path.exists(db_path):
            try:
                backup_path = db_path.replace('.db', '_backup.db')
                shutil.copy2(db_path, backup_path)
            except Exception as e:
                print(f"[ADVERTENCIA] No se pudo crear el respaldo preventivo de la BD: {e}")

        from app.models.paciente import Paciente
        from app.models.cita import Cita
        from app.models.pago import Pago
        from app.models.historial_clinico import HistorialClinico
        from app.models.valoracion_antropometrica import ValoracionAntropometrica
        from app.models.usuario import Usuario
        from app.models.plantilla import PlantillaMensaje
        from app.models.bitacora import BitacoraContacto
        
        db_orm.create_all()

        # 2. Inspección y migración automática de columnas faltantes en tablas existentes
        try:
            inspector = db_orm.inspect(db_orm.engine)
            metadata = db_orm.metadata
            
            with db_orm.engine.begin() as connection:
                for table_name, table in metadata.tables.items():
                    if inspector.has_table(table_name):
                        existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
                        for column in table.columns:
                            col_name = column.name
                            if col_name not in existing_columns:
                                # Determinar tipo SQL y valor por defecto seguro
                                col_type = str(column.type)
                                default_val = "''" if 'CHAR' in col_type or 'TEXT' in col_type or 'STR' in col_type else "0"
                                if 'BOOL' in col_type:
                                    default_val = "0"
                                
                                alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type} DEFAULT {default_val}"
                                connection.execute(db_orm.text(alter_sql))
                                print(f"[MIGRACIÓN] Columna agregada automáticamente: {table_name}.{col_name}")
        except Exception as e:
            print(f"[ADVERTENCIA] Error durante la migración automática de esquema: {e}")

    # RUTA PARA FAVICON
    @app.route('/favicon.ico')
    def favicon():
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            base_dir = app.root_path

        icons_dir = os.path.join(base_dir, 'static', 'img', 'icons')
        return send_from_directory(
            icons_dir,
            'logo.ico',
            mimetype='image/vnd.microsoft.icon'
        )

    # FILTROS GLOBALES DE JINJA2
    @app.template_filter('format_date')
    def format_date(value):
        if not value:
            return ""
        try:
            fecha_str = str(value)
            fecha = fecha_str.split('-')
            meses = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
            return f"{fecha[2]} {meses[int(fecha[1])]}, {fecha[0]}"
        except:
            return value
    
    return app
