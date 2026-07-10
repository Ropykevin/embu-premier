from flask_wtf import FlaskForm
from wtforms import DateField, EmailField, PasswordField, SelectField, StringField, TextAreaField, TimeField
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp


class LoginForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=2, max=100)],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=128)],
    )


class BookAppointmentForm(FlaskForm):
    patient_name = StringField(
        "Patient name",
        validators=[DataRequired(), Length(min=2, max=255)],
    )
    phone = StringField(
        "Phone",
        validators=[
            DataRequired(),
            Length(min=7, max=50),
            Regexp(r"^[\d\s+\-()]+$", message="Invalid phone number."),
        ],
    )
    email = EmailField(
        "Email",
        validators=[Optional(), Email(), Length(max=254)],
    )
    specialty = SelectField(
        "Specialty",
        choices=[],
        validators=[DataRequired()],
    )
    doctor_id = SelectField(
        "Preferred consultant",
        choices=[],
        validators=[Optional()],
    )
    appointment_date = DateField("Date", validators=[DataRequired()])
    appointment_time = TimeField("Time", validators=[DataRequired()])
    reason_for_visit = TextAreaField(
        "Reason",
        validators=[Optional(), Length(max=2000)],
    )


class ContactForm(FlaskForm):
    full_name = StringField(
        "Full name",
        validators=[DataRequired(), Length(min=2, max=255)],
    )
    phone = StringField(
        "Phone",
        validators=[
            DataRequired(),
            Length(min=7, max=50),
            Regexp(r"^[\d\s+\-()]+$", message="Invalid phone number."),
        ],
    )
    email = EmailField(
        "Email",
        validators=[DataRequired(), Email(), Length(max=254)],
    )
    subject = StringField(
        "Subject",
        validators=[DataRequired(), Length(min=2, max=255)],
    )
    message = TextAreaField(
        "Message",
        validators=[DataRequired(), Length(min=5, max=5000)],
    )


class DoctorForm(FlaskForm):
    doctor_name = StringField(
        "Doctor name",
        validators=[DataRequired(), Length(min=2, max=255)],
    )
    specialty = StringField(
        "Specialty",
        validators=[DataRequired(), Length(max=255)],
    )
    qualifications = StringField(
        "Qualifications",
        validators=[Optional(), Length(max=500)],
    )
    experience_years = StringField(
        "Experience years",
        validators=[Optional(), Length(max=3)],
    )
    consultation_fee = StringField(
        "Consultation fee",
        validators=[Optional(), Length(max=12)],
    )
    phone = StringField(
        "Phone",
        validators=[Optional(), Length(max=50)],
    )
    email = EmailField(
        "Email",
        validators=[Optional(), Email(), Length(max=254)],
    )
    biography = TextAreaField(
        "Biography",
        validators=[Optional(), Length(max=5000)],
    )
    availability_status = SelectField(
        "Availability",
        choices=[("Available", "Available"), ("Unavailable", "Unavailable")],
        validators=[DataRequired()],
        default="Available",
    )
