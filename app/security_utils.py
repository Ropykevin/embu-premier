import logging
import os
import re
from html import escape

from flask import request, session

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_RE = re.compile(r"^[\d\s+\-()]{7,20}$")

WEAK_SECRET_KEYS = frozenset({
    "dev-only-change-me",
    "change-me",
    "change-me-to-a-long-random-string",
})
WEAK_ADMIN_PASSWORDS = frozenset({
    "admin123",
    "password",
    "admin",
    "change-me-admin-password",
    "dev-only-not-for-production",
})
WEAK_DB_PASSWORDS = frozenset({
    "postgres",
    "1234",
    "password",
    "change-me-strong-db-password",
})


def escape_html(value):
    if value is None:
        return ""
    return escape(str(value))


def sanitize_email_header(value):
    if value is None:
        return ""
    return str(value).replace("\r", "").replace("\n", "").strip()[:998]


def is_valid_email(value):
    if not value or len(value) > 254:
        return False
    return bool(EMAIL_RE.match(value.strip()))


def is_valid_phone(value):
    if not value:
        return False
    cleaned = value.strip()
    if not PHONE_RE.match(cleaned):
        return False
    digits = re.sub(r"\D", "", cleaned)
    return 7 <= len(digits) <= 15


def validate_production_settings(app):
    if not app.config.get("PRODUCTION"):
        return

    secret = app.config.get("SECRET_KEY", "")
    if not secret or secret in WEAK_SECRET_KEYS or len(secret) < 32:
        raise RuntimeError(
            "PRODUCTION requires a strong SECRET_KEY (32+ random characters)."
        )

    if not app.config.get("SESSION_COOKIE_SECURE"):
        raise RuntimeError("PRODUCTION requires SESSION_COOKIE_SECURE=true.")

    admin_pwd = app.config.get("ADMIN_PASSWORD_CHECK", "")
    if not admin_pwd or admin_pwd in WEAK_ADMIN_PASSWORDS or len(admin_pwd) < 12:
        raise RuntimeError(
            "PRODUCTION requires ADMIN_PASSWORD of at least 12 characters."
        )

    db_password = os.environ.get("POSTGRES_PASSWORD", "")
    if not db_password or db_password in WEAK_DB_PASSWORDS or len(db_password) < 12:
        raise RuntimeError(
            "PRODUCTION requires POSTGRES_PASSWORD of at least 12 characters."
        )


def log_admin_action(action, resource_type=None, resource_id=None, details=None):
    from app import db
    from app.models import AdminAuditLog

    admin_id = session.get("admin_id")
    if not admin_id:
        return

    entry = AdminAuditLog(
        admin_id=admin_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=request.remote_addr,
    )
    db.session.add(entry)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception("Failed to write admin audit log")
