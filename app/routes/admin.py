from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy.orm import joinedload

from app import db
from app.auth import login_required, verify_admin_password
from app.constants import APPOINTMENT_STATUSES, STATUS_BADGES
from app.extensions import limiter
from app.forms import DoctorForm, LoginForm
from app.models import AdminUser, Appointment, ContactMessage, Doctor
from app.security_utils import log_admin_action
from app.services.notification_service import notify_appointment_status_change

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.context_processor
def admin_nav_context():
    if "admin_id" not in session:
        return {}

    return {
        "admin_pending_count": Appointment.query.filter_by(
            appointment_status="Pending"
        ).count(),
        "admin_message_count": ContactMessage.query.count(),
    }


def _parse_doctor_id(raw_value):
    if not raw_value:
        return None
    try:
        doctor_id = int(raw_value)
    except (TypeError, ValueError):
        return "invalid"
    if not db.session.get(Doctor, doctor_id):
        return "invalid"
    return doctor_id


@admin_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def admin_login():
    form = LoginForm()
    if form.validate_on_submit():
        admin = AdminUser.query.filter_by(username=form.username.data.strip()).first()

        if admin and verify_admin_password(admin, form.password.data):
            session.clear()
            session.permanent = True
            session["admin_id"] = admin.admin_id
            session["admin_name"] = admin.full_name
            log_admin_action("login", "admin_user", admin.admin_id)
            return redirect(url_for("admin.admin_dashboard"))

        flash("Invalid username or password", "danger")

    return render_template("admin_login.html", form=form)


@admin_bp.route("/dashboard")
@login_required
def admin_dashboard():
    total_appointments = Appointment.query.count()
    pending = Appointment.query.filter_by(appointment_status="Pending").count()
    doctors = Doctor.query.count()
    messages = ContactMessage.query.count()

    return render_template(
        "dashboard.html",
        total_appointments=total_appointments,
        pending=pending,
        doctors=doctors,
        messages=messages,
    )


@admin_bp.route("/logout", methods=["POST"])
@login_required
def admin_logout():
    log_admin_action("logout", "admin_user", session.get("admin_id"))
    session.clear()
    return redirect(url_for("admin.admin_login"))


@admin_bp.route("/appointments")
@login_required
def admin_appointments():
    status_filter = request.args.get("status", "")
    query = Appointment.query.options(joinedload(Appointment.doctor))

    if status_filter and status_filter in APPOINTMENT_STATUSES:
        query = query.filter_by(appointment_status=status_filter)

    appointments = query.order_by(Appointment.created_at.desc()).all()

    return render_template(
        "admin_appointments.html",
        appointments=appointments,
        statuses=APPOINTMENT_STATUSES,
        status_badges=STATUS_BADGES,
        current_status=status_filter,
    )


@admin_bp.route("/appointments/<int:appointment_id>")
@login_required
def admin_appointment_detail(appointment_id):
    appointment = (
        Appointment.query.options(joinedload(Appointment.doctor))
        .filter_by(appointment_id=appointment_id)
        .first_or_404()
    )
    doctors = Doctor.query.order_by(Doctor.doctor_name).all()

    return render_template(
        "admin_appointment_detail.html",
        appointment=appointment,
        doctors=doctors,
        statuses=APPOINTMENT_STATUSES,
        status_badges=STATUS_BADGES,
    )


