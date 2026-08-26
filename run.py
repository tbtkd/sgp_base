import logging
import os
import socket
import sys
import traceback
import webbrowser
from contextlib import suppress
from getpass import getpass
from logging.handlers import RotatingFileHandler
from pathlib import Path
from threading import Timer


def _port():
    try:
        port = int(os.environ.get("SGPN_PORT", "5000"))
    except ValueError as error:
        raise RuntimeError("SGPN_PORT debe ser numérico.") from error
    if not 1024 <= port <= 65535:
        raise RuntimeError("SGPN_PORT debe estar entre 1024 y 65535.")
    return port


def _port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
        connection.settimeout(0.5)
        return connection.connect_ex(("127.0.0.1", port)) == 0


def _open_browser(port):
    with suppress(Exception):
        webbrowser.open(f"http://127.0.0.1:{port}/", new=1)


def _runtime_directory():
    """Resuelve la carpeta de datos sin importar Flask ni dependencias externas."""
    configured = os.environ.get("SGPN_DATA_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _error_summary(error):
    message = " ".join(str(error).split()) or "sin detalle adicional"
    return f"{type(error).__name__}: {message[:500]}"


def _write_startup_failure(error):
    """Registra fallos que ocurren incluso antes de que Flask configure su logger."""
    handler = None
    try:
        log_directory = _runtime_directory() / "instance" / "logs"
        log_directory.mkdir(parents=True, exist_ok=True)
        log_path = log_directory / "startup.log"
        handler = RotatingFileHandler(log_path, maxBytes=1_048_576, backupCount=3, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger = logging.Logger("sgpn.startup", level=logging.ERROR)
        logger.addHandler(handler)
        logger.error(
            "Fallo crítico durante el inicio",
            exc_info=(type(error), error, error.__traceback__),
        )
        return log_path
    except OSError:
        return None
    finally:
        if handler is not None:
            handler.close()


def _report_startup_failure(error):
    log_path = _write_startup_failure(error)
    print("No fue posible iniciar SGPN.", file=sys.stderr)
    print(f"Causa: {_error_summary(error)}", file=sys.stderr)
    if log_path:
        print(f"Registro técnico: {log_path}", file=sys.stderr)
    else:
        print("No se pudo escribir el registro técnico; se muestra el traceback:", file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


def _handle_maintenance_command(argv=None):
    """Ejecuta recuperación local sin iniciar el servidor ni abrir el navegador."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments:
        return False
    if arguments[0] not in {"--reset-password", "--recover-admin"} or len(arguments) != 2:
        raise RuntimeError(
            "Uso: python run.py --reset-password NOMBRE_USUARIO "
            "o python run.py --recover-admin NOMBRE_USUARIO"
        )

    from app import create_app
    from app.core.password_recovery import recover_admin_offline, reset_password_offline

    recovery_password = getpass("Nueva contraseña de recuperación: ")
    confirmation = getpass("Confirma la contraseña: ")
    if recovery_password != confirmation:
        raise RuntimeError("Las contraseñas no coinciden.")
    app = create_app(os.environ.get("SGPN_ENV", "default"))
    with app.app_context():
        user = (
            recover_admin_offline(arguments[1], recovery_password)
            if arguments[0] == "--recover-admin"
            else reset_password_offline(arguments[1], recovery_password)
        )
        app.logger.warning("Recuperación local completada; usuario_id=%s", user.id)
    if arguments[0] == "--recover-admin":
        print("Acceso de Administración recuperado. Inicia sesión y establece una contraseña definitiva.")
    else:
        print("Contraseña restablecida. Inicia sesión y establece una contraseña definitiva.")
    return True


def main():
    if _handle_maintenance_command():
        return
    port = _port()
    if _port_in_use(port):
        raise RuntimeError(f"El puerto local {port} ya está en uso.")

    # Las importaciones se hacen aquí para que también se diagnostiquen las
    # dependencias ausentes o los errores tempranos de configuración.
    from waitress import serve

    from app import create_app, get_database_path

    app = create_app(os.environ.get("SGPN_ENV", "default"))
    if os.environ.get("SGPN_NO_BROWSER") != "1":
        timer = Timer(1.0, _open_browser, args=[port])
        timer.daemon = True
        timer.start()
    app.logger.info("SGPN iniciado en interfaz local; database=%s", get_database_path().name)
    serve(app, host="127.0.0.1", port=port, threads=4, clear_untrusted_proxy_headers=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        _report_startup_failure(error)
        raise SystemExit(1) from error
