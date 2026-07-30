# app/core/error_handlers.py
import logging
from flask import render_template, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

def register_error_handlers(app) -> None:
    """
    Registra manejadores de errores globales en la aplicación Flask.
    Captura fallas de base de datos (SQLAlchemyError), errores HTTP (400, 404, 500)
    y excepciones generales, respondiendo con JSON para AJAX/API y HTML para navegación normal.
    """
    
    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(error: SQLAlchemyError):
        """Manejador global para errores relacionados con la Base de Datos."""
        logger.error(f"Error de Base de Datos [SQLAlchemyError]: {error}")
        error_msg = "Error en la base de datos al procesar la operación."
        if request.path.startswith('/api/') or request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return jsonify({'success': False, 'error': error_msg, 'details': str(error)}), 500
        return render_template('errors/500.html', message=error_msg), 500

    @app.errorhandler(400)
    def bad_request_error(error):
        """Manejador para errores 400 (Bad Request)."""
        mensaje = error.description if hasattr(error, 'description') and error.description else "Petición incorrecta o mal formada."
        if request.path.startswith('/api/') or request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return jsonify({'success': False, 'error': mensaje}), 400
        return render_template('errors/400.html', message=mensaje), 400

    @app.errorhandler(404)
    def not_found_error(error):
        """Manejador para errores 404 (Not Found)."""
        if request.path.startswith('/api/') or request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return jsonify({'success': False, 'error': 'Recurso o página no encontrada'}), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Manejador para errores 500 (Internal Server Error)."""
        logger.error(f"Error interno del servidor [500]: {error}")
        if request.path.startswith('/api/') or request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500
        return render_template('errors/500.html'), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        """Manejador global para cualquier excepción no controlada."""
        logger.exception(f"Excepción no controlada detectada en el sistema: {e}")
        if request.path.startswith('/api/') or request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return jsonify({'success': False, 'error': 'Ocurrió un error inesperado en el servidor'}), 500
        return render_template('errors/500.html'), 500
