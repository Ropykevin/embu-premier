import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def _database_uri():
    uri = os.environ.get("DATABASE_URL")
    if not uri:
        if _env_bool("PRODUCTION"):
            raise RuntimeError("DATABASE_URL is required in production.")
        uri = "postgresql://postgres:1234@localhost:5432/embu_premier_clinic"
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    return uri


def _env_bool(name, default=False):
    return os.environ.get(name, str(default)).lower() in ("1", "true", "yes")


def _env_first(*names, default=""):
    for name in names:
        value = os.environ.get(name)
        if value is not None and value != "":
            return value
    return default


class Config:
    PRODUCTION = _env_bool("PRODUCTION")
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        if PRODUCTION:
            raise RuntimeError("SECRET_KEY is required in production.")
        SECRET_KEY = "dev-only-change-me"

    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }

    PERMANENT_SESSION_LIFETIME = timedelta(
        hours=int(os.environ.get("SESSION_LIFETIME_HOURS", "8"))
    )
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", PRODUCTION)

    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = int(os.environ.get("CSRF_TIME_LIMIT", "3600"))

    RATELIMIT_ENABLED = _env_bool("RATELIMIT_ENABLED", True)
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")

    ADMIN_PASSWORD_CHECK = os.environ.get("ADMIN_PASSWORD", "")

    # Email / SMTP (supports SMTP_* or EMAIL_* env names)
    SMTP_HOST = _env_first("SMTP_HOST", "EMAIL_SERVER", default="smtp.gmail.com")
    SMTP_PORT = int(_env_first("SMTP_PORT", "EMAIL_PORT", default="587"))
    SMTP_USER = _env_first("SMTP_USER", "EMAIL_USERNAME")
    SMTP_PASSWORD = _env_first("SMTP_PASSWORD", "EMAIL_PASSWORD").replace(" ", "").strip('"').strip("'")
    SMTP_USE_TLS = _env_bool("SMTP_USE_TLS") if "SMTP_USE_TLS" in os.environ else _env_bool("EMAIL_USE_TLS", True)
    SMTP_USE_SSL = _env_bool("SMTP_USE_SSL") if "SMTP_USE_SSL" in os.environ else _env_bool("EMAIL_USE_SSL", False)
    MAIL_FROM = _env_first("MAIL_FROM", "EMAIL_SENDER", default=SMTP_USER)
    ADMIN_NOTIFY_EMAIL = _env_first(
        "ADMIN_NOTIFY_EMAIL",
        "CLINIC_EMAIL",
        "EMAIL_SENDER",
        default="embupremierclinic@gmail.com",
    )
    MAIL_SUPPRESS_SEND = _env_bool("MAIL_SUPPRESS_SEND", False)
    if "MAIL_ENABLED" in os.environ:
        MAIL_ENABLED = _env_bool("MAIL_ENABLED")
    else:
        MAIL_ENABLED = bool(SMTP_USER and SMTP_PASSWORD)
    CLINIC_NAME = os.environ.get("CLINIC_NAME", "Embu Premier Physicians Clinic")

    # Africa's Talking
    AT_USERNAME = os.environ.get("AT_USERNAME", "")
    AT_API_KEY = os.environ.get("AT_API_KEY", "")
    AT_SENDER_ID = _env_first("AT_SENDER_ID", "AT_FROM")
    AT_API_URL = _env_first(
        "AT_URL",
        default="https://api.africastalking.com/version1/messaging",
    )
    AT_SANDBOX = _env_bool("AT_SANDBOX", False)
    if AT_SANDBOX:
        AT_USERNAME = "sandbox"
        AT_API_URL = "https://api.sandbox.africastalking.com/version1/messaging"
    if "SMS_ENABLED" in os.environ:
        SMS_ENABLED = _env_bool("SMS_ENABLED")
    else:
        SMS_ENABLED = bool(AT_USERNAME and AT_API_KEY)

    SMS_SUPPRESS_SEND = _env_bool("SMS_SUPPRESS_SEND", False)
    SMS_PROVIDER = os.environ.get("SMS_PROVIDER", "africastalking")
    ADMIN_NOTIFY_PHONE = os.environ.get("ADMIN_NOTIFY_PHONE", "+254792718222")

    # Twilio (alternative)
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
    TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER", "")


class TestConfig(Config):
    TESTING = True
    PRODUCTION = False
    SECRET_KEY = "test-secret-key-for-pytest-only-not-production"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    MAIL_ENABLED = False
    MAIL_SUPPRESS_SEND = True
    SMS_ENABLED = False
    SMS_SUPPRESS_SEND = True
    SESSION_COOKIE_SECURE = False
