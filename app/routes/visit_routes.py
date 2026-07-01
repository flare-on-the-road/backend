from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.common.response import fail
from app.services import visit_service

visit_bp = Blueprint("visit", __name__)


@visit_bp.post("")
def record_visit():
    body = request.get_json() or {}
    user_id = None

    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        user_id = int(identity) if identity else None
    except Exception:
        user_id = None

    try:
        result = visit_service.record_visit(
            visitor_key=body.get("visitorKey"),
            path=body.get("path"),
            user_id=user_id,
            ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
            user_agent=request.headers.get("User-Agent"),
        )
        return jsonify(result)
    except ValueError as exc:
        return fail(str(exc), 400)
