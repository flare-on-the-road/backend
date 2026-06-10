"""add files and profile image

Revision ID: 7714c0501d92
Revises: 4ddb6ddd9342
Create Date: 2026-06-10 13:43:12.048721

"""
from alembic import op
import sqlalchemy as sa


revision = "7714c0501d92"
down_revision = "4ddb6ddd9342"
branch_labels = None
depends_on = None


def upgrade():
    if not _has_table("files"):
        op.create_table(
            "files",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("owner_user_id", sa.Integer(), nullable=True),
            sa.Column("original_filename", sa.String(length=255), nullable=False),
            sa.Column("stored_filename", sa.String(length=255), nullable=False),
            sa.Column(
                "storage_provider",
                sa.String(length=30),
                nullable=False,
                server_default="cloudflare_r2",
            ),
            sa.Column("bucket", sa.String(length=255), nullable=False),
            sa.Column("object_key", sa.String(length=500), nullable=False),
            sa.Column("public_url", sa.String(length=1000), nullable=True),
            sa.Column("content_type", sa.String(length=120), nullable=False),
            sa.Column("byte_size", sa.Integer(), nullable=False),
            sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
            sa.Column("purpose", sa.String(length=50), nullable=False),
            sa.Column("entity_type", sa.String(length=50), nullable=True),
            sa.Column("entity_id", sa.String(length=80), nullable=True),
            sa.Column(
                "status",
                sa.String(length=20),
                nullable=False,
                server_default="active",
            ),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.ForeignKeyConstraint(
                ["owner_user_id"],
                ["users.id"],
                name="fk_files_owner_user_id",
                ondelete="SET NULL",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("object_key", name="uq_files_object_key"),
            mysql_charset="utf8mb4",
            mysql_collate="utf8mb4_unicode_ci",
            mysql_engine="InnoDB",
        )

    _create_index_if_missing("files", "ix_files_owner_user_id", ["owner_user_id"])
    _create_index_if_missing("files", "ix_files_purpose", ["purpose"])
    _create_index_if_missing("files", "ix_files_entity_type", ["entity_type"])
    _create_index_if_missing("files", "ix_files_entity_id", ["entity_id"])

    if not _has_column("users", "profile_image_file_id"):
        op.add_column(
            "users",
            sa.Column("profile_image_file_id", sa.Integer(), nullable=True),
        )

    _create_index_if_missing(
        "users",
        "ix_users_profile_image_file_id",
        ["profile_image_file_id"],
    )

    if not _has_foreign_key("users", "fk_users_profile_image_file_id"):
        op.create_foreign_key(
            "fk_users_profile_image_file_id",
            "users",
            "files",
            ["profile_image_file_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade():
    if _has_foreign_key("users", "fk_users_profile_image_file_id"):
        op.drop_constraint(
            "fk_users_profile_image_file_id",
            "users",
            type_="foreignkey",
        )

    if _has_index("users", "ix_users_profile_image_file_id"):
        op.drop_index("ix_users_profile_image_file_id", table_name="users")

    if _has_column("users", "profile_image_file_id"):
        op.drop_column("users", "profile_image_file_id")

    if _has_table("files"):
        op.drop_table("files")


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


def _has_foreign_key(table_name, constraint_name):
    if not _has_table(table_name):
        return False

    return any(
        foreign_key["name"] == constraint_name
        for foreign_key in _inspector().get_foreign_keys(table_name)
    )


def _create_index_if_missing(table_name, index_name, columns):
    if not _has_index(table_name, index_name):
        op.create_index(index_name, table_name, columns)
