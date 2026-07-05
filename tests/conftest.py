import pytest
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.config import TestConfig
from app.models import AdminUser, Doctor


@pytest.fixture
def app():
    application = create_app(TestConfig)
    with application.app_context():
        db.create_all()
        admin = AdminUser(
            username="admin",
            password_hash=generate_password_hash("testpass123"),
            full_name="Test Admin",
        )
        db.session.add(admin)
        db.session.commit()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_client(client):
    client.post(
        "/admin/login",
        data={"username": "admin", "password": "testpass123"},
        follow_redirects=True,
    )
    return client


@pytest.fixture
def sample_doctor(app):
    doctor = Doctor(
        doctor_name="Dr. Test Specialist",
        specialty="Family Physician",
        qualifications="MBChB",
        experience_years=5,
        consultation_fee=2000,
        phone="+254700000000",
        email="doctor@test.com",
        biography="Test biography",
    )
    db.session.add(doctor)
    db.session.commit()
    return doctor
