from app import db
from app.models import Appointment


def test_book_appointment_shows_all_specialties(client, sample_doctor):
    response = client.get("/book-appointment")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    for specialty in (
        "Family Physician",
        "General Surgeon",
        "Neurosurgeon",
        "ENT Surgeon",
        "Obstetrician &amp; Gynaecologist",
        "Radiologist",
        "Ophthalmologist",
        "Urologist",
    ):
        assert specialty in body


def test_book_appointment_creates_record(client, sample_doctor):
    response = client.post(
        "/book-appointment",
        data={
            "patient_name": "John Doe",
            "phone": "+254712345678",
            "email": "john@example.com",
            "specialty": sample_doctor.specialty,
            "appointment_date": "2026-08-01",
            "appointment_time": "10:30",
            "reason_for_visit": "General checkup",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"submitted successfully" in response.data

    appointment = Appointment.query.first()
    assert appointment is not None
    assert appointment.patient_name == "John Doe"
    assert appointment.appointment_status == "Pending"


def test_contact_form_creates_message(client):
    response = client.post(
        "/contact",
        data={
            "full_name": "Jane Doe",
            "phone": "+254700000001",
            "email": "jane@example.com",
            "subject": "Inquiry",
            "message": "I would like more information.",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"submitted successfully" in response.data
