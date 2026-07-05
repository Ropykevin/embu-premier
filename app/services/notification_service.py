import logging

from app.security_utils import escape_html, sanitize_email_header
from app.services.email_service import _send_email
from app.services.sms_service import send_sms

logger = logging.getLogger(__name__)


def _e(value):
    return escape_html(value)


def _appointment_details(appointment):
    doctor_name = (
        appointment.doctor.doctor_name if appointment.doctor else "Not assigned"
    )
    return {
        "patient_name": appointment.patient_name,
        "phone": appointment.phone,
        "email": appointment.email or "N/A",
        "specialty": appointment.specialty,
        "doctor_name": doctor_name,
        "date": appointment.appointment_date,
        "time": appointment.appointment_time,
        "reason": appointment.reason_for_visit or "N/A",
        "status": appointment.appointment_status,
    }


def _notify_admin_email(clinic, details):
    subject = sanitize_email_header(f"[{clinic}] New appointment request")
    body_text = (
        f"A new appointment has been submitted.\n\n"
        f"Patient: {details['patient_name']}\n"
        f"Phone: {details['phone']}\n"
        f"Email: {details['email']}\n"
        f"Specialty: {details['specialty']}\n"
        f"Doctor: {details['doctor_name']}\n"
        f"Date: {details['date']}\n"
        f"Time: {details['time']}\n"
        f"Reason: {details['reason']}\n"
        f"Status: {details['status']}\n"
    )
    body_html = f"""
    <h2>New Appointment Request</h2>
    <ul>
      <li><strong>Patient:</strong> {_e(details['patient_name'])}</li>
      <li><strong>Phone:</strong> {_e(details['phone'])}</li>
      <li><strong>Email:</strong> {_e(details['email'])}</li>
      <li><strong>Specialty:</strong> {_e(details['specialty'])}</li>
      <li><strong>Doctor:</strong> {_e(details['doctor_name'])}</li>
      <li><strong>Date:</strong> {_e(details['date'])}</li>
      <li><strong>Time:</strong> {_e(details['time'])}</li>
      <li><strong>Reason:</strong> {_e(details['reason'])}</li>
    </ul>
    """
    return _send_email(subject, body_text, body_html)


def _notify_admin_sms(clinic, details):
    from flask import current_app

    admin_phone = current_app.config.get("ADMIN_NOTIFY_PHONE")
    if not admin_phone:
        logger.warning("ADMIN_NOTIFY_PHONE not set; admin SMS skipped.")
        return False

    message = (
        f"{clinic}: New appointment.\n"
        f"Patient: {details['patient_name']}\n"
        f"Phone: {details['phone']}\n"
        f"Specialty: {details['specialty']}\n"
        f"Date: {details['date']} {details['time']}"
    )
    return send_sms(admin_phone, message)


def _notify_patient_email(clinic, appointment, details):
    from app.security_utils import is_valid_email

    if not appointment.email or not is_valid_email(appointment.email):
        return False

    subject = sanitize_email_header(f"[{clinic}] Appointment request received")
    body_text = (
        f"Dear {details['patient_name']},\n\n"
        f"Thank you for booking with {clinic}.\n\n"
        f"Your appointment request details:\n"
        f"Specialty: {details['specialty']}\n"
        f"Date: {details['date']}\n"
        f"Time: {details['time']}\n\n"
        f"We have received your request and will contact you shortly to confirm.\n\n"
        f"Embu Premier Physicians Clinic\n"
        f"+254 792 718 222"
    )
    body_html = f"""
    <h2>Appointment Request Received</h2>
    <p>Dear {_e(details['patient_name'])},</p>
    <p>Thank you for booking with <strong>{_e(clinic)}</strong>.</p>
    <ul>
      <li><strong>Specialty:</strong> {_e(details['specialty'])}</li>
      <li><strong>Date:</strong> {_e(details['date'])}</li>
      <li><strong>Time:</strong> {_e(details['time'])}</li>
    </ul>
    <p>We have received your request and will contact you shortly to confirm.</p>
    """

    return _send_email(
        subject,
        body_text,
        body_html,
        to_email=appointment.email,
    )


def _notify_patient_sms(clinic, details):
    if not details["phone"]:
        return False

    message = (
        f"Dear {details['patient_name']}, your appointment request at {clinic} "
        f"for {details['specialty']} on {details['date']} at {details['time']} "
        f"has been received. We will contact you shortly. Call +254792718222."
    )
    return send_sms(details["phone"], message)


def notify_appointment_booked(appointment):
    """
    Send appointment notifications via email and SMS to:
    - Clinic admin (email + SMS)
    - Patient (email + SMS, when contact details provided)
    """
    from flask import current_app

    clinic = current_app.config["CLINIC_NAME"]
    details = _appointment_details(appointment)

    results = {
        "admin_email": _notify_admin_email(clinic, details),
        "admin_sms": _notify_admin_sms(clinic, details),
        "patient_email": _notify_patient_email(clinic, appointment, details),
        "patient_sms": _notify_patient_sms(clinic, details),
    }

    logger.info("Appointment notifications sent: %s", results)
    return results


def notify_appointment_status_change(appointment, previous_status):
    """Notify patient and doctor when admin confirms or cancels an appointment."""
    from flask import current_app

    clinic = current_app.config["CLINIC_NAME"]
    status = appointment.appointment_status
    details = _appointment_details(appointment)

    if status == previous_status:
        return {}

    if status == "Confirmed":
        return _notify_patient_confirmed(clinic, appointment, details)
    if status == "Cancelled":
        return _notify_patient_cancelled(clinic, appointment, details)
    return {}


