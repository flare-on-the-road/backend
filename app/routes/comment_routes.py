from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.common.decorators import get_current_role, get_current_user_id
from app.services import comment_service

comment_bp = Blueprint("comments", __name__)


@comment_bp.get("/posts/<int:post_id>/comments")
@jwt_required()
def get_comments(post_id):
    """
    댓글 트리 조회
    ---
    tags:
      - Comments
    summary: 게시글의 댓글을 트리 구조로 조회
    security:
      - Bearer: []
    parameters:
      - in: path
        name: post_id
        type: integer
        required: true
    responses:
      200:
        description: 댓글 트리
      403:
        description: 가려진 게시물 접근 (FORBIDDEN)
      404:
        description: 게시물 없음 (POST_NOT_FOUND)
    """
    user_id = get_current_user_id()
    role = get_current_role()

    result = comment_service.get_comment_tree(post_id, user_id, role)
    return jsonify(result)


@comment_bp.post("/posts/<int:post_id>/comments")
@jwt_required()
def create_comment(post_id):
    """
    댓글/대댓글 작성
    ---
    tags:
      - Comments
    summary: 댓글 또는 대댓글 작성 (대댓글은 깊이 2단계까지)
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
            - content
          properties:
            content:
              type: string
              example: 저도 재현됩니다
            parent_id:
              type: integer
              description: 대댓글일 경우 부모 댓글 id
    responses:
      201:
        description: 작성 성공
      400:
        description: 입력값 검증 실패 (VALIDATION_ERROR) / 깊이 초과 (MAX_DEPTH_EXCEEDED) / 잘못된 부모 댓글 (INVALID_PARENT)
      403:
        description: 가려진 게시물 접근 (FORBIDDEN)
      404:
        description: 게시물 없음 (POST_NOT_FOUND)
    """
    user_id = get_current_user_id()
    role = get_current_role()
    body = request.get_json() or {}

    result = comment_service.create_comment(post_id, user_id, role, body)
    return jsonify(result), 201


@comment_bp.put("/comments/<int:comment_id>")
@jwt_required()
def update_comment(comment_id):
    """
    댓글 수정
    ---
    tags:
      - Comments
    summary: 댓글 수정 (작성자 본인만)
    security:
      - Bearer: []
    parameters:
      - in: path
        name: comment_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - content
          properties:
            content:
              type: string
    responses:
      200:
        description: 수정 성공
      400:
        description: 입력값 검증 실패 (VALIDATION_ERROR)
      403:
        description: 작성자가 아니거나 가려진 댓글 (FORBIDDEN)
      404:
        description: 댓글 없음 (COMMENT_NOT_FOUND)
    """
    user_id = get_current_user_id()
    body = request.get_json() or {}

    result = comment_service.update_comment(comment_id, user_id, body)
    return jsonify(result)


@comment_bp.delete("/comments/<int:comment_id>")
@jwt_required()
def delete_comment(comment_id):
    """
    댓글 삭제 (soft delete)
    ---
    tags:
      - Comments
    summary: 댓글 삭제 (작성자 본인만, soft delete)
    security:
      - Bearer: []
    parameters:
      - in: path
        name: comment_id
        type: integer
        required: true
    responses:
      200:
        description: 삭제 성공
      403:
        description: 작성자가 아니거나 가려진 댓글 (FORBIDDEN)
      404:
        description: 댓글 없음 (COMMENT_NOT_FOUND)
    """
    user_id = get_current_user_id()

    comment_service.delete_comment(comment_id, user_id)
    return jsonify({"id": comment_id})


@comment_bp.patch("/comments/<int:comment_id>/hide")
@jwt_required()
def hide_comment(comment_id):
    """
    댓글 가리기 (관리자)
    ---
    tags:
      - Comments
    summary: 댓글 가리기 (ADMIN)
    security:
      - Bearer: []
    parameters:
      - in: path
        name: comment_id
        type: integer
        required: true
    responses:
      200:
        description: 가리기 성공
      403:
        description: 관리자 권한 필요 (FORBIDDEN)
      404:
        description: 댓글 없음 (COMMENT_NOT_FOUND)
    """
    role = get_current_role()
    admin_id = get_current_user_id()

    comment_service.hide_comment(comment_id, role, admin_id)
    return jsonify({"id": comment_id, "is_hidden": True})


@comment_bp.patch("/comments/<int:comment_id>/unhide")
@jwt_required()
def unhide_comment(comment_id):
    """
    댓글 가리기 해제 (관리자)
    ---
    tags:
      - Comments
    summary: 댓글 가리기 해제 (ADMIN)
    security:
      - Bearer: []
    parameters:
      - in: path
        name: comment_id
        type: integer
        required: true
    responses:
      200:
        description: 가리기 해제 성공
      403:
        description: 관리자 권한 필요 (FORBIDDEN)
      404:
        description: 댓글 없음 (COMMENT_NOT_FOUND)
    """
    role = get_current_role()

    comment_service.unhide_comment(comment_id, role)
    return jsonify({"id": comment_id, "is_hidden": False})
