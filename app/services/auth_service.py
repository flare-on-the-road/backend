from flask_jwt_extended import create_access_token, create_refresh_token
from app.common.constants import FilePurpose, FileStatus, UserRole, AuthProvider
from app.common.uploads import ALLOWED_IMAGE_CONTENT_TYPES, UploadContext, upload_file
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


def update_current_user(
    user_id,
    name=None,
    department=None,
    phone=None,
):
    user = user_repository.find_by_id(user_id)

    if not user:
        raise ValueError("사용자를 찾을 수 없습니다.")

    if not user.is_active:
        raise ValueError("비활성화된 계정입니다.")

    if name is not None:
        normalized_name = str(name).strip()

        if not normalized_name:
            raise ValueError("이름을 입력해주세요.")

        user.name = normalized_name

    if department is not None:
        normalized_department = str(department).strip()
        user.department = normalized_department or None

    if phone is not None:
        normalized_phone = str(phone).strip()
        user.phone = normalized_phone or None

    return user_repository.save(user).to_dict()


def update_current_user_profile_image(user_id, profile_image):
    user = user_repository.find_by_id(user_id)

    if not user:
        raise ValueError("사용자를 찾을 수 없습니다.")

    if not user.is_active:
        raise ValueError("비활성화된 계정입니다.")

    uploaded_file = upload_file(
        profile_image,
        UploadContext(
            purpose=FilePurpose.PROFILE_IMAGE,
            owner_user_id=user.id,
            entity_type="user",
            entity_id=user.id,
            directory="profiles",
            allowed_content_types=ALLOWED_IMAGE_CONTENT_TYPES,
        ),
    )

    if user.profile_image_file:
        user.profile_image_file.status = FileStatus.DELETED

    user.profile_image_file_id = uploaded_file.id
    user.profile_image_file = uploaded_file

    return user_repository.save(user).to_dict()


def change_current_user_password(
    user_id,
    current_password=None,
    new_password=None,
    new_password_confirm=None,
):
    user = user_repository.find_by_id(user_id)

    if not user:
        raise ValueError("사용자를 찾을 수 없습니다.")

    if not user.is_active:
        raise ValueError("비활성화된 계정입니다.")

    if not user.password_hash:
        raise ValueError("비밀번호 변경은 이메일 로그인 계정만 가능합니다.")

    normalized_current_password = str(current_password or "")
    normalized_new_password = str(new_password or "")
    normalized_new_password_confirm = str(new_password_confirm or "")

    if not normalized_current_password:
        raise ValueError("현재 비밀번호를 입력해주세요.")

    if not normalized_new_password:
        raise ValueError("새 비밀번호를 입력해주세요.")

    if len(normalized_new_password) < 8:
        raise ValueError("새 비밀번호는 8자 이상 입력해주세요.")

    if normalized_new_password != normalized_new_password_confirm:
        raise ValueError("새 비밀번호 확인이 일치하지 않습니다.")

    if not user.check_password(normalized_current_password):
        raise ValueError("현재 비밀번호가 올바르지 않습니다.")

    user.set_password(normalized_new_password)
    user_repository.save(user)

    return {"changed": True}
