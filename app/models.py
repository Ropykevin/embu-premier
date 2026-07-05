from datetime import datetime

from app import db


class Doctor(db.Model):
    __tablename__ = "doctors"

    doctor_id = db.Column(db.Integer, primary_key=True)
    doctor_name = db.Column(db.String(255), nullable=False)
    specialty = db.Column(db.String(255))
    qualifications = db.Column(db.Text)
    experience_years = db.Column(db.Integer)
    consultation_fee = db.Column(db.Numeric(10, 2))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(255))
    biography = db.Column(db.Text)
    profile_photo = db.Column(db.String(255))
    availability_status = db.Column(db.String(50), default="Available")

    appointments = db.relationship("Appointment", back_populates="doctor")


class Appointment(db.Model):
    __tablename__ = "appointments"

    appointment_id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(255))
    specialty = db.Column(db.String(255))
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.doctor_id"))
    appointment_date = db.Column(db.Date)
    appointment_time = db.Column(db.Time)
    reason_for_visit = db.Column(db.Text)
    appointment_status = db.Column(db.String(50), default="Pending")
    admin_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    doctor = db.relationship("Doctor", back_populates="appointments")


class AdminUser(db.Model):
    __tablename__ = "admin_users"

    admin_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255))


class AdminAuditLog(db.Model):
    __tablename__ = "admin_audit_logs"

    log_id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admin_users.admin_id"))
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50))
    resource_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    message_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(255))
    subject = db.Column(db.String(255))
    message = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
