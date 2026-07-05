from functools import wraps

from flask import flash, redirect, session, url_for
from werkzeug.security import check_password_hash

from app import db
from app.models import AdminUser


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        admin_id = session.get("admin_id")
        if not admin_id:
            return redirect(url_for("admin.admin_login"))

        admin = db.session.get(AdminUser, admin_id)
        if not admin:
            session.clear()
            flash("Your session has expired. Please sign in again.", "warning")
            return redirect(url_for("admin.admin_login"))

        return view(*args, **kwargs)

    return wrapped_view


def verify_admin_password(admin, password):
    stored = admin.password_hash
    if not stored.startswith(("pbkdf2:", "scrypt:")):
        return False
    return check_password_hash(stored, password)
