"""add post board_type and is_important

Revision ID: b3f1a9c7d2e4
Revises: 7714c0501d92
Create Date: 2026-06-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b3f1a9c7d2e4"
down_revision = "7714c0501d92"
branch_labels = None
depends_on = None


def upgrade():
    if not _has_column("posts", "board_type"):
        op.add_column(
            "posts",
            sa.Column(
                "board_type",
                sa.String(length=20),
                nullable=False,
                server_default="bug",
            ),
        )

    if not _has_column("posts", "is_important"):
        op.add_column(
            "posts",
            sa.Column(
                "is_important",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            ),
        )

    _create_index_if_missing("posts", "ix_posts_board_type", ["board_type"])
    _create_index_if_missing(
        "posts",
        "ix_posts_board_type_is_deleted_created_at",
        ["board_type", "is_deleted", "created_at"],
    )


def downgrade():
    if _has_index("posts", "ix_posts_board_type_is_deleted_created_at"):
        op.drop_index("ix_posts_board_type_is_deleted_created_at", table_name="posts")

    if _has_index("posts", "ix_posts_board_type"):
        op.drop_index("ix_posts_board_type", table_name="posts")

    if _has_column("posts", "is_important"):
        op.drop_column("posts", "is_important")

    if _has_column("posts", "board_type"):
        op.drop_column("posts", "board_type")


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(table_name):
    return table_name in _inspector().get_table_names()


def _has_column(table_name, column_name):
    if not _has_table(table_name):
        return False

    return any(
        column["name"] == column_name
        for column in _inspector().get_columns(table_name)
    )


def _has_index(table_name, index_name):
    if not _has_table(table_name):
        return False

    return any(index["name"] == index_name for index in _inspector().get_indexes(table_name))


def _create_index_if_missing(table_name, index_name, columns):
    if not _has_index(table_name, index_name):
        op.create_index(index_name, table_name, columns)
