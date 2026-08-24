from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def admin_required(view):
    """Exige sesión activa y rol administrativo."""

    @login_required
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user.rol_clinico != "admin":
            abort(403)
        return view(*args, **kwargs)

    return wrapped


__all__ = ["admin_required", "login_required"]
