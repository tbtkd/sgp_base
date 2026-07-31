import os
from datetime import timedelta

class Config:
    """Configuración base"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-secreta-por-defecto'
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = True
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    
    # Configuración de logging
    #LOG_LEVEL = 'INFO'
    #LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    """Configuración de desarrollo"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # Permitir HTTP en desarrollo
    SQLALCHEMY_DATABASE_URI = 'sqlite:///sgpn_nutricion.db'
    # LOG_LEVEL = 'DEBUG' 
    # TODO: Descomentar para habilitar logging en desarrollo
    
class ProductionConfig(Config):
    """Configuración de producción"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///production.db'
    
    @staticmethod
    def init_app(app):
        # Configuración adicional para producción
        import logging
        from logging.handlers import RotatingFileHandler
        
        handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
        handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}