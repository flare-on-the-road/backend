from app.common.constants import UserRole
from app.common.errors import (
    CommentNotFoundError,
    ForbiddenError,
    InvalidParentError,
    MaxDepthExceededError,
    PostNotFoundError,
)
from app.repositories import comment_repository, post_repository
from app.schemas.comment_schema import build_comment_tree, validate_comment_input


def _ensure_post_visible(post_id, user_id, role):
    post = post_repository.find_active_by_id(post_id)
    if post is None:
        raise PostNotFoundError()

    is_owner = post.author_id == user_id
    is_admin = role == UserRole.ADMIN

    if post.is_hidden and not (is_owner or is_admin):
        raise ForbiddenError("가려진 게시물입니다.")

    return post


def get_comment_tree(post_id, user_id, role):
    _ensure_post_visible(post_id, user_id, role)

    rows = comment_repository.find_all_by_post(post_id)
    comments = build_comment_tree(rows, user_id, role)
    total_count = comment_repository.count_visible_by_post(post_id)

    return {"comments": comments, "total_count": total_count}


def create_comment(post_id, user_id, role, data):
    content, parent_id = validate_comment_input(data)
    _ensure_post_visible(post_id, user_id, role)

    if parent_id is not None:
        parent = comment_repository.find_by_id(parent_id)
        if parent is None or parent.post_id != post_id:
            raise InvalidParentError()

        if parent.is_deleted or parent.is_hidden:
            raise InvalidParentError()

        if parent.parent_id is not None:
            raise MaxDepthExceededError()

    comment = comment_repository.create(post_id, user_id, content, parent_id)
    return {"id": comment.id}


def _get_owned_editable_comment(comment_id, user_id):
    comment = comment_repository.find_by_id(comment_id)
    if comment is None or comment.is_deleted:
        raise CommentNotFoundError()

    if comment.author_id != user_id:
        raise ForbiddenError("본인 댓글만 수정/삭제할 수 있습니다.")

    if comment.is_hidden:
        raise ForbiddenError("가려진 댓글은 수정/삭제할 수 없습니다.")

    return comment


def update_comment(comment_id, user_id, data):
    comment = _get_owned_editable_comment(comment_id, user_id)
    content, _ = validate_comment_input({"content": data.get("content")})

    comment.content = content
    comment_repository.save(comment)

    return {"id": comment.id}


def delete_comment(comment_id, user_id):
    comment = _get_owned_editable_comment(comment_id, user_id)
    comment_repository.soft_delete(comment)


def hide_comment(comment_id, role, admin_id):
    if role != UserRole.ADMIN:
        raise ForbiddenError("관리자만 댓글을 가릴 수 있습니다.")

    comment = comment_repository.find_by_id(comment_id)
    if comment is None:
        raise CommentNotFoundError()

    comment_repository.hide(comment, admin_id)


def unhide_comment(comment_id, role):
    if role != UserRole.ADMIN:
        raise ForbiddenError("관리자만 댓글 가림을 해제할 수 있습니다.")

    comment = comment_repository.find_by_id(comment_id)
    if comment is None:
        raise CommentNotFoundError()

    comment_repository.unhide(comment)
