from datetime import datetime
from typing import Optional

from sqlalchemy import select, func

from app.extensions import db
from app.models.event import Event


def create(data: dict) -> Event:
    event = Event(
        cctv_id=data["cctv_id"],
        cctv_name=data["cctv_name"],
        location_name=data["location_name"],
        detected_at=data["detected_at"],
        is_fire=data.get("is_fire"),
        vlm_reason=data.get("vlm_reason"),
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
        q = q.where(Event.is_fire == is_fire)
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
    q = select(Event).where(Event.is_fire.is_(True))

    if after_id is not None:
        q = q.where(Event.id > after_id)
        q = q.order_by(Event.id.asc()).limit(limit)
        return db.session.execute(q).scalars().all()

    q = q.order_by(Event.id.desc()).limit(limit)
    rows = db.session.execute(q).scalars().all()
    return list(reversed(rows))


def update_vlm_result(event_id: int, is_fire: bool, vlm_reason: Optional[str]) -> Optional[Event]:
    event = db.session.get(Event, event_id)
    if event is None:
        return None
    event.is_fire = is_fire
    event.vlm_reason = vlm_reason
    db.session.commit()
    return event
