from sqlalchemy import func, select

from app.extensions import db
from app.models.post_like import PostLike


def find(post_id, user_id):
    stmt = select(PostLike).where(
        PostLike.post_id == post_id,
        PostLike.user_id == user_id,
    )
    return db.session.execute(stmt).scalar_one_or_none()


def count_by_post(post_id):
    stmt = select(func.count(PostLike.id)).where(PostLike.post_id == post_id)
    return db.session.execute(stmt).scalar_one()


def create(post_id, user_id):
    like = PostLike(post_id=post_id, user_id=user_id)
    db.session.add(like)
    db.session.commit()
    return like


def delete(like):
    db.session.delete(like)
    db.session.commit()
