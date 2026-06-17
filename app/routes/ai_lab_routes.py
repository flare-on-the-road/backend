from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.common.errors import ValidationError
from app.services import ai_lab_service

ai_lab_bp = Blueprint("ai_lab", __name__)

VALID_MODEL_KEYS = {"rt-detr", "yolov8", "yolov11"}


@ai_lab_bp.post("/detect")
@jwt_required()
def detect():
    """
    화재/연기 탐지 모델 비교
    ---
    tags:
      - AI Lab
    summary: 선택한 모델들의 탐지 결과 비교 (RT-DETR은 Vision FastAPI 서버 호출)
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - models
          properties:
            image_base64:
              type: string
              description: 업로드 이미지의 base64 (image_key와 택일)
            image_key:
              type: string
              description: 샘플 이미지 식별자 (image_base64와 택일)
              example: sample_highway_fire
            models:
              type: array
              items:
                type: string
                enum: [rt-detr, yolov8, yolov11]
              example: ["rt-detr", "yolov8", "yolov11"]
            threshold:
              type: number
              default: 0.3
              example: 0.3
    responses:
      200:
        description: 모델별 추론 시간 / FPS / 탐지 결과
      400:
        description: 입력값 검증 실패 (VALIDATION_ERROR)
      401:
        description: 인증 필요 (AUTH_REQUIRED)
    """
    body = request.get_json(silent=True) or {}

    models = body.get("models")
    image_base64 = body.get("image_base64")
    image_key = body.get("image_key")
    threshold = body.get("threshold", 0.30)

    errors = {}

    if (
        not models
        or not isinstance(models, list)
        or not all(isinstance(m, str) and m in VALID_MODEL_KEYS for m in models)
    ):
        errors["models"] = "models는 rt-detr, yolov8, yolov11 중 1개 이상을 포함한 배열이어야 합니다."

    if not image_base64 and not image_key:
        errors["image"] = "image_base64 또는 image_key 중 하나는 필수입니다."

    if not isinstance(threshold, (int, float)) or not (0 <= threshold <= 1):
        errors["threshold"] = "threshold는 0~1 사이의 숫자여야 합니다."

    if errors:
        raise ValidationError(errors)

    results = ai_lab_service.detect(
        image_key=image_key,
        image_base64=image_base64,
        models=models,
        threshold=float(threshold),
    )
    return jsonify({"results": results})
