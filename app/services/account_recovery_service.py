import secrets
import string

from app.common.constants import AuthProvider
from app.repositories import user_repository


def find_user_emails(name, phone):
    if not name:
        raise ValueError("이름을 입력해주세요.")

    if not phone:
        raise ValueError("전화번호를 입력해주세요.")

    users = user_repository.find_by_name_and_phone(name, phone)

    return {
        "accounts": [
            {
                "email": _mask_email(user.email),
                "provider": user.provider,
                "createdAt": user.created_at.isoformat() if user.created_at else None,
            }
            for user in users
        ],
    }


def reset_password(email, name, phone):
    if not email:
        raise ValueError("이메일을 입력해주세요.")

    if not name:
        raise ValueError("이름을 입력해주세요.")

    if not phone:
        raise ValueError("전화번호를 입력해주세요.")

    user = user_repository.find_by_email_name_and_phone(email, name, phone)

    if not user:
        raise ValueError("일치하는 계정을 찾을 수 없습니다.")

    if user.provider != AuthProvider.LOCAL:
        raise ValueError("소셜 로그인 계정은 해당 서비스에서 비밀번호를 변경해주세요.")

    temporary_password = _generate_temporary_password()
    user.set_password(temporary_password)
    user_repository.save(user)

    return {
        "temporaryPassword": temporary_password,
        "message": "임시 비밀번호가 발급되었습니다. 로그인 후 비밀번호를 변경해주세요.",
    }


def _generate_temporary_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _mask_email(email):
    local_part, _, domain = email.partition("@")

    if len(local_part) <= 2:
        masked_local = local_part[0] + "*"
    else:
        masked_local = local_part[:2] + "*" * max(1, len(local_part) - 2)

    return f"{masked_local}@{domain}"
