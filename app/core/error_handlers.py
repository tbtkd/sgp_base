import logging

from flask import jsonify, render_template, request
from flask_wtf.csrf import CSRFError
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from app import db_orm as db

logger = logging.getLogger(__name__)


def _wants_json():
    return (
        request.path.startswith("/api/")
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.is_json
        or request.accept_mimetypes.best == "application/json"
    )


def _response(message, status):
    if _wants_json():
        return jsonify({"success": False, "error": message}), status
    template = "errors/404.html" if status == 404 else "errors/500.html"
    if status in {400, 401, 403, 413, 429}:
        template = "errors/error.html"
    return render_template(template, message=message, status_code=status), status


def register_error_handlers(app):
    @app.errorhandler(CSRFError)
    def csrf_error(error):
        logger.warning("Solicitud rechazada por CSRF")
        return _response("La sesión del formulario expiró. Recarga la página e inténtalo nuevamente.", 400)

    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        db.session.rollback()
        logger.exception("Error de base de datos")
        return _response("No fue posible guardar los cambios. Inténtalo de nuevo.", 500)

    @app.errorhandler(413)
    def too_large(error):
        return _response("El archivo es demasiado grande. Elige uno de hasta 16 MB.", 413)

    @app.errorhandler(HTTPException)
    def http_error(error):
        messages = {
            400: "Revisa la información capturada e inténtalo de nuevo.",
            401: "Debes iniciar sesión para continuar.",
            403: "No tienes permiso para realizar esta acción.",
            404: "No encontramos la página o información solicitada.",
            405: "Esta acción no está disponible desde aquí.",
            429: "Demasiados intentos. Espera antes de intentarlo nuevamente.",
        }
        return _response(messages.get(error.code, "No pudimos completar esta acción."), error.code)

    @app.errorhandler(Exception)
    def unhandled_error(error):
        db.session.rollback()
        logger.exception("Excepción no controlada")
        return _response("Ocurrió algo inesperado. Inténtalo de nuevo; si continúa, avisa a Administración.", 500)
