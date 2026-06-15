from datetime import datetime
from typing import Optional

from app.common.errors import EventNotFoundError, ValidationError
from app.repositories import event_repository

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


def create_event(body: dict) -> dict:
    required = ["cctv_id", "cctv_name", "location_name", "detected_at"]
    missing = [f for f in required if not body.get(f)]
    if missing:
        raise ValidationError(f"필수 필드 누락: {', '.join(missing)}")

    detected_at = _parse_datetime(body["detected_at"])

    event = event_repository.create({
        "cctv_id": body["cctv_id"],
        "cctv_name": body["cctv_name"],
        "location_name": body["location_name"],
        "detected_at": detected_at,
        "risk_score": int(body.get("risk_score") or 0),
        "risk_candidate": bool(body.get("risk_candidate", True)),
        "is_fire": body.get("is_fire"),
        "vlm_reason": body.get("vlm_reason"),
        "detected_classes": body.get("detected_classes") or [],
        "snapshot_key": body.get("snapshot_key"),
    })

    return event.to_dict()


def list_events(
    page: int = 1,
    size: int = DEFAULT_PAGE_SIZE,
    cctv_id: Optional[str] = None,
    is_fire: Optional[bool] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> dict:
    page = max(page or 1, 1)
    size = min(max(size or DEFAULT_PAGE_SIZE, 1), MAX_PAGE_SIZE)

    parsed_from = _parse_datetime(date_from) if date_from else None
    parsed_to = _parse_datetime(date_to) if date_to else None

    rows, total = event_repository.find_list(
        page, size, cctv_id=cctv_id, is_fire=is_fire,
        date_from=parsed_from, date_to=parsed_to,
    )

    total_pages = (total + size - 1) // size if total else 0

    return {
        "events": [r.to_dict() for r in rows],
        "pagination": {
            "current_page": page,
            "size": size,
            "total_count": total,
            "total_pages": total_pages,
        },
    }


def get_event(event_id: int) -> dict:
    event = event_repository.find_by_id(event_id)
    if event is None:
        raise EventNotFoundError()
    return event.to_dict()


def _parse_datetime(value: str) -> datetime:
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value.replace("+09:00", "").replace("Z", ""), fmt.replace("%z", ""))
            return dt
        except (ValueError, AttributeError):
            continue
    raise ValidationError(f"날짜 형식 오류: {value}")
