from datetime import datetime

from app.extensions import db


class Comment(db.Model):
    __tablename__ = "comments"
    __table_args__ = (
        db.Index("ix_comments_post_parent_created", "post_id", "parent_id", "created_at"),
    )

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )

    post_id = db.Column(
        db.BigInteger,
        db.ForeignKey("posts.id"),
        nullable=False,
        index=True,
    )

    # users.id is Integer; FK 컬럼 타입을 맞춰야 함
    author_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
    )

    parent_id = db.Column(
        db.BigInteger,
        db.ForeignKey("comments.id"),
        nullable=True,
    )

    content = db.Column(db.String(1000), nullable=False)

    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    is_hidden = db.Column(db.Boolean, nullable=False, default=False)
    hidden_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    hidden_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    author = db.relationship("User", foreign_keys=[author_id])
    parent = db.relationship("Comment", remote_side=[id], backref="replies")