@admin_bp.route("/appointments/<int:appointment_id>/update", methods=["POST"])
@login_required
def admin_appointment_update(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    previous_status = appointment.appointment_status

    doctor_id = _parse_doctor_id(request.form.get("doctor_id"))
    if doctor_id == "invalid":
        flash("Please select a valid doctor.", "danger")
        return redirect(url_for("admin.admin_appointment_detail", appointment_id=appointment_id))

    appointment.doctor_id = doctor_id

    status = request.form.get("appointment_status", appointment.appointment_status)
    if status in APPOINTMENT_STATUSES:
        appointment.appointment_status = status

    notes = request.form.get("admin_notes", "").strip()
    appointment.admin_notes = notes[:5000] if notes else None
    appointment.updated_at = datetime.utcnow()
    db.session.commit()
    db.session.refresh(appointment)

    if appointment.appointment_status in ("Confirmed", "Cancelled"):
        notify_appointment_status_change(appointment, previous_status)

    log_admin_action(
        "appointment_update",
        "appointment",
        appointment_id,
        f"status={appointment.appointment_status}",
    )
    flash("Appointment updated successfully.", "success")
    return redirect(url_for("admin.admin_appointment_detail", appointment_id=appointment_id))


@admin_bp.route("/appointments/<int:appointment_id>/quick/<action>", methods=["POST"])
@login_required
def admin_appointment_quick_action(appointment_id, action):
    appointment = Appointment.query.get_or_404(appointment_id)
    previous_status = appointment.appointment_status

    action_map = {
        "confirm": "Confirmed",
        "cancel": "Cancelled",
        "complete": "Completed",
    }

    if action not in action_map:
        flash("Invalid action.", "danger")
        return redirect(url_for("admin.admin_appointment_detail", appointment_id=appointment_id))

    appointment.appointment_status = action_map[action]
    appointment.updated_at = datetime.utcnow()
    db.session.commit()
    db.session.refresh(appointment)

    if appointment.appointment_status in ("Confirmed", "Cancelled"):
        notify_appointment_status_change(appointment, previous_status)

    log_admin_action(
        f"appointment_{action}",
        "appointment",
        appointment_id,
        f"status={appointment.appointment_status}",
    )

    if action == "confirm" and not appointment.doctor_id:
        flash(
            "Appointment confirmed. Patient notified. Assign a doctor so they "
            "also receive email and SMS.",
            "warning",
        )
    else:
        flash(f"Appointment marked as {appointment.appointment_status}.", "success")
    return redirect(url_for("admin.admin_appointment_detail", appointment_id=appointment_id))


@admin_bp.route("/doctors")
@login_required
def manage_doctors():
    doctors = Doctor.query.order_by(Doctor.doctor_name).all()
    return render_template("manage_doctors.html", doctors=doctors)


@admin_bp.route("/add-doctor", methods=["GET", "POST"])
@login_required
def add_doctor():
    form = DoctorForm()
    form.availability_status.data = "Available"

    if form.validate_on_submit():
        doctor = Doctor(
            doctor_name=form.doctor_name.data.strip(),
            specialty=form.specialty.data.strip(),
            qualifications=(form.qualifications.data or "").strip(),
            experience_years=form.experience_years.data or None,
            consultation_fee=form.consultation_fee.data or None,
            phone=(form.phone.data or "").strip(),
            email=(form.email.data or "").strip(),
            biography=(form.biography.data or "").strip(),
            availability_status="Available",
        )
        db.session.add(doctor)
        db.session.commit()
        log_admin_action("doctor_create", "doctor", doctor.doctor_id, doctor.doctor_name)
        flash("Doctor added successfully.", "success")
        return redirect(url_for("admin.manage_doctors"))

    return render_template("add_doctor.html", form=form)


@admin_bp.route("/edit-doctor/<int:doctor_id>", methods=["GET", "POST"])
@login_required
def edit_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    form = DoctorForm(obj=doctor)

    if form.validate_on_submit():
        doctor.doctor_name = form.doctor_name.data.strip()
        doctor.specialty = form.specialty.data.strip()
        doctor.qualifications = (form.qualifications.data or "").strip()
        doctor.experience_years = form.experience_years.data or None
        doctor.consultation_fee = form.consultation_fee.data or None
        doctor.phone = (form.phone.data or "").strip()
        doctor.email = (form.email.data or "").strip()
        doctor.biography = (form.biography.data or "").strip()
        doctor.availability_status = form.availability_status.data
        db.session.commit()
        log_admin_action("doctor_update", "doctor", doctor_id, doctor.doctor_name)
        flash("Doctor updated successfully.", "success")
        return redirect(url_for("admin.manage_doctors"))

    return render_template("edit_doctor.html", doctor=doctor, form=form)


@admin_bp.route("/delete-doctor/<int:doctor_id>", methods=["POST"])
@login_required
def delete_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)

    appointment_count = Appointment.query.filter_by(doctor_id=doctor_id).count()
    if appointment_count > 0:
        flash(
            "Doctor cannot be deleted because appointments exist.",
            "danger",
        )
        return redirect(url_for("admin.manage_doctors"))

    name = doctor.doctor_name
    db.session.delete(doctor)
    db.session.commit()
    log_admin_action("doctor_delete", "doctor", doctor_id, name)
    flash("Doctor deleted successfully.", "success")
    return redirect(url_for("admin.manage_doctors"))


@admin_bp.route("/messages")
@login_required
def admin_messages():
    messages = (
        ContactMessage.query.order_by(ContactMessage.submitted_at.desc()).all()
    )
    return render_template("admin_messages.html", messages=messages)
