from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.common.constants import PostBoardType
from app.common.decorators import get_current_role, get_current_user_id
from app.services import post_like_service, post_service

post_bp = Blueprint("posts", __name__)


@post_bp.get("")
@jwt_required()
def list_posts():
    """
    게시글 목록 조회
    ---
    tags:
      - Posts
    summary: 게시글 목록 조회 (페이지네이션 + 검색)
    security:
      - Bearer: []
    parameters:
      - in: query
        name: page
        type: integer
        default: 1
      - in: query
        name: size
        type: integer
        default: 10
        description: 최대 50, 초과 시 50으로 클램프
      - in: query
        name: keyword
        type: string
        description: 검색어 (공백이면 검색 미적용)
      - in: query
        name: search_type
        type: string
        enum: [title, content, title_content, author]
        default: title
      - in: query
        name: board_type
        type: string
        enum: [bug, notice, inquiry]
        default: bug
    responses:
      200:
        description: 게시글 목록
      401:
        description: 인증 필요 (AUTH_REQUIRED)
    """
    user_id = get_current_user_id()
    role = get_current_role()

    page = request.args.get("page", default=1, type=int)
    size = request.args.get("size", default=10, type=int)
    keyword = request.args.get("keyword")
    search_type = request.args.get("search_type")
    board_type = request.args.get("board_type", default=PostBoardType.BUG)

    result = post_service.list_posts(
        user_id, role, page, size, keyword, search_type, board_type
    )
    return jsonify(result)


@post_bp.get("/<int:post_id>")
@jwt_required()
def get_post(post_id):
    """
    게시글 상세 조회
    ---
    tags:
      - Posts
    summary: 게시글 상세 조회 (조회수 +1)
    security:
      - Bearer: []
    parameters:
      - in: path
        name: post_id
        type: integer
        required: true
    responses:
      200:
        description: 게시글 상세
      403:
        description: 가려진 게시물 접근 (FORBIDDEN)
      404:
        description: 게시물 없음 (POST_NOT_FOUND)
    """
    user_id = get_current_user_id()
    role = get_current_role()

    result = post_service.get_post_detail(post_id, user_id, role)
    return jsonify(result)


@post_bp.post("")
@jwt_required()
def create_post():
    """
    게시글 작성
    ---
    tags:
      - Posts
    summary: 게시글 작성
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - title
            - content
          properties:
            title:
              type: string
              example: 로그인 후 새로고침하면 토큰 날아감
            content:
              type: string
              example: 재현 경로 ...
            board_type:
              type: string
              enum: [bug, notice, inquiry]
              default: bug
            is_important:
              type: boolean
              description: 공지사항(admin)만 적용
      - in: formData
        name: attachments
        type: file
        required: false
        description: 첨부 이미지 (jpg/png/webp/gif, 최대 2개, multipart/form-data 전용)
    responses:
      201:
        description: 작성 성공
      400:
        description: 입력값 검증 실패 (VALIDATION_ERROR)
      403:
        description: 게시판 작성 권한 없음 (FORBIDDEN)
    """
    user_id = get_current_user_id()
    role = get_current_role()

    if request.content_type and request.content_type.startswith("multipart/form-data"):
        body = request.form.to_dict()
        files = request.files.getlist("attachments")
    else:
        body = request.get_json() or {}
        files = []

    result = post_service.create_post(user_id, role, body, files)
    return jsonify(result), 201


