"""baseline: create base tables for fresh DB

Revision ID: 4ddb6ddd9342
Revises:
Create Date: 2026-06-10 13:42:53.087322

새 TiDB 인스턴스에서 flask db upgrade를 처음 실행할 때
users / posts / comments / post_likes / social_accounts 5개 기본 테이블을 생성한다.

이후 마이그레이션 체인:
  7714  → files 테이블 생성 + users.profile_image_file_id 추가
  b3f1  → posts.board_type / is_important 추가
  c1e2  → events 테이블 생성
  d2f3  → events 컬럼 추가
  e3f4  → events.detected_at 추가
  f4a5  → events 테이블 재생성 (최종 스키마)
"""
from alembic import op
import sqlalchemy as sa


revision = "4ddb6ddd9342"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = inspector.get_table_names()

    if "users" not in existing:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("email", sa.String(120), nullable=False),
            sa.Column("name", sa.String(50), nullable=False),
            sa.Column("password_hash", sa.String(255), nullable=True),
            sa.Column("role", sa.String(20), nullable=False, server_default="viewer"),
            sa.Column("provider", sa.String(20), nullable=False, server_default="local"),
            sa.Column("provider_user_id", sa.String(255), nullable=True),
            sa.Column("department", sa.String(100), nullable=True),
            sa.Column("phone", sa.String(50), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
            sa.UniqueConstraint("email", name="uq_users_email"),
            mysql_charset="utf8mb4",
            mysql_collate="utf8mb4_unicode_ci",
            mysql_engine="InnoDB",
        )
        op.create_index("ix_users_email", "users", ["email"], unique=True)

    if "posts" not in existing:
        op.create_table(
            "posts",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column("author_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(100), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("hidden_by", sa.Integer(), nullable=True),
            sa.Column("hidden_at", sa.DateTime(), nullable=True),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
            sa.ForeignKeyConstraint(["author_id"], ["users.id"], name="fk_posts_author_id"),
            sa.ForeignKeyConstraint(["hidden_by"], ["users.id"], name="fk_posts_hidden_by"),
            mysql_charset="utf8mb4",
            mysql_collate="utf8mb4_unicode_ci",
            mysql_engine="InnoDB",
        )
        op.create_index("ix_posts_author_id", "posts", ["author_id"])
        op.create_index("ix_posts_is_deleted", "posts", ["is_deleted"])
        op.create_index("ix_posts_is_deleted_created_at", "posts", ["is_deleted", "created_at"])

    if "comments" not in existing:
        op.create_table(
            "comments",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column("post_id", sa.BigInteger(), nullable=False),
            sa.Column("author_id", sa.Integer(), nullable=False),
            sa.Column("parent_id", sa.BigInteger(), nullable=True),
            sa.Column("content", sa.String(1000), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("hidden_by", sa.Integer(), nullable=True),
            sa.Column("hidden_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
            sa.ForeignKeyConstraint(["post_id"], ["posts.id"], name="fk_comments_post_id"),
            sa.ForeignKeyConstraint(["author_id"], ["users.id"], name="fk_comments_author_id"),
            sa.ForeignKeyConstraint(["parent_id"], ["comments.id"], name="fk_comments_parent_id"),
            sa.ForeignKeyConstraint(["hidden_by"], ["users.id"], name="fk_comments_hidden_by"),
            mysql_charset="utf8mb4",
            mysql_collate="utf8mb4_unicode_ci",
            mysql_engine="InnoDB",
        )
        op.create_index("ix_comments_post_id", "comments", ["post_id"])
        op.create_index("ix_comments_post_parent_created", "comments", ["post_id", "parent_id", "created_at"])

    if "post_likes" not in existing:
        op.create_table(
            "post_likes",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column("post_id", sa.BigInteger(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
            sa.ForeignKeyConstraint(["post_id"], ["posts.id"], name="fk_post_likes_post_id"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_post_likes_user_id"),
            sa.UniqueConstraint("post_id", "user_id", name="uq_post_likes_post_user"),
            mysql_charset="utf8mb4",
            mysql_collate="utf8mb4_unicode_ci",
            mysql_engine="InnoDB",
        )

    if "social_accounts" not in existing:
        op.create_table(
            "social_accounts",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("provider", sa.String(20), nullable=False),
            sa.Column("provider_user_id", sa.String(255), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_social_accounts_user_id"),
            mysql_charset="utf8mb4",
            mysql_collate="utf8mb4_unicode_ci",
            mysql_engine="InnoDB",
        )
        op.create_index("ix_social_accounts_user_id", "social_accounts", ["user_id"])


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = inspector.get_table_names()

    for table in ["social_accounts", "post_likes", "comments", "posts", "users"]:
        if table in existing:
            op.drop_table(table)
