from flask_jwt_extended import create_access_token, create_refresh_token
from app.common.constants import UserRole, AuthProvider
from app.repositories import user_repository


def create_access(user):
    return create_access_token(
        identity=str(user.id),
        additional_claims={
            "email": user.email,
            "name": user.name,
            "role": user.role,
        },
    )


def create_refresh(user):
    return create_refresh_token(
        identity=str(user.id),
        additional_claims={
            "email": user.email,
            "role": user.role,
        },
    )


def create_token_pair(user):
    return {
        "accessToken": create_access(user),
        "refreshToken": create_refresh(user),
        "user": user.to_dict(),
    }


# 기존 oauth_service.py에서 create_token을 import하고 있으므로 호환용으로 유지
def create_token(user):
    return create_access(user)


def register_user(email, name, password, department=None, phone=None):
    exists = user_repository.find_by_email(email)
    if exists:
        raise ValueError("이미 가입된 이메일입니다.")

    user = user_repository.create_user(
        email=email,
        name=name,
        password=password,
        role=UserRole.VIEWER,
        provider=AuthProvider.LOCAL,
        department=department,
        phone=phone,
    )

    return create_token_pair(user)


def login_user(email, password):
    user = user_repository.find_by_email(email)

    if not user:
        raise ValueError("가입되지 않은 이메일입니다.")

    if not user.check_password(password):
        raise ValueError("비밀번호가 올바르지 않습니다.")

    if not user.is_active:
        raise ValueError("비활성화된 계정입니다.")

    return create_token_pair(user)


def refresh_access_token(user_id):
    user = user_repository.find_by_id(user_id)

    if not user:
        raise ValueError("사용자를 찾을 수 없습니다.")

    if not user.is_active:
        raise ValueError("비활성화된 계정입니다.")

    return {
        "accessToken": create_access(user),
    }


def get_current_user(user_id):
    user = user_repository.find_by_id(user_id)

    if not user:
        raise ValueError("사용자를 찾을 수 없습니다.")

    return user.to_dict()