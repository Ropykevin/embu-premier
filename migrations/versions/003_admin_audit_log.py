"""Revisions

Revision ID: 003_audit_log
Revises: 002_admin_notes
Create Date: 2026-07-05

"""
from alembic import op
import sqlalchemy as sa

revision = "003_audit_log"
down_revision = "002_admin_notes"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "admin_audit_logs",
        sa.Column("log_id", sa.Integer(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=50), nullable=True),
        sa.Column("resource_id", sa.Integer(), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["admin_id"], ["admin_users.admin_id"]),
        sa.PrimaryKeyConstraint("log_id"),
    )


def downgrade():
    op.drop_table("admin_audit_logs")
