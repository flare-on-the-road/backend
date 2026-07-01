from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app.common.decorators import admin_read_required, admin_required
from app.services import admin_service, post_service

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/summary")
@admin_read_required
def get_admin_summary():
    return jsonify(admin_service.get_summary())


@admin_bp.get("/users")
@admin_read_required
def list_admin_users():
    result = admin_service.list_users(
        page=request.args.get("page", default=1, type=int),
        size=request.args.get("size", default=10, type=int),
        keyword=request.args.get("keyword"),
        role=request.args.get("role"),
        active=request.args.get("active"),
        actor_role=get_jwt().get("role"),
    )
    return jsonify(result)


@admin_bp.post("/users")
@admin_required
def create_admin_user():
    body = request.get_json() or {}
    result = admin_service.create_user(body)
    return jsonify(result), 201


@admin_bp.get("/users/<int:user_id>")
@admin_required
def get_admin_user(user_id):
    return jsonify(admin_service.get_user(user_id))


@admin_bp.patch("/users/<int:user_id>")
@admin_required
def update_admin_user(user_id):
    body = request.get_json() or {}
    result = admin_service.update_user(
        user_id=user_id,
        data=body,
        actor_id=int(get_jwt_identity()),
    )
    return jsonify(result)


@admin_bp.delete("/users/<int:user_id>")
@admin_required
def deactivate_admin_user(user_id):
    result = admin_service.update_user_active(
        user_id=user_id,
        is_active=False,
        actor_id=int(get_jwt_identity()),
    )
    return jsonify(result)


@admin_bp.patch("/users/<int:user_id>/role")
@admin_required
def update_admin_user_role(user_id):
    body = request.get_json() or {}
    result = admin_service.update_user_role(
        user_id=user_id,
        role=body.get("role"),
        actor_id=int(get_jwt_identity()),
    )
    return jsonify(result)


@admin_bp.patch("/users/<int:user_id>/active")
@admin_required
def update_admin_user_active(user_id):
    body = request.get_json() or {}
    result = admin_service.update_user_active(
        user_id=user_id,
        is_active=body.get("is_active"),
        actor_id=int(get_jwt_identity()),
    )
    return jsonify(result)


@admin_bp.get("/posts")
@admin_read_required
def list_admin_posts():
    result = admin_service.list_posts(
        page=request.args.get("page", default=1, type=int),
        size=request.args.get("size", default=10, type=int),
        keyword=request.args.get("keyword"),
        board_type=request.args.get("board_type"),
        visibility=request.args.get("visibility"),
    )
    return jsonify(result)


@admin_bp.patch("/posts/<int:post_id>/hide")
@admin_required
def hide_admin_post(post_id):
    post_service.hide_post(post_id, "admin", int(get_jwt_identity()))
    return jsonify({"id": post_id, "is_hidden": True})


@admin_bp.patch("/posts/<int:post_id>/unhide")
@admin_required
def unhide_admin_post(post_id):
    post_service.unhide_post(post_id, "admin")
    return jsonify({"id": post_id, "is_hidden": False})


@admin_bp.get("/inquiries")
@admin_read_required
def list_admin_inquiries():
    result = admin_service.list_inquiries(
        page=request.args.get("page", default=1, type=int),
        size=request.args.get("size", default=10, type=int),
        keyword=request.args.get("keyword"),
        status=request.args.get("status"),
    )
    return jsonify(result)


@admin_bp.post("/inquiries/<int:post_id>/answer")
@admin_required
def answer_admin_inquiry(post_id):
    body = request.get_json() or {}
    result = admin_service.answer_inquiry(
        post_id=post_id,
        admin_id=int(get_jwt_identity()),
        content=body.get("content"),
    )
    return jsonify(result), 201


@admin_bp.get("/access-requests/me")
@jwt_required()
def get_my_admin_access_request():
    result = admin_service.get_my_access_request(int(get_jwt_identity()))
    return jsonify({"request": result})


@admin_bp.post("/access-requests")
@jwt_required()
def create_admin_access_request():
    body = request.get_json() or {}
    result = admin_service.create_access_request(
        user_id=int(get_jwt_identity()),
        reason=body.get("reason"),
    )
    return jsonify(result), 201


@admin_bp.get("/access-requests")
@admin_required
def list_admin_access_requests():
    result = admin_service.list_access_requests(
        page=request.args.get("page", default=1, type=int),
        size=request.args.get("size", default=10, type=int),
        status=request.args.get("status"),
    )
    return jsonify(result)


@admin_bp.patch("/access-requests/<int:request_id>")
@admin_required
def review_admin_access_request(request_id):
    body = request.get_json() or {}
    result = admin_service.review_access_request(
        request_id=request_id,
        status=body.get("status"),
        reviewer_id=int(get_jwt_identity()),
    )
    return jsonify(result)


@admin_bp.post("/public-viewer")
@admin_required
def ensure_public_admin_viewer():
    return jsonify(admin_service.ensure_public_admin_viewer()), 201
