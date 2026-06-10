from app.common.constants import UserRole
from app.common.errors import ForbiddenError, PostNotFoundError
from app.repositories import post_like_repository, post_repository
from app.schemas.post_schema import (
    serialize_post_detail,
    serialize_post_summary,
    validate_post_input,
)

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50
ALLOWED_SEARCH_TYPES = {"title", "content", "title_content", "author"}


def list_posts(user_id, role, page=1, size=DEFAULT_PAGE_SIZE, keyword=None, search_type=None):
    page = max(page or 1, 1)
    size = min(max(size or DEFAULT_PAGE_SIZE, 1), MAX_PAGE_SIZE)

    keyword = (keyword or "").strip()
    if search_type not in ALLOWED_SEARCH_TYPES:
        search_type = "title"

    rows, total_count = post_repository.find_posts(page, size, keyword or None, search_type)
    posts = [serialize_post_summary(row, user_id, role) for row in rows]

    total_pages = (total_count + size - 1) // size if total_count else 0

    return {
        "posts": posts,
        "pagination": {
            "current_page": page,
            "size": size,
            "total_count": total_count,
            "total_pages": total_pages,
        },
    }


def get_post_detail(post_id, user_id, role):
    row = post_repository.find_detail(post_id)
    if row is None:
        raise PostNotFoundError()

    post = row.Post
    is_owner = post.author_id == user_id
    is_admin = role == UserRole.ADMIN

    if post.is_hidden and not (is_owner or is_admin):
        raise ForbiddenError("가려진 게시물입니다.")

    post_repository.increment_view_count(post)

    like = post_like_repository.find(post_id, user_id)
    liked_by_me = like is not None

    return serialize_post_detail(row, user_id, role, liked_by_me)


def create_post(user_id, data):
    title, content = validate_post_input(data)
    post = post_repository.create(user_id, title, content)
    return {"id": post.id}


def _get_owned_active_post(post_id, user_id):
    post = post_repository.find_active_by_id(post_id)
    if post is None:
        raise PostNotFoundError()

    if post.author_id != user_id:
        raise ForbiddenError("본인 게시글만 수정/삭제할 수 있습니다.")

    if post.is_hidden:
        raise ForbiddenError("가려진 게시물은 수정/삭제할 수 없습니다.")

    return post


def update_post(post_id, user_id, data):
    post = _get_owned_active_post(post_id, user_id)
    title, content = validate_post_input(data)

    post.title = title
    post.content = content
    post_repository.save(post)

    return {"id": post.id}


def delete_post(post_id, user_id):
    post = _get_owned_active_post(post_id, user_id)
    post_repository.soft_delete(post)


def hide_post(post_id, role, admin_id):
    if role != UserRole.ADMIN:
        raise ForbiddenError("관리자만 게시글을 가릴 수 있습니다.")

    post = post_repository.find_active_by_id(post_id)
    if post is None:
        raise PostNotFoundError()

    post_repository.hide(post, admin_id)


def unhide_post(post_id, role):
    if role != UserRole.ADMIN:
        raise ForbiddenError("관리자만 게시글 가림을 해제할 수 있습니다.")

    post = post_repository.find_active_by_id(post_id)
    if post is None:
        raise PostNotFoundError()

    post_repository.unhide(post)
