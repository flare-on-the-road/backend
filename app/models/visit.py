from datetime import date, datetime

from app.extensions import db


class Visit(db.Model):
    __tablename__ = "visits"
    __table_args__ = (
        db.UniqueConstraint("visitor_key", "visit_date", name="uq_visits_visitor_date"),
        db.Index("ix_visits_visit_date", "visit_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    visitor_key = db.Column(db.String(100), nullable=False, index=True)
    visit_date = db.Column(db.Date, nullable=False, default=date.today)
    path = db.Column(db.String(500), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    ip_address = db.Column(db.String(100), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", foreign_keys=[user_id])
