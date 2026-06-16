"""add missing event columns

Revision ID: d2f3a4b5c6e7
Revises: c1e2f3a4b5d6
Create Date: 2026-06-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "d2f3a4b5c6e7"
down_revision = "c1e2f3a4b5d6"
branch_labels = None
depends_on = None

_EXPECTED_COLUMNS = {
    "cctv_name":        lambda: op.add_column("events", sa.Column("cctv_name", sa.String(200), nullable=True)),
    "location_name":    lambda: op.add_column("events", sa.Column("location_name", sa.String(200), nullable=True)),
    "detected_at":      lambda: op.add_column("events", sa.Column("detected_at", sa.DateTime, nullable=True)),
    "risk_score":       lambda: op.add_column("events", sa.Column("risk_score", sa.Integer, nullable=True, server_default="0")),
    "risk_candidate":   lambda: op.add_column("events", sa.Column("risk_candidate", sa.Boolean, nullable=True, server_default=sa.text("1"))),
    "is_fire":          lambda: op.add_column("events", sa.Column("is_fire", sa.Boolean, nullable=True)),
    "vlm_reason":       lambda: op.add_column("events", sa.Column("vlm_reason", sa.Text, nullable=True)),
    "detected_classes": lambda: op.add_column("events", sa.Column("detected_classes", sa.JSON, nullable=True)),
    "snapshot_key":     lambda: op.add_column("events", sa.Column("snapshot_key", sa.String(500), nullable=True)),
    "created_at":       lambda: op.add_column("events", sa.Column("created_at", sa.DateTime, nullable=True, server_default=sa.text("NOW()"))),
}


def upgrade():
    inspector = sa.inspect(op.get_bind())
    if "events" not in inspector.get_table_names():
        return

    existing = {c["name"] for c in inspector.get_columns("events")}
    for col_name, add_fn in _EXPECTED_COLUMNS.items():
        if col_name not in existing:
            add_fn()


def downgrade():
    pass
