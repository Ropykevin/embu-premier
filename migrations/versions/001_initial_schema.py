"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-07-05

"""
from alembic import op
import sqlalchemy as sa


revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "doctors",
        sa.Column("doctor_id", sa.Integer(), nullable=False),
        sa.Column("doctor_name", sa.String(length=255), nullable=False),
        sa.Column("specialty", sa.String(length=255), nullable=True),
        sa.Column("qualifications", sa.Text(), nullable=True),
        sa.Column("experience_years", sa.Integer(), nullable=True),
        sa.Column("consultation_fee", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("biography", sa.Text(), nullable=True),
        sa.Column("profile_photo", sa.String(length=255), nullable=True),
        sa.Column(
            "availability_status",
            sa.String(length=50),
            nullable=True,
            server_default="Available",
        ),
        sa.PrimaryKeyConstraint("doctor_id"),
    )

    op.create_table(
        "admin_users",
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("admin_id"),
        sa.UniqueConstraint("username"),
    )

    op.create_table(
        "contact_messages",
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("subject", sa.String(length=255), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("message_id"),
    )

    op.create_table(
        "appointments",
        sa.Column("appointment_id", sa.Integer(), nullable=False),
        sa.Column("patient_name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("specialty", sa.String(length=255), nullable=True),
        sa.Column("doctor_id", sa.Integer(), nullable=True),
        sa.Column("appointment_date", sa.Date(), nullable=True),
        sa.Column("appointment_time", sa.Time(), nullable=True),
        sa.Column("reason_for_visit", sa.Text(), nullable=True),
        sa.Column(
            "appointment_status",
            sa.String(length=50),
            nullable=True,
            server_default="Pending",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctors.doctor_id"]),
        sa.PrimaryKeyConstraint("appointment_id"),
    )

    op.create_index("ix_appointments_doctor_id", "appointments", ["doctor_id"])
    op.create_index("ix_appointments_status", "appointments", ["appointment_status"])
    op.create_index("ix_appointments_created_at", "appointments", ["created_at"])


def downgrade():
    op.drop_index("ix_appointments_created_at", table_name="appointments")
    op.drop_index("ix_appointments_status", table_name="appointments")
    op.drop_index("ix_appointments_doctor_id", table_name="appointments")
    op.drop_table("appointments")
    op.drop_table("contact_messages")
    op.drop_table("admin_users")
    op.drop_table("doctors")