@post_bp.put("/<int:post_id>")
@jwt_required()
def update_post(post_id):
    """
    게시글 수정
    ---
    tags:
      - Posts
    summary: 게시글 수정 (작성자 본인만)
    security:
      - Bearer: []
    parameters:
      - in: path
        name: post_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - title
            - content
          properties:
            title:
              type: string
            content:
              type: string
            is_important:
              type: boolean
              description: 공지사항(admin)만 적용
      - in: formData
        name: attachments
        type: file
        required: false
        description: 새로 추가할 첨부 이미지 (jpg/png/webp/gif, multipart/form-data 전용)
      - in: formData
        name: removed_file_ids
        type: array
        items:
          type: integer
        required: false
        description: 삭제할 기존 첨부파일 id (반복 가능, multipart/form-data 전용)
    responses:
      200:
        description: 수정 성공
      400:
        description: 입력값 검증 실패 (VALIDATION_ERROR)
      403:
        description: 작성자가 아니거나 가려진 게시물 (FORBIDDEN)
      404:
        description: 게시물 없음 (POST_NOT_FOUND)
    """
    user_id = get_current_user_id()
    role = get_current_role()

    if request.content_type and request.content_type.startswith("multipart/form-data"):
        body = request.form.to_dict()
        files = request.files.getlist("attachments")
        removed_file_ids = [int(v) for v in request.form.getlist("removed_file_ids")]
    else:
        body = request.get_json() or {}
        files = []
        removed_file_ids = body.get("removed_file_ids") or []

    result = post_service.update_post(post_id, user_id, role, body, files, removed_file_ids)
    return jsonify(result)


@post_bp.delete("/<int:post_id>")
@jwt_required()
def delete_post(post_id):
    """
    게시글 삭제 (soft delete)
    ---
    tags:
      - Posts
    summary: 게시글 삭제 (작성자 본인만, soft delete)
    security:
      - Bearer: []
    parameters:
      - in: path
        name: post_id
        type: integer
        required: true
    responses:
      200:
        description: 삭제 성공
      403:
        description: 작성자가 아니거나 가려진 게시물 (FORBIDDEN)
      404:
        description: 게시물 없음 (POST_NOT_FOUND)
    """
    user_id = get_current_user_id()
    role = get_current_role()

    post_service.delete_post(post_id, user_id, role)
    return jsonify({"id": post_id})


@post_bp.patch("/<int:post_id>/hide")
@jwt_required()
def hide_post(post_id):
    """
    게시글 가리기 (관리자)
    ---
    tags:
      - Posts
    summary: 게시글 가리기 (ADMIN)
    security:
      - Bearer: []
    parameters:
      - in: path
        name: post_id
        type: integer
        required: true
    responses:
      200:
        description: 가리기 성공
      403:
        description: 관리자 권한 필요 (FORBIDDEN)
      404:
        description: 게시물 없음 (POST_NOT_FOUND)
    """
    role = get_current_role()
    admin_id = get_current_user_id()

    post_service.hide_post(post_id, role, admin_id)
    return jsonify({"id": post_id, "is_hidden": True})


@post_bp.patch("/<int:post_id>/unhide")
@jwt_required()
def unhide_post(post_id):
    """
    게시글 가리기 해제 (관리자)
    ---
    tags:
      - Posts
    summary: 게시글 가리기 해제 (ADMIN)
    security:
      - Bearer: []
    parameters:
      - in: path
        name: post_id
        type: integer
        required: true
    responses:
      200:
        description: 가리기 해제 성공
      403:
        description: 관리자 권한 필요 (FORBIDDEN)
      404:
        description: 게시물 없음 (POST_NOT_FOUND)
    """
    role = get_current_role()

    post_service.unhide_post(post_id, role)
    return jsonify({"id": post_id, "is_hidden": False})


@post_bp.post("/<int:post_id>/like")
@jwt_required()
def toggle_like(post_id):
    """
    게시글 좋아요 토글
    ---
    tags:
      - Posts
    summary: 좋아요 토글 (이미 눌렀으면 취소)
    security:
      - Bearer: []
    parameters:
      - in: path
        name: post_id
        type: integer
        required: true
    responses:
      200:
        description: 토글 결과 (liked, like_count)
      403:
        description: 가려진 게시물 (FORBIDDEN)
      404:
        description: 게시물 없음 (POST_NOT_FOUND)
    """
    user_id = get_current_user_id()
    role = get_current_role()

    result = post_like_service.toggle_like(post_id, user_id, role)
    return jsonify(result)
