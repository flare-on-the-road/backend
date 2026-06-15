"""add events table

Revision ID: c1e2f3a4b5d6
Revises: b3f1a9c7d2e4
Create Date: 2026-06-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "c1e2f3a4b5d6"
down_revision = "b3f1a9c7d2e4"
branch_labels = None
depends_on = None


def upgrade():
    if _has_table("events"):
        return

    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer, "sqlite"), primary_key=True, autoincrement=True),
        sa.Column("cctv_id", sa.String(100), nullable=False),
        sa.Column("cctv_name", sa.String(200), nullable=False),
        sa.Column("location_name", sa.String(200), nullable=False),
        sa.Column("detected_at", sa.DateTime, nullable=False),
        sa.Column("risk_score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("risk_candidate", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("is_fire", sa.Boolean, nullable=True),
        sa.Column("vlm_reason", sa.Text, nullable=True),
        sa.Column("detected_classes", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("snapshot_key", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_index("ix_events_cctv_id", "events", ["cctv_id"])
    op.create_index("ix_events_detected_at", "events", ["detected_at"])
    op.create_index("ix_events_is_fire", "events", ["is_fire"])
    op.create_index("ix_events_cctv_id_detected_at", "events", ["cctv_id", "detected_at"])


def downgrade():
    if not _has_table("events"):
        return

    op.drop_index("ix_events_cctv_id_detected_at", table_name="events")
    op.drop_index("ix_events_is_fire", table_name="events")
    op.drop_index("ix_events_detected_at", table_name="events")
    op.drop_index("ix_events_cctv_id", table_name="events")
    op.drop_table("events")


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(table_name):
    return table_name in _inspector().get_table_names()
