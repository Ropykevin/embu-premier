"""Add admin_notes and updated_at to appointments

Revision ID: 002_admin_notes
Revises: 001_initial
Create Date: 2026-07-05

"""
from alembic import op
import sqlalchemy as sa


revision = "002_admin_notes"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("appointments", sa.Column("admin_notes", sa.Text(), nullable=True))
    op.add_column("appointments", sa.Column("updated_at", sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column("appointments", "updated_at")
    op.drop_column("appointments", "admin_notes")
