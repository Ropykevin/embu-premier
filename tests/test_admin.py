from app import db
from app.models import Appointment, Doctor


def test_admin_login_success(client):
    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "testpass123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Welcome" in response.data or b"Dashboard" in response.data


def test_admin_login_failure(client):
    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "wrong-password"},
        follow_redirects=True,
    )
    assert b"Invalid username or password" in response.data


def test_admin_dashboard_requires_login(client):
    response = client.get("/admin/dashboard", follow_redirects=True)
    assert b"Admin Login" in response.data or b"login" in response.data.lower()


def test_admin_dashboard_authenticated(admin_client):
    response = admin_client.get("/admin/dashboard")
    assert response.status_code == 200
    assert b"Total appointments" in response.data
