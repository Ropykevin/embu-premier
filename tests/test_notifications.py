from unittest.mock import patch

import json
import pytest

from app.services import notification_service, sms_service


def test_normalize_kenyan_phone():
    assert sms_service.normalize_phone("0712345678") == "+254712345678"
    assert sms_service.normalize_phone("+254712345678") == "+254712345678"
    assert sms_service.normalize_phone("254712345678") == "+254712345678"
    assert sms_service.normalize_phone("712345678") == "+254712345678"


def test_notify_appointment_booked_sends_all_channels(app, sample_doctor):
    from datetime import date, time

    from app.models import Appointment

    with app.app_context():
        appointment = Appointment(
            patient_name="John Doe",
            phone="0712345678",
            email="john@example.com",
            specialty=sample_doctor.specialty,
            appointment_date=date(2026, 8, 1),
            appointment_time=time(10, 30),
            reason_for_visit="Checkup",
            appointment_status="Pending",
        )

        with patch.object(notification_service, "_notify_admin_email", return_value=True) as admin_email, \
             patch.object(notification_service, "_notify_admin_sms", return_value=True) as admin_sms, \
             patch.object(notification_service, "_notify_patient_email", return_value=True) as patient_email, \
             patch.object(notification_service, "_notify_patient_sms", return_value=True) as patient_sms:

            results = notification_service.notify_appointment_booked(appointment)

        assert results == {
            "admin_email": True,
            "admin_sms": True,
            "patient_email": True,
            "patient_sms": True,
        }
        admin_email.assert_called_once()
        admin_sms.assert_called_once()
        patient_email.assert_called_once()
        patient_sms.assert_called_once()


def test_send_sms_suppressed(app):
    with app.app_context():
        result = sms_service.send_sms("+254712345678", "Test message")
    assert result is True


def test_parse_at_response_success():
    body = json.dumps({
        "SMSMessageData": {
            "Message": "Sent to 1/1 Total Cost: KES 1.00",
            "Recipients": [{
                "statusCode": 101,
                "number": "+254712345678",
                "status": "Success",
                "messageId": "ATXid_123",
            }],
        }
    })
    assert sms_service._parse_at_response(body, "+254712345678") is True


def test_parse_at_response_invalid_sender():
    body = json.dumps({
        "SMSMessageData": {
            "Recipients": [{
                "statusCode": 402,
                "number": "+254712345678",
                "status": "InvalidSenderId",
            }],
        }
    })
    assert sms_service._parse_at_response(body, "+254712345678") is False


def test_confirmation_notifies_patient_and_doctor(app, sample_doctor):
    from datetime import date, time

    from app import db
    from app.models import Appointment

    sample_doctor.email = "doctor@clinic.com"
    sample_doctor.phone = "0722334455"
    db.session.commit()

    with app.app_context():
        appointment = Appointment(
            patient_name="John Doe",
            phone="0712345678",
            email="john@example.com",
            specialty=sample_doctor.specialty,
            doctor_id=sample_doctor.doctor_id,
            appointment_date=date(2026, 8, 1),
            appointment_time=time(10, 30),
            reason_for_visit="Checkup",
            appointment_status="Confirmed",
        )
        appointment.doctor = sample_doctor

        with patch.object(notification_service, "_send_email", return_value=True) as mock_email, \
             patch.object(notification_service, "send_sms", return_value=True) as mock_sms:

            results = notification_service._notify_patient_confirmed(
                "Embu Premier Physicians Clinic",
                appointment,
                notification_service._appointment_details(appointment),
            )

        assert results["patient_email"] is True
        assert results["patient_sms"] is True
        assert results["doctor_email"] is True
        assert results["doctor_sms"] is True
        assert mock_email.call_count == 2
        assert mock_sms.call_count == 2
