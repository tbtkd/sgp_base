import logging
from logging.handlers import RotatingFileHandler

def setup_logger(app, config):
    """Configura el sistema de logging"""
    formatter = logging.Formatter(config.LOG_FORMAT)
    
    # Configurar el logger de la aplicación
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=1024 * 1024,  # 1MB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Configurar el logger de errores
    error_handler = RotatingFileHandler(
        'logs/error.log',
        maxBytes=1024 * 1024,
        backupCount=10
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.setLevel(getattr(logging, config.LOG_LEVEL))