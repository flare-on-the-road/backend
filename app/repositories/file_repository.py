from app.common.constants import FileStatus
from app.extensions import db
from app.models.file import File


def find_by_id(file_id):
    return File.query.get(file_id)


def find_active_by_entity(entity_type, entity_id):
    return (
        File.query.filter_by(
            entity_type=entity_type,
            entity_id=str(entity_id),
            status=FileStatus.ACTIVE,
        )
        .order_by(File.id.asc())
        .all()
    )


def mark_deleted(file):
    # no commit: caller commits together with the related post change
    file.status = FileStatus.DELETED


def create_file(
    owner_user_id,
    original_filename,
    stored_filename,
    storage_provider,
    bucket,
    object_key,
    public_url,
    content_type,
    byte_size,
    checksum_sha256,
    purpose,
    entity_type=None,
    entity_id=None,
):
    file = File(
        owner_user_id=owner_user_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        storage_provider=storage_provider,
        bucket=bucket,
        object_key=object_key,
        public_url=public_url,
        content_type=content_type,
        byte_size=byte_size,
        checksum_sha256=checksum_sha256,
        purpose=purpose,
        entity_type=entity_type,
        entity_id=entity_id,
    )

    db.session.add(file)
    db.session.flush()

    return file


def save(file):
    db.session.add(file)
    db.session.commit()

    return file
