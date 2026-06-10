from flask import Blueprint, redirect

from app.common.constants import FileStatus
from app.common.response import fail
from app.common.uploads import create_presigned_download_url
from app.repositories import file_repository

file_bp = Blueprint("file", __name__)


@file_bp.get("/<int:file_id>/download")
def download_file(file_id):
    file = file_repository.find_by_id(file_id)

    if not file or file.status != FileStatus.ACTIVE:
        return fail("파일을 찾을 수 없습니다.", 404)

    if file.public_url:
        return redirect(file.public_url)

    try:
        return redirect(create_presigned_download_url(file.object_key))
    except Exception as e:
        return fail(str(e), 400)
