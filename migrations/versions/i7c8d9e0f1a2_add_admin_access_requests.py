"""add admin access requests

Revision ID: i7c8d9e0f1a2
Revises: h6b7c8d9e0f1
Create Date: 2026-07-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from werkzeug.security import generate_password_hash


revision = "i7c8d9e0f1a2"
down_revision = "h6b7c8d9e0f1"
branch_labels = None
depends_on = None


PUBLIC_ADMIN_VIEWER_EMAIL = "public-admin-viewer@flare.local"


def upgrade():
    op.create_table(
        "admin_access_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("requester_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_admin_access_requests_requester_id"),
        "admin_access_requests",
        ["requester_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_admin_access_requests_status"),
        "admin_access_requests",
        ["status"],
        unique=False,
    )

    users = sa.table(
        "users",
        sa.column("email", sa.String),
        sa.column("name", sa.String),
        sa.column("password_hash", sa.String),
        sa.column("role", sa.String),
        sa.column("provider", sa.String),
        sa.column("department", sa.String),
        sa.column("is_active", sa.Boolean),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )
    bind = op.get_bind()
    exists = bind.execute(
        sa.text("SELECT 1 FROM users WHERE email = :email"),
        {"email": PUBLIC_ADMIN_VIEWER_EMAIL},
    ).first()
    if not exists:
        op.execute(
            users.insert().values(
                email=PUBLIC_ADMIN_VIEWER_EMAIL,
                name="공개 관리자 관전자",
                password_hash=generate_password_hash("PublicViewer123!"),
                role="admin_viewer",
                provider="local",
                department="Public",
                is_active=True,
                created_at=sa.func.now(),
                updated_at=sa.func.now(),
            )
        )


def downgrade():
    op.execute(
        sa.text("DELETE FROM users WHERE email = :email").bindparams(
            email=PUBLIC_ADMIN_VIEWER_EMAIL
        )
    )
    op.drop_index(op.f("ix_admin_access_requests_status"), table_name="admin_access_requests")
    op.drop_index(
        op.f("ix_admin_access_requests_requester_id"),
        table_name="admin_access_requests",
    )
    op.drop_table("admin_access_requests")
