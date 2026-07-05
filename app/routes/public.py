from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, url_for
from sqlalchemy import distinct

from app import db
from app.extensions import limiter
from app.forms import BookAppointmentForm, ContactForm
from app.models import Appointment, ContactMessage, Doctor
from app.security_utils import is_valid_email
from app.services.notification_service import notify_appointment_booked
from app.services.email_service import notify_new_contact_message

public_bp = Blueprint("public", __name__)


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
    return render_template("doctor_profile.html", doctor=doctor)


def _load_specialties():
    rows = (
        db.session.query(distinct(Doctor.specialty))
        .filter(Doctor.specialty.isnot(None))
        .order_by(Doctor.specialty)
        .all()
    )
    return [row[0] for row in rows]


@public_bp.route("/book-appointment", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def book_appointment():
    specialty_names = _load_specialties()
    form = BookAppointmentForm()
    form.specialty.choices = [(name, name) for name in specialty_names]

    if form.validate_on_submit():
        specialty = form.specialty.data
        if specialty not in specialty_names:
            flash("Please select a valid specialty.", "danger")
            return render_template(
                "book_appointment.html",
                form=form,
                specialties=specialty_names,
            )

        email = (form.email.data or "").strip() or None
        if email and not is_valid_email(email):
            flash("Please enter a valid email address.", "danger")
            return render_template(
                "book_appointment.html",
                form=form,
                specialties=specialty_names,
            )

        appointment = Appointment(
            patient_name=form.patient_name.data.strip(),
            phone=form.phone.data.strip(),
            email=email,
            specialty=specialty,
            doctor_id=None,
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
        specialties=specialty_names,
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
