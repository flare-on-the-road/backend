from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.common.response import fail, success
from app.services import auth_service

user_bp = Blueprint("user", __name__)


def _error_message(error):
    return str(error) or type(error).__name__


@user_bp.get("/me")
@jwt_required()
def get_my_profile():
    """
    내 프로필 조회 API
    ---
    tags:
      - Users
    summary: 내 프로필 조회
    description: Access Token을 이용해 현재 로그인한 사용자의 프로필을 조회합니다.
    security:
      - Bearer: []
    responses:
      200:
        description: 내 프로필 조회 성공
      404:
        description: 사용자 정보 없음
    """
    try:
        user = auth_service.get_current_user(get_jwt_identity())
        return success(user, "내 프로필 조회 성공")
    except Exception as e:
        return fail(_error_message(e), 404)


@user_bp.patch("/me")
@jwt_required()
def update_my_profile():
    """
    내 프로필 수정 API
    ---
    tags:
      - Users
    summary: 내 프로필 수정
    description: 현재 로그인한 사용자의 이름, 부서, 전화번호를 수정합니다.
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              example: 홍길동
            department:
              type: string
              example: 관제팀
            phone:
              type: string
              example: 010-1234-5678
    responses:
      200:
        description: 내 프로필 수정 성공
      400:
        description: 잘못된 요청
      404:
        description: 사용자 정보 없음
    """
    body = request.get_json(silent=True) or {}

    try:
        user = auth_service.update_current_user(
            user_id=get_jwt_identity(),
            name=body.get("name"),
            department=body.get("department"),
            phone=body.get("phone"),
        )
        return success(user, "내 프로필 수정 성공")
    except ValueError as e:
        return fail(_error_message(e), 400)
    except Exception as e:
        return fail(_error_message(e), 404)


@user_bp.post("/me/profile-image")
@jwt_required()
def update_my_profile_image():
    """
    내 프로필 이미지 수정 API
    ---
    tags:
      - Users
    summary: 내 프로필 이미지 수정
    description: multipart/form-data로 전달된 profileImage 파일을 업로드하고 현재 사용자의 프로필 이미지로 지정합니다.
    security:
      - Bearer: []
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: profileImage
        type: file
        required: true
        description: 프로필 이미지 파일
    responses:
      200:
        description: 내 프로필 이미지 수정 성공
      400:
        description: 잘못된 요청
      404:
        description: 사용자 정보 없음
    """
    profile_image = request.files.get("profileImage")

    if not profile_image:
        return fail("프로필 이미지를 선택해주세요.", 400)

    try:
        user = auth_service.update_current_user_profile_image(
            user_id=get_jwt_identity(),
            profile_image=profile_image,
        )
        return success(user, "내 프로필 이미지 수정 성공")
    except ValueError as e:
        return fail(_error_message(e), 400)
    except Exception as e:
        return fail(_error_message(e), 400)
