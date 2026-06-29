"""add vlm_results column to events

Revision ID: g5a6b7c8d9e0
Revises: f4a5b6c7d8e9
Create Date: 2026-06-29

VLM 판단 구조를 이진(is_fire) → per-detection 다중 분류로 전환.
vlm_reason(Text) 제거, vlm_results(JSON) 추가.
각 항목: {"class_name": str, "is_false_positive": bool, "reason": str}
"""
from alembic import op
import sqlalchemy as sa


revision = "g5a6b7c8d9e0"
down_revision = "f4a5b6c7d8e9"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {c["name"] for c in inspector.get_columns("events")}

    if "vlm_results" not in columns:
        op.add_column("events", sa.Column("vlm_results", sa.JSON, nullable=True))

    if "vlm_reason" in columns:
        op.drop_column("events", "vlm_reason")


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {c["name"] for c in inspector.get_columns("events")}

    if "vlm_reason" not in columns:
        op.add_column("events", sa.Column("vlm_reason", sa.Text, nullable=True))

    if "vlm_results" in columns:
        op.drop_column("events", "vlm_results")
