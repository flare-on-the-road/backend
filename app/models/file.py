from datetime import datetime

from app.common.constants import FileStatus
from app.extensions import db


class File(db.Model):
    __tablename__ = "files"

    id = db.Column(db.Integer, primary_key=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    storage_provider = db.Column(db.String(30), nullable=False, default="cloudflare_r2")
    bucket = db.Column(db.String(255), nullable=False)
    object_key = db.Column(db.String(500), nullable=False, unique=True, index=True)
    public_url = db.Column(db.String(1000), nullable=True)
    content_type = db.Column(db.String(120), nullable=False)
    byte_size = db.Column(db.Integer, nullable=False)
    checksum_sha256 = db.Column(db.String(64), nullable=False)
    purpose = db.Column(db.String(50), nullable=False, index=True)
    entity_type = db.Column(db.String(50), nullable=True, index=True)
    entity_id = db.Column(db.String(80), nullable=True, index=True)
    status = db.Column(db.String(20), nullable=False, default=FileStatus.ACTIVE)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    owner = db.relationship(
        "User",
        foreign_keys=[owner_user_id],
        back_populates="owned_files",
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "ownerUserId": str(self.owner_user_id) if self.owner_user_id else None,
            "originalFilename": self.original_filename,
            "storedFilename": self.stored_filename,
            "storageProvider": self.storage_provider,
            "bucket": self.bucket,
            "objectKey": self.object_key,
            "publicUrl": self.public_url,
            "contentType": self.content_type,
            "byteSize": self.byte_size,
            "checksumSha256": self.checksum_sha256,
            "purpose": self.purpose,
            "entityType": self.entity_type,
            "entityId": self.entity_id,
            "status": self.status,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
