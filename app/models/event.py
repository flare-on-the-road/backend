from datetime import datetime

from app.extensions import db


class Event(db.Model):
    __tablename__ = "events"
    __table_args__ = (
        db.Index("ix_events_cctv_id_detected_at", "cctv_id", "detected_at"),
        db.Index("ix_events_detected_at", "detected_at"),
        db.Index("ix_events_is_fire", "is_fire"),
    )

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )

    cctv_id = db.Column(db.String(100), nullable=False, index=True)
    cctv_name = db.Column(db.String(200), nullable=False)
    location_name = db.Column(db.String(200), nullable=False)

    detected_at = db.Column(db.DateTime, nullable=False)

    risk_score = db.Column(db.Integer, nullable=False, default=0)
    risk_candidate = db.Column(db.Boolean, nullable=False, default=True)

    # VLM 2차 판단 결과 (미구현 시 NULL)
    is_fire = db.Column(db.Boolean, nullable=True)
    vlm_reason = db.Column(db.Text, nullable=True)

    # RT-DETRv2 탐지 클래스 목록 (JSON array: ["fire", "smoke"])
    detected_classes = db.Column(db.JSON, nullable=False, default=list)

    # Cloudflare R2 키 (예: "raw/20260615_120000_고덕터널.jpg")
    snapshot_key = db.Column(db.String(500), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "cctvId": self.cctv_id,
            "cctvName": self.cctv_name,
            "locationName": self.location_name,
            "detectedAt": self.detected_at.isoformat() if self.detected_at else None,
            "riskScore": self.risk_score,
            "riskCandidate": self.risk_candidate,
            "isFire": self.is_fire,
            "vlmReason": self.vlm_reason,
            "detectedClasses": self.detected_classes or [],
            "snapshotKey": self.snapshot_key,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
