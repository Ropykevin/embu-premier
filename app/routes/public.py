from datetime import datetime

from flask import Blueprint, Response, flash, redirect, render_template, request, url_for

from app import db
from app.extensions import limiter
from app.forms import BookAppointmentForm, ContactForm
from app.models import Appointment, ContactMessage, Doctor
from app.security_utils import is_valid_email
from app.services.notification_service import notify_appointment_booked
from app.services.email_service import notify_new_contact_message
from app.seo import render_robots_txt, render_sitemap_xml
from app.specialties import CLINIC_SPECIALTIES, SPECIALTY_INFO, is_valid_clinic_specialty, normalize_specialty_name

public_bp = Blueprint("public", __name__)


@public_bp.route("/robots.txt")
def robots_txt():
    return Response(render_robots_txt(), mimetype="text/plain")


@public_bp.route("/sitemap.xml")
def sitemap_xml():
    body = '<?xml version="1.0" encoding="UTF-8"?>\n' + render_sitemap_xml()
    return Response(body, mimetype="application/xml")


@public_bp.route("/")
def index():
    featured_doctors = (
        Doctor.query.order_by(Doctor.doctor_id).limit(4).all()
    )
    return render_template("index.html", featured_doctors=featured_doctors)


@public_bp.route("/about")
def about():
    return render_template("about.html")


@public_bp.route("/services")
def services():
    return render_template("services.html")


@public_bp.route("/specialists")
def specialists():
    doctors = Doctor.query.order_by(Doctor.doctor_name).all()
    return render_template("specialists.html", doctors=doctors)


@public_bp.route("/doctor/<int:doctor_id>")
def doctor_profile(doctor_id):
    doctor = db.session.get(Doctor, doctor_id)
    if not doctor:
        return render_template("404.html"), 404
    from app.seo import physician_ld_for_doctor

    return render_template(
        "doctor_profile.html",
        doctor=doctor,
        physician_ld=physician_ld_for_doctor(doctor),
    )


def _load_specialties():
    """Return all clinic specialties (not limited to doctors currently in the DB)."""
    return list(CLINIC_SPECIALTIES)


def _load_available_doctors():
    return (
        Doctor.query.filter_by(availability_status="Available")
        .order_by(Doctor.specialty, Doctor.doctor_name)
        .all()
    )


def _doctor_select_choices(doctors):
    return [("", "Any available consultant")] + [
        (str(doctor.doctor_id), f"{doctor.doctor_name} ({doctor.specialty})")
        for doctor in doctors
    ]


def _doctors_json(doctors):
    return [
        {
            "id": doctor.doctor_id,
            "name": doctor.doctor_name,
            "specialty": normalize_specialty_name(doctor.specialty) or doctor.specialty,
        }
        for doctor in doctors
    ]


def _configure_booking_form(form, doctors, preselected_doctor=None):
    specialty_names = _load_specialties()
    form.specialty.choices = [("", "Select specialty")] + [
        (name, name) for name in specialty_names
    ]
    form.doctor_id.choices = _doctor_select_choices(doctors)

    if preselected_doctor:
        normalized = normalize_specialty_name(preselected_doctor.specialty)
        if normalized in specialty_names:
            form.specialty.data = normalized
        form.doctor_id.data = str(preselected_doctor.doctor_id)
    elif request.args.get("specialty"):
        requested = normalize_specialty_name(request.args.get("specialty"))
        if requested in specialty_names:
            form.specialty.data = requested


@public_bp.route("/book-appointment", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def book_appointment():
    specialty_names = _load_specialties()
    doctors = _load_available_doctors()
    form = BookAppointmentForm()

    preselected_doctor = None
    doctor_id_arg = request.args.get("doctor_id", type=int)
    if doctor_id_arg:
        preselected_doctor = db.session.get(Doctor, doctor_id_arg)

    _configure_booking_form(form, doctors, preselected_doctor)

    if form.validate_on_submit():
        specialty = normalize_specialty_name(form.specialty.data)
        if not is_valid_clinic_specialty(specialty):
            flash("Please select a valid specialty.", "danger")
            return render_template(
                "book_appointment.html",
                form=form,
                specialty_info=SPECIALTY_INFO,
                doctors_json=_doctors_json(doctors),
            )

        doctor_id = None
        if form.doctor_id.data:
            try:
                doctor_id = int(form.doctor_id.data)
            except (TypeError, ValueError):
                doctor_id = None

        if doctor_id:
            doctor = db.session.get(Doctor, doctor_id)
            if not doctor or doctor.availability_status != "Available":
                flash("Please select a valid consultant.", "danger")
                return render_template(
                    "book_appointment.html",
                    form=form,
                    specialty_info=SPECIALTY_INFO,
                    doctors_json=_doctors_json(doctors),
                )
            doctor_specialty = normalize_specialty_name(doctor.specialty)
            if doctor_specialty and doctor_specialty != specialty:
                specialty = doctor_specialty

        email = (form.email.data or "").strip() or None
        if email and not is_valid_email(email):
            flash("Please enter a valid email address.", "danger")
            return render_template(
                "book_appointment.html",
                form=form,
                specialty_info=SPECIALTY_INFO,
                doctors_json=_doctors_json(doctors),
            )

        appointment = Appointment(
            patient_name=form.patient_name.data.strip(),
            phone=form.phone.data.strip(),
            email=email,
            specialty=specialty,
            doctor_id=doctor_id,
            appointment_date=form.appointment_date.data,
            appointment_time=form.appointment_time.data,
            reason_for_visit=(form.reason_for_visit.data or "").strip() or None,
            appointment_status="Pending",
        )
        db.session.add(appointment)
        db.session.commit()
        notify_appointment_booked(appointment)

        flash(
            "Your appointment request has been submitted successfully. "
            "We will contact you shortly to confirm.",
            "success",
        )
        return redirect(url_for("public.book_appointment"))

    return render_template(
        "book_appointment.html",
        form=form,
        specialty_info=SPECIALTY_INFO,
        doctors_json=_doctors_json(doctors),
    )


@public_bp.route("/contact", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def contact():
    form = ContactForm()

    if form.validate_on_submit():
        message = ContactMessage(
            full_name=form.full_name.data.strip(),
            phone=form.phone.data.strip(),
            email=form.email.data.strip(),
            subject=form.subject.data.strip(),
            message=form.message.data.strip(),
        )
        db.session.add(message)
        db.session.commit()
        notify_new_contact_message(message)

        flash("Your message has been submitted successfully.", "success")
        return redirect(url_for("public.contact"))

    return render_template("contact.html", form=form)
