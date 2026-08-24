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
        return _response("No fue posible completar la operación en la base de datos.", 500)

    @app.errorhandler(413)
    def too_large(error):
        return _response("La solicitud excede el límite permitido de 16 MB.", 413)

    @app.errorhandler(HTTPException)
    def http_error(error):
        messages = {
            400: "La solicitud contiene datos inválidos.",
            401: "Debes iniciar sesión para continuar.",
            403: "No tienes permiso para realizar esta acción.",
            404: "El recurso solicitado no existe.",
            405: "El método solicitado no está permitido.",
            429: "Demasiados intentos. Espera antes de intentarlo nuevamente.",
        }
        return _response(messages.get(error.code, "No fue posible procesar la solicitud."), error.code)

    @app.errorhandler(Exception)
    def unhandled_error(error):
        db.session.rollback()
        logger.exception("Excepción no controlada")
        return _response("Ocurrió un error inesperado. El incidente quedó registrado.", 500)
