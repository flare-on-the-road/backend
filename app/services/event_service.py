import logging
from datetime import datetime
from typing import Optional

from app.common.errors import EventNotFoundError, ValidationError
from app.common.uploads import create_presigned_download_url
from app.repositories import event_repository

logger = logging.getLogger(__name__)

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
        "vlm_results": body.get("vlm_results"),
        "detections": body.get("detections") or [],
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
        "events": [_with_snapshot_url(r.to_dict()) for r in rows],
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
    return _with_snapshot_url(event.to_dict())


def list_fire_alerts(after_id: Optional[int] = None, size: int = 20) -> dict:
    size = min(max(size or DEFAULT_PAGE_SIZE, 1), MAX_PAGE_SIZE)
    rows = event_repository.find_confirmed_fire_alerts(after_id=after_id, limit=size)

    return {
        "events": [_with_snapshot_url(r.to_dict()) for r in rows],
        "latestId": rows[-1].id if rows else after_id,
    }


def patch_event_vlm(event_id: int, body: dict) -> dict:
    if "vlm_results" not in body:
        raise ValidationError("vlm_results 필드가 필요합니다")
    vlm_results = body["vlm_results"]
    if not isinstance(vlm_results, list):
        raise ValidationError("vlm_results는 배열이어야 합니다")

    event = event_repository.update_vlm_result(event_id, vlm_results)
    if event is None:
        raise EventNotFoundError()
    return _with_snapshot_url(event.to_dict())


def _with_snapshot_url(event_dict: dict) -> dict:
    key = event_dict.get("snapshotKey")
    if key:
        try:
            event_dict["snapshotUrl"] = create_presigned_download_url(key)
        except Exception:
            logger.warning("presigned URL 생성 실패: %s", key)
            event_dict["snapshotUrl"] = None
    else:
        event_dict["snapshotUrl"] = None
    return event_dict


def _parse_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except (ValueError, AttributeError):
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value.replace("+09:00", "").replace("Z", ""), fmt.replace("%z", ""))
            return dt
        except (ValueError, AttributeError):
            continue
    raise ValidationError(f"날짜 형식 오류: {value}")
