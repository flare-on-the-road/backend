"""add visits table

Revision ID: j8d9e0f1a2b3
Revises: i7c8d9e0f1a2
Create Date: 2026-07-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "j8d9e0f1a2b3"
down_revision = "i7c8d9e0f1a2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "visits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("visitor_key", sa.String(length=100), nullable=False),
        sa.Column("visit_date", sa.Date(), nullable=False),
        sa.Column("path", sa.String(length=500), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("ip_address", sa.String(length=100), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("visitor_key", "visit_date", name="uq_visits_visitor_date"),
    )
    op.create_index(op.f("ix_visits_visit_date"), "visits", ["visit_date"], unique=False)
    op.create_index(op.f("ix_visits_visitor_key"), "visits", ["visitor_key"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_visits_visitor_key"), table_name="visits")
    op.drop_index(op.f("ix_visits_visit_date"), table_name="visits")
    op.drop_table("visits")
