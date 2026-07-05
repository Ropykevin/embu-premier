from app import db
from app.models import Appointment, Doctor


def test_add_doctor(admin_client):
    response = admin_client.post(
        "/admin/add-doctor",
        data={
            "doctor_name": "Dr. New Doctor",
            "specialty": "Radiologist",
            "qualifications": "MBChB",
            "experience_years": "8",
            "consultation_fee": "3000",
            "phone": "+254711111111",
            "email": "new@doctor.com",
            "biography": "Experienced radiologist.",
            "availability_status": "Available",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Doctor added successfully" in response.data
    assert Doctor.query.filter_by(doctor_name="Dr. New Doctor").first() is not None


def test_delete_doctor_blocked_when_appointments_exist(admin_client, sample_doctor):
    appointment = Appointment(
        patient_name="Patient One",
        phone="+254700000002",
        specialty=sample_doctor.specialty,
        doctor_id=sample_doctor.doctor_id,
        appointment_status="Pending",
    )
    db.session.add(appointment)
    db.session.commit()

    response = admin_client.post(
        f"/admin/delete-doctor/{sample_doctor.doctor_id}",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"cannot be deleted" in response.data
    assert db.session.get(Doctor, sample_doctor.doctor_id) is not None


def test_delete_doctor_without_appointments(admin_client, sample_doctor):
    response = admin_client.post(
        f"/admin/delete-doctor/{sample_doctor.doctor_id}",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"deleted successfully" in response.data
    assert db.session.get(Doctor, sample_doctor.doctor_id) is None
