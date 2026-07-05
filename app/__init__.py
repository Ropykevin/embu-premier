import logging
import os

from flask import Flask, jsonify
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.middleware.proxy_fix import ProxyFix

db = SQLAlchemy()
migrate = Migrate()

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


def create_app(config_class=None):
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
    )

    if config_class is None:
        app.config.from_object("app.config.Config")
    elif isinstance(config_class, str):
        app.config.from_object(config_class)
    else:
        app.config.from_object(config_class)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    migrate.init_app(app, db)

    from app.extensions import csrf, limiter
    from app.security_utils import validate_production_settings

    csrf.init_app(app)
    limiter.init_app(app)
    limiter.enabled = app.config.get("RATELIMIT_ENABLED", True)

    from app.routes.admin import admin_bp
    from app.routes.public import public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    validate_production_settings(app)

    @app.after_request
    def set_security_headers(response):
        if app.config.get("TESTING"):
            return response
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=()",
        )
        if app.config.get("SESSION_COOKIE_SECURE"):
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        return response

    @app.route("/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))
            return jsonify({"status": "ok", "database": "connected"}), 200
        except Exception:
            app.logger.exception("Health check database failure")
            return jsonify(
                {"status": "degraded", "database": "disconnected"}
            ), 503

    return app
