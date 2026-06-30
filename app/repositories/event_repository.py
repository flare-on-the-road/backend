from datetime import datetime
from typing import Optional

from sqlalchemy import select, func, text

from app.extensions import db
from app.models.event import Event


def create(data: dict) -> Event:
    event = Event(
        cctv_id=data["cctv_id"],
        cctv_name=data["cctv_name"],
        location_name=data["location_name"],
        detected_at=data["detected_at"],
        vlm_results=data.get("vlm_results"),
        detections=data.get("detections", []),
        snapshot_key=data.get("snapshot_key"),
    )
    db.session.add(event)
    db.session.commit()
    return event


def find_list(
    page: int,
    size: int,
    cctv_id: Optional[str] = None,
    is_fire: Optional[bool] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
):
    q = select(Event)

    if cctv_id:
        q = q.where(Event.cctv_id == cctv_id)
    if is_fire is not None:
        # vlm_results 배열에 is_false_positive=false 항목 존재 여부로 화재 확정 판단 (MySQL 8.0.17+)
        fire_confirmed = text(
            "JSON_OVERLAPS(JSON_EXTRACT(vlm_results, '$[*].is_false_positive'), JSON_ARRAY(false)) = 1"
        )
        if is_fire:
            q = q.where(Event.vlm_results.isnot(None)).where(fire_confirmed)
        else:
            q = q.where(
                (Event.vlm_results.is_(None)) | ~fire_confirmed
            )
    if date_from:
        q = q.where(Event.detected_at >= date_from)
    if date_to:
        q = q.where(Event.detected_at <= date_to)

    q = q.order_by(Event.detected_at.desc())

    count_q = select(func.count()).select_from(q.subquery())
    total = db.session.execute(count_q).scalar() or 0

    rows = db.session.execute(q.offset((page - 1) * size).limit(size)).scalars().all()
    return rows, total


def find_by_id(event_id: int) -> Optional[Event]:
    return db.session.get(Event, event_id)


def find_confirmed_fire_alerts(after_id: Optional[int] = None, limit: int = 20):
    # vlm_results 배열에 is_false_positive=false인 항목이 하나라도 있는 행 조회 (MySQL 8.0.17+)
    fire_confirmed = text(
        "JSON_OVERLAPS(JSON_EXTRACT(vlm_results, '$[*].is_false_positive'), JSON_ARRAY(false)) = 1"
    )
    q = select(Event).where(Event.vlm_results.isnot(None)).where(fire_confirmed)

    if after_id is not None:
        q = q.where(Event.id > after_id)
        q = q.order_by(Event.id.asc()).limit(limit)
        return db.session.execute(q).scalars().all()

    q = q.order_by(Event.id.desc()).limit(limit)
    rows = db.session.execute(q).scalars().all()
    return list(reversed(rows))


def update_vlm_result(event_id: int, vlm_results: Optional[list]) -> Optional[Event]:
    event = db.session.get(Event, event_id)
    if event is None:
        return None
    event.vlm_results = vlm_results
    db.session.commit()
    return event
