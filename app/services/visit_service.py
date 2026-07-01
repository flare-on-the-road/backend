from datetime import date

from sqlalchemy import func, select

from app.extensions import db
from app.models.visit import Visit


def record_visit(visitor_key, path=None, user_id=None, ip_address=None, user_agent=None):
    visitor_key = str(visitor_key or "").strip()[:100]
    if not visitor_key:
        raise ValueError("visitor_key is required")

    today = date.today()
    existing = db.session.execute(
        select(Visit.id).where(
            Visit.visitor_key == visitor_key,
            Visit.visit_date == today,
        )
    ).first()

    if existing:
        return {"recorded": False}

    visit = Visit(
        visitor_key=visitor_key,
        visit_date=today,
        path=str(path or "")[:500] or None,
        user_id=user_id,
        ip_address=str(ip_address or "")[:100] or None,
        user_agent=str(user_agent or "")[:500] or None,
    )
    db.session.add(visit)
    db.session.commit()
    return {"recorded": True}


def count_total_visitors():
    return db.session.execute(select(func.count(func.distinct(Visit.visitor_key)))).scalar_one()


def count_today_visitors():
    return db.session.execute(
        select(func.count(func.distinct(Visit.visitor_key))).where(
            Visit.visit_date == date.today(),
        )
    ).scalar_one()
