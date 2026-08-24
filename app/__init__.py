import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, flash, g, jsonify, redirect, request, send_from_directory, session, url_for
from flask_login import LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import event
from sqlalchemy.engine import Engine

from app.config import config
from app.db import data_directory, get_database_path, init_db, respaldar_db

db_orm = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


@event.listens_for(Engine, "connect")
def _configure_sqlite(dbapi_connection, connection_record):
    import sqlite3

    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()


def get_base_path():
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def create_app(config_name=None, test_config=None):
    config_name = config_name or os.environ.get("SGPN_ENV", "default")
    if config_name not in config:
        raise RuntimeError("Configuración de ejecución inválida.")

    base_path = get_base_path()
    app = Flask(
        __name__,
        static_folder=str(base_path / "app" / "static"),
        template_folder=str(base_path / "app" / "templates"),
        instance_path=str(data_directory()),
    )
    app.config.from_object(config[config_name])
    if test_config:
        app.config.update(test_config)
    config[config_name].init_app(app)

    db_path = get_database_path()
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path.as_posix()}"

    db_orm.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Debes iniciar sesión para continuar."
    login_manager.login_message_category = "error"

    from app.core.error_handlers import register_error_handlers
    from app.core.security import configure_security_headers
    from app.logger import setup_logger

    register_error_handlers(app)
    configure_security_headers(app)
    setup_logger(app, data_directory())

    from app.controllers.auth import auth
    from app.controllers.historial_clinico import historial_clinico
    from app.controllers.main import main
    from app.controllers.pacientes import pacientes
    from app.controllers.plantillas import plantillas_bp
    from app.controllers.recetas import recetas
    from app.controllers.valoracion_antropometrica import valoracion

    app.register_blueprint(main)
    app.register_blueprint(plantillas_bp)
    app.register_blueprint(pacientes)
    app.register_blueprint(historial_clinico)
    app.register_blueprint(valoracion)
    app.register_blueprint(recetas)
    app.register_blueprint(auth)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.usuario import Usuario

        try:
            return db_orm.session.get(Usuario, int(user_id))
        except (TypeError, ValueError):
            return None

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": False, "error": "Autenticación requerida"}), 401
        return redirect(url_for("auth.login", next=request.path))

    @app.before_request
    def prepare_request():
        g.request_id = str(uuid.uuid4())
        if not current_user.is_authenticated:
            return None
        if current_user.status != "activo":
            session.clear()
            logout_user()
            flash("La cuenta ya no se encuentra activa.", "warning")
            return redirect(url_for("auth.login"))
        if session.get("auth_version") != int(current_user.auth_version or 0):
            app.logger.warning("Sesión invalidada por cambio de credencial; usuario_id=%s", current_user.id)
            session.clear()
            logout_user()
            flash("La credencial cambió. Inicia sesión nuevamente.", "warning")
            return redirect(url_for("auth.login"))
        if current_user.must_change_password and request.endpoint not in {
            "auth.cambiar_contrasena",
            "auth.logout",
            "static",
            "favicon",
        }:
            flash("Debes establecer una contraseña definitiva antes de continuar.", "warning")
            return redirect(url_for("auth.cambiar_contrasena"))
        return None

    @app.after_request
    def attach_request_id(response):
        response.headers["X-Request-ID"] = getattr(g, "request_id", "")
        return response

    with app.app_context():
        if app.config.get("AUTO_BACKUP_DATABASE") and not app.config["SQLALCHEMY_DATABASE_URI"].endswith(":memory:"):
            try:
                respaldar_db(db_path, retention=app.config["BACKUP_RETENTION"])
            except (OSError, RuntimeError):
                app.logger.exception("No fue posible crear el respaldo de base de datos")
        if app.config.get("AUTO_CREATE_SCHEMA"):
            init_db(db_orm, logger=app.logger)

    @app.route("/favicon.ico")
    def favicon():
        images_dir = Path(app.static_folder) / "img"
        response = send_from_directory(images_dir, "logo.ico", mimetype="image/vnd.microsoft.icon")
        response.headers["Cache-Control"] = "no-cache, max-age=0, must-revalidate"
        response.headers["Expires"] = "0"
        return response

    @app.template_filter("format_date")
    def format_date(value):
        if not value:
            return ""
        try:
            parsed = value if hasattr(value, "strftime") else datetime.strptime(str(value), "%Y-%m-%d")
            return parsed.strftime("%d/%m/%Y")
        except (TypeError, ValueError):
            return ""

    return app
