from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.services import event_service

event_bp = Blueprint("events", __name__)


@event_bp.post("")
def create_event():
    """
    이벤트 저장 (Worker → Backend)
    ---
    tags:
      - Events
    summary: AI 탐지 이벤트 저장 (Worker 내부 호출, 인증 불필요)
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - cctv_id
            - cctv_name
            - location_name
            - detected_at
          properties:
            cctv_id:
              type: string
              example: goduck_tunnel
            cctv_name:
              type: string
              example: "[세종] 고덕터널"
            location_name:
              type: string
              example: 고덕터널
            detected_at:
              type: string
              example: "2026-06-15T12:00:00+09:00"
            risk_score:
              type: integer
              example: 87
            risk_candidate:
              type: boolean
              example: true
            is_fire:
              type: boolean
              example: null
            vlm_reason:
              type: string
              example: null
            detected_classes:
              type: array
              items:
                type: string
              example: ["fire", "smoke"]
            snapshot_key:
              type: string
              example: "raw/20260615_120000_고덕터널.jpg"
    responses:
      201:
        description: 이벤트 저장 성공
      400:
        description: 입력값 오류 (VALIDATION_ERROR)
    """
    body = request.get_json() or {}
    result = event_service.create_event(body)
    return jsonify(result), 201


@event_bp.get("")
@jwt_required()
def list_events():
    """
    이벤트 목록 조회 (Dashboard)
    ---
    tags:
      - Events
    summary: 탐지 이벤트 목록 조회 (페이지네이션 + 필터)
    security:
      - Bearer: []
    parameters:
      - in: query
        name: page
        type: integer
        default: 1
      - in: query
        name: size
        type: integer
        default: 20
      - in: query
        name: cctv_id
        type: string
        description: CCTV ID 필터 (예: goduck_tunnel)
      - in: query
        name: is_fire
        type: boolean
        description: 화재 확정 여부 필터
      - in: query
        name: date_from
        type: string
        description: 시작일 (ISO8601, 예: 2026-06-15)
      - in: query
        name: date_to
        type: string
        description: 종료일 (ISO8601)
    responses:
      200:
        description: 이벤트 목록
      401:
        description: 인증 필요 (AUTH_REQUIRED)
    """
    page = request.args.get("page", default=1, type=int)
    size = request.args.get("size", default=20, type=int)
    cctv_id = request.args.get("cctv_id") or None
    date_from = request.args.get("date_from") or None
    date_to = request.args.get("date_to") or None

    is_fire_raw = request.args.get("is_fire")
    is_fire = None
    if is_fire_raw is not None:
        is_fire = is_fire_raw.lower() in ("true", "1")

    result = event_service.list_events(
        page=page,
        size=size,
        cctv_id=cctv_id,
        is_fire=is_fire,
        date_from=date_from,
        date_to=date_to,
    )
    return jsonify(result)


@event_bp.get("/<int:event_id>")
@jwt_required()
def get_event(event_id):
    """
    이벤트 상세 조회
    ---
    tags:
      - Events
    summary: 이벤트 상세 조회
    security:
      - Bearer: []
    parameters:
      - in: path
        name: event_id
        type: integer
        required: true
    responses:
      200:
        description: 이벤트 상세
      404:
        description: 이벤트 없음 (EVENT_NOT_FOUND)
    """
    result = event_service.get_event(event_id)
    return jsonify(result)
