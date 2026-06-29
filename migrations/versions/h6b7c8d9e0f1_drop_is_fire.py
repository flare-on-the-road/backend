"""drop is_fire column from events

Revision ID: h6b7c8d9e0f1
Revises: g5a6b7c8d9e0
Create Date: 2026-06-29

is_fire 컬럼 제거. vlm_results 기반으로 화재 여부를 런타임에 파생하는 구조로 전환.
is_fire 컬럼이 완전히 불필요하다고 확인된 시점에 실행.
"""
from alembic import op
import sqlalchemy as sa


revision = "h6b7c8d9e0f1"
down_revision = "g5a6b7c8d9e0"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = {i["name"] for i in inspector.get_indexes("events")}
    columns = {c["name"] for c in inspector.get_columns("events")}

    if "ix_events_is_fire" in indexes:
        op.drop_index("ix_events_is_fire", table_name="events")

    if "is_fire" in columns:
        op.drop_column("events", "is_fire")


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {c["name"] for c in inspector.get_columns("events")}

    if "is_fire" not in columns:
        op.add_column("events", sa.Column("is_fire", sa.Boolean, nullable=True))
        op.create_index("ix_events_is_fire", "events", ["is_fire"])
