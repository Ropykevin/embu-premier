import os

from sqlalchemy import inspect, text
from werkzeug.security import generate_password_hash

from app import db
from app.models import AdminUser, Doctor
from app.security_utils import WEAK_ADMIN_PASSWORDS


def _validate_admin_password(password):
    if len(password) < 12:
        raise ValueError(
            "ADMIN_PASSWORD must be at least 12 characters. "
            "Set a strong password in .env before running init-db."
        )
    if password in WEAK_ADMIN_PASSWORDS:
        raise ValueError(
            "ADMIN_PASSWORD is a known weak default. Choose a unique strong password."
        )


def init_database(seed_sample_doctors=False):
    """Create all tables and seed the default admin user."""
    db.create_all()

    username = os.environ.get("ADMIN_USERNAME", "admin")
    password = os.environ.get("ADMIN_PASSWORD", "")
    full_name = os.environ.get("ADMIN_FULL_NAME", "Clinic Administrator")

    if not AdminUser.query.filter_by(username=username).first():
        if not password:
            if os.environ.get("PRODUCTION"):
                raise RuntimeError("ADMIN_PASSWORD is required in production.")
            password = "dev-only-not-for-production"
            print("WARNING: Using temporary dev admin password. Set ADMIN_PASSWORD in .env.")
        else:
            _validate_admin_password(password)

        admin = AdminUser(
            username=username,
            password_hash=generate_password_hash(password),
            full_name=full_name,
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Created admin user: {username}")
    else:
        print(f"Admin user '{username}' already exists.")

    if seed_sample_doctors and Doctor.query.count() == 0:
        sample_doctors = [
            Doctor(
                doctor_name="Dr. Jane Wanjiru",
                specialty="Family Physician",
                qualifications="MBChB, MMed Family Medicine",
                experience_years=12,
                consultation_fee=2500,
                phone="+254 792 718 222",
                email="jane.wanjiru@embupremierclinic.com",
                biography="Provides comprehensive healthcare for children, adults and the elderly.",
            ),
            Doctor(
                doctor_name="Dr. Peter Kamau",
                specialty="General Surgeon",
                qualifications="MBChB, MMed Surgery",
                experience_years=15,
                consultation_fee=3500,
                phone="+254 792 718 223",
                email="peter.kamau@embupremierclinic.com",
                biography="Expert surgical consultation and operative management.",
            ),
            Doctor(
                doctor_name="Dr. Grace Muthoni",
                specialty="Obstetrician & Gynaecologist",
                qualifications="MBChB, MMed OBGYN",
                experience_years=10,
                consultation_fee=3000,
                phone="+254 792 718 224",
                email="grace.muthoni@embupremierclinic.com",
                biography="Compassionate care for women's reproductive health and pregnancy.",
            ),
        ]
        db.session.add_all(sample_doctors)
        db.session.commit()
        print(f"Seeded {len(sample_doctors)} sample doctors.")

    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"Database ready. Tables: {', '.join(sorted(tables))}")


def database_is_initialized():
    inspector = inspect(db.engine)
    required = {"doctors", "appointments", "admin_users", "contact_messages"}
    return required.issubset(set(inspector.get_table_names()))
