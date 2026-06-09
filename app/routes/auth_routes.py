from urllib.parse import urlencode

from flask import Blueprint, request, redirect, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.common.response import success, fail
from app.services import account_recovery_service, auth_service, oauth_service

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    """
    회원가입 API
    ---
    tags:
      - Auth
    summary: 회원가입
    description: 이메일, 이름, 비밀번호, 부서, 전화번호를 받아 신규 사용자를 생성합니다.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - name
            - password
          properties:
            email:
              type: string
              example: user@example.com
            name:
              type: string
              example: 홍길동
            password:
              type: string
              example: password1234
            department:
              type: string
              example: 관제팀
            phone:
              type: string
              example: 010-1234-5678
    responses:
      201:
        description: 회원가입 성공
      400:
        description: 회원가입 실패
    """
    body = request.get_json() or {}

    try:
        result = auth_service.register_user(
            email=body.get("email"),
            name=body.get("name"),
            password=body.get("password"),
            department=body.get("department"),
            phone=body.get("phone"),
        )
        return success(result, "회원가입 성공", 201)
    except Exception as e:
        return fail(str(e), 400)


@auth_bp.post("/login")
def login():
    """
    로그인 API
    ---
    tags:
      - Auth
    summary: 로그인
    description: 이메일과 비밀번호를 검증하고 Access Token, Refresh Token을 발급합니다.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: user@example.com
            password:
              type: string
              example: password1234
    responses:
      200:
        description: 로그인 성공
      401:
        description: 로그인 실패
    """
    body = request.get_json() or {}

    try:
        result = auth_service.login_user(
            email=body.get("email"),
            password=body.get("password"),
        )
        return success(result, "로그인 성공")
    except Exception as e:
        return fail(str(e), 401)


@auth_bp.post("/find-id")
def find_id():
    body = request.get_json() or {}

    try:
        result = account_recovery_service.find_user_emails(
            name=body.get("name"),
            phone=body.get("phone"),
        )
        return success(result, "아이디 찾기 성공")
    except Exception as e:
        return fail(str(e), 400)


@auth_bp.post("/forgot-password")
def forgot_password():
    body = request.get_json() or {}

    try:
        result = account_recovery_service.reset_password(
            email=body.get("email"),
            name=body.get("name"),
            phone=body.get("phone"),
        )
        return success(result, "임시 비밀번호 발급 성공")
    except Exception as e:
        return fail(str(e), 400)


@auth_bp.get("/me")
@jwt_required()
def me():
    """
    내 정보 조회 API
    ---
    tags:
      - Auth
    summary: 내 정보 조회
    description: Access Token을 이용해 현재 로그인한 사용자의 정보를 조회합니다.
    security:
      - Bearer: []
    responses:
      200:
        description: 내 정보 조회 성공
      404:
        description: 사용자 정보 없음
    """
    try:
        user_id = get_jwt_identity()
        user = auth_service.get_current_user(user_id)
        return success(user, "내 정보 조회 성공")
    except Exception as e:
        return fail(str(e), 404)


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    """
    Access Token 재발급 API
    ---
    tags:
      - Auth
    summary: Access Token 재발급
    description: Refresh Token을 이용해 새로운 Access Token을 발급합니다.
    security:
      - Bearer: []
    responses:
      200:
        description: 토큰 재발급 성공
      401:
        description: 토큰 재발급 실패
    """
    try:
        user_id = get_jwt_identity()
        result = auth_service.refresh_access_token(user_id)
        return success(result, "토큰 재발급 성공")
    except Exception as e:
        return fail(str(e), 401)


@auth_bp.post("/logout")
@jwt_required()
def logout():
    """
    로그아웃 API
    ---
    tags:
      - Auth
    summary: 로그아웃
    description: 현재 MVP 단계에서는 클라이언트가 토큰을 제거하는 방식으로 로그아웃을 처리합니다.
    security:
      - Bearer: []
    responses:
      200:
        description: 로그아웃 성공
    """
    return success(None, "로그아웃 성공")


@auth_bp.get("/oauth/<provider>/login")
def oauth_login(provider):
    """
    OAuth 로그인 시작 API
    ---
    tags:
      - OAuth
    summary: OAuth 로그인 URL로 이동
    description: Google/Naver/Kakao OAuth 로그인 페이지로 redirect합니다.
    parameters:
      - in: path
        name: provider
        required: true
        type: string
        enum:
          - google
          - naver
          - kakao
        example: google
    responses:
      302:
        description: OAuth 로그인 페이지로 이동
      400:
        description: 지원하지 않는 provider
    """
    try:
        url = oauth_service.get_oauth_login_url(provider)
        return redirect(url)
    except Exception as e:
        return fail(str(e), 400)


@auth_bp.get("/oauth/<provider>/callback")
def oauth_callback(provider):
    """
    OAuth Callback API
    ---
    tags:
      - OAuth
    summary: OAuth Callback 처리
    description: OAuth provider에서 전달받은 code를 처리하고 JWT 토큰을 발급한 뒤 프론트엔드로 redirect합니다.
    parameters:
      - in: path
        name: provider
        required: true
        type: string
        enum:
          - google
          - naver
          - kakao
        example: google
      - in: query
        name: code
        required: true
        type: string
        example: oauth_authorization_code
    responses:
      302:
        description: 프론트엔드 OAuth callback 페이지로 이동
    """
    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        return redirect(f"{current_app.config['FRONTEND_URL']}/login?error=oauth_no_code")

    try:
        result = oauth_service.handle_oauth_callback(provider, code, state)

        query = urlencode({
            "accessToken": result["accessToken"],
            "refreshToken": result.get("refreshToken", ""),
        })

        return redirect(f"{current_app.config['FRONTEND_URL']}/oauth/callback?{query}")

    except Exception:
        return redirect(f"{current_app.config['FRONTEND_URL']}/login?error=oauth_failed")
