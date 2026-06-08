from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt
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