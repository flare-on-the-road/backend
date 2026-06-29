"""drop risk_score/risk_candidate, rename detected_classes to detections

Revision ID: a1b2c3d4e5f6
Revises: f4a5b6c7d8e9
Create Date: 2026-06-29

변경 내용:
  - events.risk_score 컬럼 삭제
  - events.risk_candidate 컬럼 삭제
  - events.detected_classes 컬럼 → detections 으로 이름 변경
    (포맷 변경: ["fire"] → [{"label": "fire", "confidence": 0.75, "bbox": [...]}])
"""
from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "f4a5b6c7d8e9"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("events", "risk_score")
    op.drop_column("events", "risk_candidate")
    op.alter_column(
        "events",
        "detected_classes",
        new_column_name="detections",
        existing_type=sa.JSON(),
        existing_nullable=False,
    )


def downgrade():
    op.alter_column(
        "events",
        "detections",
        new_column_name="detected_classes",
        existing_type=sa.JSON(),
        existing_nullable=False,
    )
    op.add_column(
        "events",
        sa.Column("risk_candidate", sa.Boolean(), nullable=False, server_default=sa.text("1")),
    )
    op.add_column(
        "events",
        sa.Column("risk_score", sa.Integer(), nullable=False, server_default="0"),
    )
