from datetime import datetime

from app.extensions import db


class PostLike(db.Model):
    __tablename__ = "post_likes"
    __table_args__ = (
        db.UniqueConstraint("post_id", "user_id", name="uq_post_likes_post_user"),
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
    )

    # users.id is Integer; FK 컬럼 타입을 맞춰야 함
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
    )

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
