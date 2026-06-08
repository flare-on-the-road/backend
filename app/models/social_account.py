from datetime import datetime

from app.extensions import db


class SocialAccount(db.Model):
    __tablename__ = "social_accounts"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    provider = db.Column(
        db.String(20),
        nullable=False,
    )

    provider_user_id = db.Column(
        db.String(255),
        nullable=False,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "social_accounts",
            lazy=True,
        ),
    )