def _notify_patient_confirmed(clinic, appointment, details):
    from app.security_utils import is_valid_email

    doctor_line = (
        f"Consultant: {details['doctor_name']}\n"
        if details["doctor_name"] != "Not assigned"
        else ""
    )
    subject = sanitize_email_header(f"[{clinic}] Appointment confirmed")
    body_text = (
        f"Dear {details['patient_name']},\n\n"
        f"Your appointment has been CONFIRMED.\n\n"
        f"{doctor_line}"
        f"Specialty: {details['specialty']}\n"
        f"Date: {details['date']}\n"
        f"Time: {details['time']}\n\n"
        f"Please arrive 10 minutes early. Call +254 792 718 222 if you need to reschedule.\n\n"
        f"{clinic}"
    )
    body_html = f"""
    <h2>Appointment Confirmed</h2>
    <p>Dear {_e(details['patient_name'])},</p>
    <p>Your appointment at <strong>{_e(clinic)}</strong> has been confirmed.</p>
    <ul>
      <li><strong>Consultant:</strong> {_e(details['doctor_name'])}</li>
      <li><strong>Specialty:</strong> {_e(details['specialty'])}</li>
      <li><strong>Date:</strong> {_e(details['date'])}</li>
      <li><strong>Time:</strong> {_e(details['time'])}</li>
    </ul>
    <p>Please arrive 10 minutes early. Call +254 792 718 222 if you need to reschedule.</p>
    """

    sms = (
        f"{clinic}: Appointment CONFIRMED for {details['date']} at {details['time']} "
        f"with {details['doctor_name']}. Arrive 10 mins early. Call +254792718222."
    )

    results = {
        "patient_email": _send_email(
            subject, body_text, body_html, to_email=appointment.email
        )
        if appointment.email and is_valid_email(appointment.email)
        else False,
        "patient_sms": send_sms(appointment.phone, sms) if appointment.phone else False,
    }

    if appointment.doctor:
        results.update(_notify_doctor_confirmed(clinic, appointment, details))

    logger.info("Confirmation notifications sent: %s", results)
    return results


def _notify_doctor_confirmed(clinic, appointment, details):
    doctor = appointment.doctor
    subject = sanitize_email_header(
        f"[{clinic}] Confirmed appointment — {details['patient_name']}"
    )
    body_text = (
        f"Dear {doctor.doctor_name},\n\n"
        f"A patient appointment has been CONFIRMED and assigned to you.\n\n"
        f"Patient: {details['patient_name']}\n"
        f"Phone: {details['phone']}\n"
        f"Email: {details['email']}\n"
        f"Specialty: {details['specialty']}\n"
        f"Date: {details['date']}\n"
        f"Time: {details['time']}\n"
        f"Reason: {details['reason']}\n\n"
        f"{clinic}"
    )
    body_html = f"""
    <h2>Confirmed Appointment</h2>
    <p>Dear {_e(doctor.doctor_name)},</p>
    <p>A patient appointment has been confirmed and assigned to you.</p>
    <ul>
      <li><strong>Patient:</strong> {_e(details['patient_name'])}</li>
      <li><strong>Phone:</strong> {_e(details['phone'])}</li>
      <li><strong>Email:</strong> {_e(details['email'])}</li>
      <li><strong>Specialty:</strong> {_e(details['specialty'])}</li>
      <li><strong>Date:</strong> {_e(details['date'])}</li>
      <li><strong>Time:</strong> {_e(details['time'])}</li>
      <li><strong>Reason:</strong> {_e(details['reason'])}</li>
    </ul>
    """

    sms = (
        f"{clinic}: Confirmed appt with {details['patient_name']} on "
        f"{details['date']} at {details['time']}. Phone: {details['phone']}"
    )

    return {
        "doctor_email": _send_email(
            subject, body_text, body_html, to_email=doctor.email
        )
        if doctor.email
        else False,
        "doctor_sms": send_sms(doctor.phone, sms) if doctor.phone else False,
    }


def _notify_patient_cancelled(clinic, appointment, details):
    from app.security_utils import is_valid_email

    subject = sanitize_email_header(f"[{clinic}] Appointment update")
    body_text = (
        f"Dear {details['patient_name']},\n\n"
        f"Your appointment request for {details['date']} at {details['time']} "
        f"has been cancelled.\n\n"
        f"Please contact us to reschedule: +254 792 718 222\n\n"
        f"{clinic}"
    )
    body_html = f"""
    <h2>Appointment Cancelled</h2>
    <p>Dear {_e(details['patient_name'])},</p>
    <p>Your appointment request for <strong>{_e(details['date'])}</strong> at
    <strong>{_e(details['time'])}</strong> has been cancelled.</p>
    <p>Please contact us to reschedule: +254 792 718 222.</p>
    """

    sms = (
        f"{clinic}: Your appointment on {details['date']} at {details['time']} "
        f"has been cancelled. Call +254792718222 to reschedule."
    )

    results = {
        "patient_email": _send_email(
            subject, body_text, body_html, to_email=appointment.email
        )
        if appointment.email and is_valid_email(appointment.email)
        else False,
        "patient_sms": send_sms(appointment.phone, sms) if appointment.phone else False,
    }
    logger.info("Cancellation notifications sent: %s", results)
    return results
