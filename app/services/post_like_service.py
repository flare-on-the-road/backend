from sqlalchemy.exc import IntegrityError

from app.common.constants import PostBoardType, UserRole
from app.common.errors import ForbiddenError, PostNotFoundError
from app.extensions import db
from app.repositories import post_like_repository, post_repository


def toggle_like(post_id, user_id, role):
    post = post_repository.find_active_by_id(post_id)
    if post is None:
        raise PostNotFoundError()

    if post.is_hidden:
        raise ForbiddenError("가려진 게시물은 좋아요를 누를 수 없습니다.")

    if (
        post.board_type == PostBoardType.INQUIRY
        and role == UserRole.ADMIN
        and post.author_id != user_id
    ):
        raise ForbiddenError("관리자는 1:1 문의에 좋아요를 누를 수 없습니다.")

    existing = post_like_repository.find(post_id, user_id)

    if existing is not None:
        post_like_repository.delete(existing)
        liked = False
    else:
        try:
            post_like_repository.create(post_id, user_id)
            liked = True
        except IntegrityError:
            db.session.rollback()
            existing = post_like_repository.find(post_id, user_id)
            if existing is not None:
                post_like_repository.delete(existing)
            liked = False

    like_count = post_like_repository.count_by_post(post_id)
    return {"liked": liked, "like_count": like_count}
