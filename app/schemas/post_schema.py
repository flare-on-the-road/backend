from app.common.constants import PostBoardType, UserRole
from app.common.errors import ValidationError

TITLE_MAX_LENGTH = 100
CONTENT_MAX_LENGTH = 10000

HIDDEN_TITLE_TEXT = "관리자에 의해 가려진 게시물입니다"


def validate_post_input(data, board_type=PostBoardType.BUG, role=None):
    errors = {}

    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()

    if not title:
        errors["title"] = "제목을 입력해주세요."
    elif len(title) > TITLE_MAX_LENGTH:
        errors["title"] = f"제목은 {TITLE_MAX_LENGTH}자 이하로 입력해주세요."

    if not content:
        errors["content"] = "내용을 입력해주세요."
    elif len(content) > CONTENT_MAX_LENGTH:
        errors["content"] = f"내용은 {CONTENT_MAX_LENGTH}자 이하로 입력해주세요."

    if errors:
        raise ValidationError(errors)

    is_important = (
        bool(data.get("is_important"))
        if board_type == PostBoardType.NOTICE and role == UserRole.ADMIN
        else False
    )

    return title, content, is_important


def serialize_post_summary(row, user_id, role):
    post = row.Post
    can_view_original = post.author_id == user_id or role == UserRole.ADMIN

    if post.is_hidden and not can_view_original:
        title = HIDDEN_TITLE_TEXT
        author_nickname = None
    else:
        title = post.title
        author_nickname = row.author_nickname

    is_locked = post.board_type == PostBoardType.INQUIRY and not can_view_original

    if is_locked:
        author_nickname = None
        view_count = 0
        comment_count = 0
        like_count = 0
    else:
        view_count = post.view_count
        comment_count = int(row.comment_count)
        like_count = int(row.like_count)

    return {
        "id": post.id,
        "title": title,
        "author_nickname": author_nickname,
        "view_count": view_count,
        "comment_count": comment_count,
        "like_count": like_count,
        "is_hidden": post.is_hidden,
        "board_type": post.board_type,
        "is_important": post.is_important,
        "is_locked": is_locked,
        "created_at": post.created_at.isoformat(),
    }


def serialize_post_detail(row, user_id, role, liked_by_me):
    post = row.Post
    is_owner = post.author_id == user_id
    is_admin = role == UserRole.ADMIN

    if post.board_type == PostBoardType.NOTICE:
        can_edit = is_admin
        can_delete = is_admin
    else:
        can_edit = is_owner and not post.is_hidden
        can_delete = is_owner and not post.is_hidden

    can_like = not (
        post.board_type == PostBoardType.INQUIRY and is_admin and not is_owner
    )

    permissions = {
        "can_edit": can_edit,
        "can_delete": can_delete,
        "can_hide": is_admin,
        "can_like": can_like,
    }

    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "author_id": post.author_id,
        "author_nickname": row.author_nickname,
        "is_hidden": post.is_hidden,
        "board_type": post.board_type,
        "is_important": post.is_important,
        "view_count": post.view_count,
        "like_count": int(row.like_count),
        "liked_by_me": liked_by_me,
        "comment_count": int(row.comment_count),
        "created_at": post.created_at.isoformat(),
        "updated_at": post.updated_at.isoformat(),
        "permissions": permissions,
    }
