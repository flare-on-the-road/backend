from datetime import datetime

from app.extensions import db


class Event(db.Model):
    __tablename__ = "events"
    __table_args__ = (
        db.Index("ix_events_cctv_id_detected_at", "cctv_id", "detected_at"),
        db.Index("ix_events_detected_at", "detected_at"),
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

    # VLM 2차 판단 결과: 항목별 오탐 여부 [{"class_name": str, "is_false_positive": bool, "reason": str}]
    vlm_results = db.Column(db.JSON, nullable=True)

    # RT-DETRv2 탐지 결과 (JSON array: [{"label": "fire", "confidence": 0.75, "bbox": [...]}])
    detections = db.Column(db.JSON, nullable=False, default=list)

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
            "vlmResults": self.vlm_results or [],
            "detections": self.detections or [],
            "snapshotKey": self.snapshot_key,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
