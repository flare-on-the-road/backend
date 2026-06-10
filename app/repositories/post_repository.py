from datetime import datetime

from sqlalchemy import func, or_, select

from app.extensions import db
from app.models.comment import Comment
from app.models.post import Post
from app.models.post_like import PostLike
from app.models.user import User


def escape_like(value):
    return (
        value.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def _comment_count_subquery():
    return (
        select(
            Comment.post_id.label("post_id"),
            func.count(Comment.id).label("comment_count"),
        )
        .where(Comment.is_deleted.is_(False), Comment.is_hidden.is_(False))
        .group_by(Comment.post_id)
        .subquery()
    )


def _like_count_subquery():
    return (
        select(
            PostLike.post_id.label("post_id"),
            func.count(PostLike.id).label("like_count"),
        )
        .group_by(PostLike.post_id)
        .subquery()
    )


def _base_select():
    comment_counts = _comment_count_subquery()
    like_counts = _like_count_subquery()

    return (
        select(
            Post,
            User.name.label("author_nickname"),
            func.coalesce(comment_counts.c.comment_count, 0).label("comment_count"),
            func.coalesce(like_counts.c.like_count, 0).label("like_count"),
        )
        .join(User, User.id == Post.author_id)
        .outerjoin(comment_counts, comment_counts.c.post_id == Post.id)
        .outerjoin(like_counts, like_counts.c.post_id == Post.id)
        .where(Post.is_deleted.is_(False))
    )


def _apply_search(stmt, keyword, search_type):
    if not keyword:
        return stmt

    pattern = f"%{escape_like(keyword)}%"

    if search_type == "content":
        return stmt.where(Post.content.like(pattern, escape="\\"))
    if search_type == "title_content":
        return stmt.where(
            or_(
                Post.title.like(pattern, escape="\\"),
                Post.content.like(pattern, escape="\\"),
            )
        )
    if search_type == "author":
        return stmt.where(User.name.like(pattern, escape="\\"))

    return stmt.where(Post.title.like(pattern, escape="\\"))


def find_posts(page, size, keyword=None, search_type="title"):
    stmt = _apply_search(_base_select(), keyword, search_type)

    total_count = db.session.execute(
        select(func.count()).select_from(stmt.subquery())
    ).scalar_one()

    stmt = (
        stmt.order_by(Post.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )

    rows = db.session.execute(stmt).all()
    return rows, total_count


def find_detail(post_id):
    stmt = _base_select().where(Post.id == post_id)
    return db.session.execute(stmt).first()


def find_active_by_id(post_id):
    stmt = select(Post).where(Post.id == post_id, Post.is_deleted.is_(False))
    return db.session.execute(stmt).scalar_one_or_none()


def find_by_id(post_id):
    return db.session.get(Post, post_id)


def create(author_id, title, content):
    post = Post(author_id=author_id, title=title, content=content)
    db.session.add(post)
    db.session.commit()
    return post


def save(post):
    db.session.commit()
    return post


def increment_view_count(post):
    post.view_count += 1
    db.session.commit()


def soft_delete(post):
    post.is_deleted = True
    db.session.commit()


def hide(post, admin_id):
    post.is_hidden = True
    post.hidden_by = admin_id
    post.hidden_at = datetime.utcnow()
    db.session.commit()


def unhide(post):
    post.is_hidden = False
    post.hidden_by = None
    post.hidden_at = None
    db.session.commit()
