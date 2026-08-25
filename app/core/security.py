import secrets
from collections import defaultdict, deque
from datetime import timedelta
from functools import wraps
from threading import Lock

from flask import abort, g
from flask_login import current_user

from app.core.time import utcnow_naive

LOGIN_WINDOW = timedelta(minutes=5)
LOGIN_LIMIT = 5
_LOGIN_FAILURES = defaultdict(deque)
_LOGIN_LOCK = Lock()


def _prune_login_failures(ip_address, now=None):
    now = now or utcnow_naive()
    cutoff = now - LOGIN_WINDOW
    failures = _LOGIN_FAILURES[ip_address]
    while failures and failures[0] <= cutoff:
        failures.popleft()
    return failures


def login_blocked(ip_address):
    with _LOGIN_LOCK:
        return len(_prune_login_failures(str(ip_address or "unknown"))) >= LOGIN_LIMIT


def register_login_failure(ip_address):
    with _LOGIN_LOCK:
        failures = _prune_login_failures(str(ip_address or "unknown"))
        failures.append(utcnow_naive())
        return len(failures)


def reset_login_failures(ip_address):
    with _LOGIN_LOCK:
        _LOGIN_FAILURES.pop(str(ip_address or "unknown"), None)


def reset_rate_limiter():
    with _LOGIN_LOCK:
        _LOGIN_FAILURES.clear()


def roles_required(*roles):
    allowed = set(roles)

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            role = getattr(current_user, "rol_clinico", current_user.rol)
            if role not in allowed:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def configure_security_headers(app):
    @app.before_request
    def create_csp_nonce():
        g.csp_nonce = secrets.token_urlsafe(18)

    @app.context_processor
    def expose_csp_nonce():
        return {"csp_nonce": getattr(g, "csp_nonce", "")}

    @app.after_request
    def add_security_headers(response):
        nonce = getattr(g, "csp_nonce", "")
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; "
            "object-src 'none'; img-src 'self' data:; connect-src 'self'; "
            f"script-src 'self' 'nonce-{nonce}'; script-src-attr 'none'; "
            f"style-src 'self' 'nonce-{nonce}'; style-src-attr 'none'; "
            "font-src 'self'; manifest-src 'self'; worker-src 'self'"
        )
        if response.content_type and "text/html" in response.content_type:
            response.headers["Cache-Control"] = "no-store, max-age=0"
            response.headers["Pragma"] = "no-cache"
        if app.config.get("SESSION_COOKIE_SECURE"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
