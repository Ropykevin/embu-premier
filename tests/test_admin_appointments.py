from datetime import date, time

from app import db
from app.models import Appointment


def test_admin_appointment_list_requires_login(client):
    response = client.get("/admin/appointments", follow_redirects=True)
    assert b"Administrator Login" in response.data or b"login" in response.data.lower()


def test_admin_appointment_detail_and_update(admin_client, sample_doctor):
    appointment = Appointment(
        patient_name="Jane Patient",
        phone="0712345678",
        email="jane@example.com",
        specialty=sample_doctor.specialty,
        appointment_date=date(2026, 9, 1),
        appointment_time=time(14, 0),
        reason_for_visit="Follow-up consultation",
        appointment_status="Pending",
    )
    db.session.add(appointment)
    db.session.commit()

    detail = admin_client.get(f"/admin/appointments/{appointment.appointment_id}")
    assert detail.status_code == 200
    assert b"Jane Patient" in detail.data
    assert b"Follow-up consultation" in detail.data

    response = admin_client.post(
        f"/admin/appointments/{appointment.appointment_id}/update",
        data={
            "doctor_id": str(sample_doctor.doctor_id),
            "appointment_status": "Confirmed",
            "admin_notes": "Patient called and confirmed.",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"updated successfully" in response.data

    updated = db.session.get(Appointment, appointment.appointment_id)
    assert updated.appointment_status == "Confirmed"
    assert updated.doctor_id == sample_doctor.doctor_id
    assert updated.admin_notes == "Patient called and confirmed."


def test_admin_appointment_quick_confirm(admin_client, sample_doctor):
    appointment = Appointment(
        patient_name="Quick Test",
        phone="0711111111",
        specialty=sample_doctor.specialty,
        appointment_date=date(2026, 9, 2),
        appointment_time=time(9, 0),
        appointment_status="Pending",
    )
    db.session.add(appointment)
    db.session.commit()

    response = admin_client.post(
        f"/admin/appointments/{appointment.appointment_id}/quick/confirm",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Confirmed" in response.data

    updated = db.session.get(Appointment, appointment.appointment_id)
    assert updated.appointment_status == "Confirmed"


def test_admin_appointments_filter_by_status(admin_client, sample_doctor):
    pending = Appointment(
        patient_name="Pending One",
        phone="0700000001",
        specialty=sample_doctor.specialty,
        appointment_status="Pending",
    )
    confirmed = Appointment(
        patient_name="Confirmed One",
        phone="0700000002",
        specialty=sample_doctor.specialty,
        appointment_status="Confirmed",
    )
    db.session.add_all([pending, confirmed])
    db.session.commit()

    response = admin_client.get("/admin/appointments?status=Pending")
    assert response.status_code == 200
    assert b"Pending One" in response.data
    assert b"Confirmed One" not in response.data
