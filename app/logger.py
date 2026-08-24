import logging
from contextlib import suppress
from logging.handlers import RotatingFileHandler
from pathlib import Path


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        try:
            from flask import g, has_request_context

            record.request_id = getattr(g, "request_id", "-") if has_request_context() else "-"
        except Exception:
            record.request_id = "-"
        return True


def setup_logger(app, target_dir: Path) -> None:
    """Configure rotating logs without recording patient data or credentials."""
    for previous in list(app.logger.handlers):
        app.logger.removeHandler(previous)
        previous.close()
    if not app.config.get("LOG_TO_FILE", True):
        app.logger.addHandler(logging.NullHandler())
        app.logger.propagate = False
        return

    log_dir = target_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    with suppress(OSError):
        log_dir.chmod(0o700)

    handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=app.config["LOG_MAX_BYTES"],
        backupCount=app.config["LOG_BACKUP_COUNT"],
        encoding="utf-8",
    )
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s request_id=%(request_id)s %(name)s: %(message)s"))
    handler.setLevel(getattr(logging, app.config["LOG_LEVEL"], logging.INFO))

    app.logger.addHandler(handler)
    app.logger.setLevel(handler.level)
    app.logger.propagate = False
