from datetime import datetime

from app.common.constants import PostBoardType
from app.extensions import db


class Post(db.Model):
    __tablename__ = "posts"
    __table_args__ = (
        db.Index("ix_posts_is_deleted_created_at", "is_deleted", "created_at"),
        db.Index(
            "ix_posts_board_type_is_deleted_created_at",
            "board_type",
            "is_deleted",
            "created_at",
        ),
    )

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )

    # users.id is Integer; FK 컬럼 타입을 맞춰야 함
    author_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)

    board_type = db.Column(
        db.String(20),
        nullable=False,
        default=PostBoardType.BUG,
        index=True,
    )
    is_important = db.Column(db.Boolean, nullable=False, default=False)

    is_hidden = db.Column(db.Boolean, nullable=False, default=False)
    hidden_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    hidden_at = db.Column(db.DateTime, nullable=True)

    is_deleted = db.Column(db.Boolean, nullable=False, default=False, index=True)
    view_count = db.Column(db.Integer, nullable=False, default=0)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    author = db.relationship("User", foreign_keys=[author_id])
