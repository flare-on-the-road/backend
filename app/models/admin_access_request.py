from datetime import datetime

from app.extensions import db
from app.common.constants import AdminAccessRequestStatus


class AdminAccessRequest(db.Model):
    __tablename__ = "admin_access_requests"

    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    status = db.Column(
        db.String(20),
        nullable=False,
        default=AdminAccessRequestStatus.PENDING,
        index=True,
    )
    reason = db.Column(db.String(500), nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    requester = db.relationship("User", foreign_keys=[requester_id])
    reviewer = db.relationship("User", foreign_keys=[reviewed_by])
