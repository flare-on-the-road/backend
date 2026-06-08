from datetime import datetime

from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)

from app.extensions import db
from app.common.constants import UserRole, AuthProvider


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
        index=True,
    )

    name = db.Column(
        db.String(50),
        nullable=False,
    )

    password_hash = db.Column(
        db.String(255),
        nullable=True,
    )

    role = db.Column(
        db.String(20),
        nullable=False,
        default=UserRole.VIEWER,
    )

    provider = db.Column(
        db.String(20),
        nullable=False,
        default=AuthProvider.LOCAL,
    )

    provider_user_id = db.Column(
        db.String(255),
        nullable=True,
    )

    department = db.Column(
        db.String(100),
        nullable=True,
    )

    phone = db.Column(
        db.String(50),
        nullable=True,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def set_password(self, password):
        if password:
            self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False

        return check_password_hash(
            self.password_hash,
            password,
        )

    def to_dict(self):
        return {
            "id": str(self.id),
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "provider": self.provider,
            "department": self.department,
            "phone": self.phone,
            "isActive": self.is_active,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "lastLoginAt": None,
        }