import os
import secrets
from contextlib import suppress
from datetime import timedelta
from pathlib import Path

from app.db import data_directory


def _load_or_create_secret(target_directory=None) -> str:
    configured = os.environ.get("SGPN_SECRET_KEY")
    if configured:
        if len(configured) < 32:
            raise RuntimeError("SGPN_SECRET_KEY debe contener al menos 32 caracteres.")
        return configured

    target_dir = Path(target_directory or data_directory())
    target_dir.mkdir(parents=True, exist_ok=True)
    secret_file = target_dir / ".secret_key"
    if secret_file.exists():
        secret = secret_file.read_text(encoding="utf-8").strip()
        if len(secret) >= 32:
            return secret

    legacy_secret = target_dir / ".session_secret"
    if legacy_secret.exists():
        secret = legacy_secret.read_text(encoding="utf-8").strip()
        if len(secret) >= 32:
            secret_file.write_text(secret, encoding="utf-8")
            with suppress(OSError):
                secret_file.chmod(0o600)
            return secret

    secret = secrets.token_hex(32)
    secret_file.write_text(secret, encoding="utf-8")
    with suppress(OSError):
        secret_file.chmod(0o600)
    return secret


class Config:
    APP_VERSION = "1.10.1"
    ASSET_VERSION = "1.10.1"
    SECRET_KEY = None
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = False
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    REMEMBER_COOKIE_DURATION = timedelta(hours=8)
    SESSION_REFRESH_EACH_REQUEST = True

    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 7200
    AUTO_CREATE_SCHEMA = True
    AUTO_BACKUP_DATABASE = True
    BACKUP_RETENTION = 10
    BACKUP_AFTER_CRITICAL_MUTATION = True
    LOG_LEVEL = "INFO"
    LOG_TO_FILE = True
    LOG_MAX_BYTES = 1_048_576
    LOG_BACKUP_COUNT = 5

    @staticmethod
    def init_app(app):
        if not app.config.get("SECRET_KEY"):
            app.config["SECRET_KEY"] = _load_or_create_secret()


class DevelopmentConfig(Config):
    DEBUG = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


class TestingConfig(Config):
    TESTING = True
    # This key is isolated to ephemeral test databases and is never used at runtime.
    SECRET_KEY = "testing-secret-key-with-at-least-32-chars"  # nosec B105
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    AUTO_BACKUP_DATABASE = False
    BACKUP_AFTER_CRITICAL_MUTATION = False
    LOG_LEVEL = "CRITICAL"
    LOG_TO_FILE = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
