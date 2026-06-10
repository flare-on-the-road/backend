from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity
from app.common.constants import UserRole
from app.common.response import fail


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()

        if claims.get("role") != UserRole.ADMIN:
            return fail("관리자 권한이 필요합니다.", 403)

        return fn(*args, **kwargs)

    return wrapper


def get_current_user_id():
    return int(get_jwt_identity())


def get_current_role():
    return get_jwt().get("role")