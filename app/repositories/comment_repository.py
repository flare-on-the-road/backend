from datetime import datetime

from sqlalchemy import func, select

from app.extensions import db
from app.models.comment import Comment
from app.models.user import User


def find_by_id(comment_id):
    return db.session.get(Comment, comment_id)


def find_all_by_post(post_id):
    stmt = (
        select(Comment, User.name.label("author_nickname"))
        .join(User, User.id == Comment.author_id)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc())
    )
    return db.session.execute(stmt).all()


def count_visible_by_post(post_id):
    stmt = select(func.count(Comment.id)).where(
        Comment.post_id == post_id,
        Comment.is_deleted.is_(False),
        Comment.is_hidden.is_(False),
    )
    return db.session.execute(stmt).scalar_one()


def create(post_id, author_id, content, parent_id=None):
    comment = Comment(
        post_id=post_id,
        author_id=author_id,
        content=content,
        parent_id=parent_id,
    )
    db.session.add(comment)
    db.session.commit()
    return comment


def save(comment):
    db.session.commit()
    return comment


def soft_delete(comment):
    comment.is_deleted = True
    db.session.commit()


def hide(comment, admin_id):
    comment.is_hidden = True
    comment.hidden_by = admin_id
    comment.hidden_at = datetime.utcnow()
    db.session.commit()


def unhide(comment):
    comment.is_hidden = False
    comment.hidden_by = None
    comment.hidden_at = None
    db.session.commit()
