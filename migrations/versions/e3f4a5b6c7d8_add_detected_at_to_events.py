"""add detected_at to events

Revision ID: e3f4a5b6c7d8
Revises: d2f3a4b5c6e7
Create Date: 2026-06-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "e3f4a5b6c7d8"
down_revision = "d2f3a4b5c6e7"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    if "events" not in inspector.get_table_names():
        return
    existing = {c["name"] for c in inspector.get_columns("events")}
    if "detected_at" not in existing:
        op.add_column("events", sa.Column("detected_at", sa.DateTime, nullable=True))


def downgrade():
    pass
