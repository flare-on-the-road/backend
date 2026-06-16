"""recreate events table with correct schema

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-06-16 00:00:00.000000

기존 events 테이블은 cctv_id가 INT(FK) 등 스키마가 달라 재생성.
"""
from alembic import op
import sqlalchemy as sa


revision = "f4a5b6c7d8e9"
down_revision = "e3f4a5b6c7d8"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "events" in inspector.get_table_names():
        # FK 제약 먼저 제거
        fks = inspector.get_foreign_keys("events")
        for fk in fks:
            if fk.get("name"):
                op.drop_constraint(fk["name"], "events", type_="foreignkey")
        op.drop_table("events")

    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("cctv_id", sa.String(100), nullable=False),
        sa.Column("cctv_name", sa.String(200), nullable=False),
        sa.Column("location_name", sa.String(200), nullable=False),
        sa.Column("detected_at", sa.DateTime, nullable=False),
        sa.Column("risk_score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("risk_candidate", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("is_fire", sa.Boolean, nullable=True),
        sa.Column("vlm_reason", sa.Text, nullable=True),
        sa.Column("detected_classes", sa.JSON, nullable=True),
        sa.Column("snapshot_key", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_index("ix_events_cctv_id", "events", ["cctv_id"])
    op.create_index("ix_events_detected_at", "events", ["detected_at"])
    op.create_index("ix_events_is_fire", "events", ["is_fire"])
    op.create_index("ix_events_cctv_id_detected_at", "events", ["cctv_id", "detected_at"])


def downgrade():
    op.drop_table("events")
