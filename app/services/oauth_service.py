import secrets
import requests
from flask import current_app
from urllib.parse import urlencode
from app.common.constants import UserRole, AuthProvider
from app.repositories import user_repository
from app.services.auth_service import create_token_pair


def get_oauth_login_url(provider):
    state = secrets.token_urlsafe(16)

    if provider == "google":
        query = urlencode({
            "client_id": current_app.config["GOOGLE_CLIENT_ID"],
            "redirect_uri": current_app.config["GOOGLE_REDIRECT_URI"],
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
        })
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"

    if provider == "naver":
        query = urlencode({
            "client_id": current_app.config["NAVER_CLIENT_ID"],
            "redirect_uri": current_app.config["NAVER_REDIRECT_URI"],
            "response_type": "code",
            "state": state,
        })
        return f"https://nid.naver.com/oauth2.0/authorize?{query}"

    if provider == "kakao":
        query = urlencode({
            "client_id": current_app.config["KAKAO_CLIENT_ID"],
            "redirect_uri": current_app.config["KAKAO_REDIRECT_URI"],
            "response_type": "code",
            "state": state,
        })
        return f"https://kauth.kakao.com/oauth/authorize?{query}"

    raise ValueError("지원하지 않는 OAuth provider입니다.")


def handle_oauth_callback(provider, code, state=None):
    if provider == "google":
        profile = _get_google_profile(code)
    elif provider == "naver":
        profile = _get_naver_profile(code, state)
    elif provider == "kakao":
        profile = _get_kakao_profile(code)
    else:
        raise ValueError("지원하지 않는 OAuth provider입니다.")

    user = user_repository.find_by_provider(provider, profile["providerUserId"])

    if not user:
        user = user_repository.find_by_email(profile["email"])

    if not user:
        user = user_repository.create_user(
            email=profile["email"],
            name=profile["name"],
            password=None,
            role=UserRole.VIEWER,
            provider=provider,
            provider_user_id=profile["providerUserId"],
        )
    else:
        user.provider = provider
        user.provider_user_id = profile["providerUserId"]
        user_repository.save(user)

    return create_token_pair(user)


def _get_google_profile(code):
    token_res = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": current_app.config["GOOGLE_CLIENT_ID"],
            "client_secret": current_app.config["GOOGLE_CLIENT_SECRET"],
            "redirect_uri": current_app.config["GOOGLE_REDIRECT_URI"],
            "grant_type": "authorization_code",
        },
        timeout=10,
    )
    token_res.raise_for_status()

    access_token = token_res.json()["access_token"]

    profile_res = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    profile_res.raise_for_status()
    data = profile_res.json()

    return {
        "providerUserId": str(data["id"]),
        "email": data["email"],
        "name": data.get("name") or data["email"].split("@")[0],
    }


def _get_naver_profile(code, state):
    if not state:
        raise ValueError("Naver OAuth state가 누락되었습니다.")

    token_res = requests.get(
        "https://nid.naver.com/oauth2.0/token",
        params={
            "grant_type": "authorization_code",
            "client_id": current_app.config["NAVER_CLIENT_ID"],
            "client_secret": current_app.config["NAVER_CLIENT_SECRET"],
            "code": code,
            "state": state,
        },
        timeout=10,
    )
    token_res.raise_for_status()

    access_token = token_res.json()["access_token"]

    profile_res = requests.get(
        "https://openapi.naver.com/v1/nid/me",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    profile_res.raise_for_status()

    data = profile_res.json()["response"]

    return {
        "providerUserId": str(data["id"]),
        "email": data["email"],
        "name": data.get("name") or data["email"].split("@")[0],
    }


def _get_kakao_profile(code):
    token_data = {
        "grant_type": "authorization_code",
        "client_id": current_app.config["KAKAO_CLIENT_ID"],
        "redirect_uri": current_app.config["KAKAO_REDIRECT_URI"],
        "code": code,
    }

    use_client_secret = (
        current_app.config.get("KAKAO_CLIENT_SECRET_ENABLED")
        and current_app.config.get("KAKAO_CLIENT_SECRET")
    )

    if use_client_secret:
        token_data["client_secret"] = current_app.config["KAKAO_CLIENT_SECRET"]

    token_res = requests.post(
        "https://kauth.kakao.com/oauth/token",
        data=token_data,
        timeout=10,
    )

    if (
        token_res.status_code == 401
        and not use_client_secret
        and current_app.config.get("KAKAO_CLIENT_SECRET")
    ):
        token_data["client_secret"] = current_app.config["KAKAO_CLIENT_SECRET"]
        token_res = requests.post(
            "https://kauth.kakao.com/oauth/token",
            data=token_data,
            timeout=10,
        )

    _raise_oauth_error(token_res, "Kakao token")

    access_token = token_res.json()["access_token"]

    profile_res = requests.get(
        "https://kapi.kakao.com/v2/user/me",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    _raise_oauth_error(profile_res, "Kakao profile")

    data = profile_res.json()
    kakao_account = data.get("kakao_account", {})
    profile = kakao_account.get("profile", {})

    email = kakao_account.get("email") or f"kakao_{data['id']}@kakao.local"

    return {
        "providerUserId": str(data["id"]),
        "email": email,
        "name": profile.get("nickname") or email.split("@")[0],
    }


def _raise_oauth_error(response, label):
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        detail = response.text[:500]
        raise ValueError(f"{label} 요청 실패: {response.status_code} {detail}") from exc
