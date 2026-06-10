import hashlib
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from flask import current_app
from PIL import Image, UnidentifiedImageError
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.repositories import file_repository

ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


@dataclass(frozen=True)
class UploadContext:
    purpose: str
    owner_user_id: int | str | None = None
    entity_type: str | None = None
    entity_id: int | str | None = None
    directory: str | None = None
    allowed_content_types: set[str] | None = None


def upload_file(file: FileStorage, context: UploadContext):
    if not file or not file.filename:
        raise ValueError("업로드할 파일을 선택해주세요.")

    content_type = file.mimetype or "application/octet-stream"
    allowed_content_types = context.allowed_content_types or ALLOWED_IMAGE_CONTENT_TYPES

    if content_type not in allowed_content_types:
        raise ValueError("지원하지 않는 파일 형식입니다.")

    file_bytes = file.read()
    max_upload_bytes = current_app.config["MAX_UPLOAD_BYTES"]

    if len(file_bytes) > max_upload_bytes:
        raise ValueError("업로드 가능한 파일 크기를 초과했습니다.")

    _validate_image_bytes(file_bytes, content_type)

    original_filename = secure_filename(file.filename) or "upload"
    extension = _get_extension(original_filename, content_type, allowed_content_types)
    stored_filename = f"{uuid4().hex}{extension}"
    object_key = _build_object_key(context, stored_filename)
    checksum_sha256 = hashlib.sha256(file_bytes).hexdigest()

    _upload_to_r2(
        object_key=object_key,
        file_bytes=file_bytes,
        content_type=content_type,
    )

    return file_repository.create_file(
        owner_user_id=context.owner_user_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        storage_provider="cloudflare_r2",
        bucket=current_app.config["CF_R2_BUCKET_NAME"],
        object_key=object_key,
        public_url=_build_public_url(object_key),
        content_type=content_type,
        byte_size=len(file_bytes),
        checksum_sha256=checksum_sha256,
        purpose=context.purpose,
        entity_type=context.entity_type,
        entity_id=str(context.entity_id) if context.entity_id is not None else None,
    )


def _upload_to_r2(object_key, file_bytes, content_type):
    client = _create_r2_client()

    client.put_object(
        Bucket=current_app.config["CF_R2_BUCKET_NAME"],
        Key=object_key,
        Body=file_bytes,
        ContentType=content_type,
    )


def create_presigned_download_url(object_key, expires_in=300):
    client = _create_r2_client()

    return client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": current_app.config["CF_R2_BUCKET_NAME"],
            "Key": object_key,
        },
        ExpiresIn=expires_in,
    )


def _create_r2_client():
    try:
        import boto3
        from botocore.client import Config as BotoConfig
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "R2 업로드를 사용하려면 backend 환경에 boto3를 설치해주세요."
        ) from exc

    endpoint_url = current_app.config["CF_R2_ENDPOINT_URL"]

    if not endpoint_url and current_app.config["CF_ACCOUNT_ID"]:
        endpoint_url = (
            f"https://{current_app.config['CF_ACCOUNT_ID']}.r2.cloudflarestorage.com"
        )

    required_values = {
        "CF_R2_ACCESS_KEY_ID": current_app.config["CF_R2_ACCESS_KEY_ID"],
        "CF_R2_SECRET_ACCESS_KEY": current_app.config["CF_R2_SECRET_ACCESS_KEY"],
        "CF_R2_BUCKET_NAME": current_app.config["CF_R2_BUCKET_NAME"],
        "CF_R2_ENDPOINT_URL or CF_ACCOUNT_ID": endpoint_url,
    }
    missing_keys = [key for key, value in required_values.items() if not value]

    if missing_keys:
        raise ValueError(f"R2 업로드 설정이 누락되었습니다: {', '.join(missing_keys)}")

    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=current_app.config["CF_R2_ACCESS_KEY_ID"],
        aws_secret_access_key=current_app.config["CF_R2_SECRET_ACCESS_KEY"],
        config=BotoConfig(signature_version="s3v4"),
        region_name="auto",
    )


def _build_object_key(context, stored_filename):
    directory = context.directory or context.purpose
    parts = [directory]

    if context.entity_type:
        parts.append(str(context.entity_type))

    if context.entity_id is not None:
        parts.append(str(context.entity_id))

    parts.append(stored_filename)

    return "/".join(_sanitize_key_part(part) for part in parts if part)


def _build_public_url(object_key):
    public_url = current_app.config["CF_R2_PUBLIC_URL"]

    if not public_url:
        return None

    return f"{public_url.rstrip('/')}/{object_key}"


def _get_extension(filename, content_type, allowed_content_types):
    extension = Path(filename).suffix.lower()

    if extension:
        return extension

    return allowed_content_types.get(content_type, "")


def _validate_image_bytes(file_bytes, content_type):
    if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        return

    try:
        Image.open(BytesIO(file_bytes)).verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("유효한 이미지 파일이 아닙니다.") from exc


def _sanitize_key_part(value):
    return str(value).strip().replace(" ", "-").replace("..", "")
