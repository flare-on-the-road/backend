from app.common.constants import UserRole
from app.common.errors import ValidationError

CONTENT_MAX_LENGTH = 1000

DELETED_CONTENT_TEXT = "삭제된 댓글입니다"
HIDDEN_CONTENT_TEXT = "관리자에 의해 가려진 댓글입니다"


def validate_comment_input(data):
    errors = {}

    content = (data.get("content") or "").strip()
    if not content:
        errors["content"] = "댓글 내용을 입력해주세요."
    elif len(content) > CONTENT_MAX_LENGTH:
        errors["content"] = f"댓글은 {CONTENT_MAX_LENGTH}자 이하로 입력해주세요."

    parent_id = data.get("parent_id")
    if parent_id is not None:
        try:
            parent_id = int(parent_id)
        except (TypeError, ValueError):
            errors["parent_id"] = "parent_id는 숫자여야 합니다."
            parent_id = None

    if errors:
        raise ValidationError(errors)

    return content, parent_id


def build_comment_tree(rows, user_id, role):
    nodes = {}
    top_level = []

    for comment, author_nickname in rows:
        node = {"comment": comment, "author_nickname": author_nickname, "replies": []}
        nodes[comment.id] = node

        if comment.parent_id is None:
            top_level.append(node)
        else:
            parent_node = nodes.get(comment.parent_id)
            if parent_node is not None:
                parent_node["replies"].append(node)

    comments = []
    for node in top_level:
        serialized = _serialize_node(node, user_id, role)
        if serialized is not None:
            comments.append(serialized)

    return comments


def _serialize_node(node, user_id, role):
    comment = node["comment"]

    replies = []
    for child in node["replies"]:
        serialized_child = _serialize_node(child, user_id, role)
        if serialized_child is not None:
            replies.append(serialized_child)

    if comment.is_deleted and not replies:
        return None

    is_owner = comment.author_id == user_id
    is_admin = role == UserRole.ADMIN

    if comment.is_deleted:
        content = DELETED_CONTENT_TEXT
        author_nickname = node["author_nickname"]
    elif comment.is_hidden and not (is_owner or is_admin):
        content = HIDDEN_CONTENT_TEXT
        author_nickname = None
    else:
        content = comment.content
        author_nickname = node["author_nickname"]

    permissions = {
        "can_edit": is_owner and not comment.is_deleted and not comment.is_hidden,
        "can_delete": is_owner and not comment.is_deleted and not comment.is_hidden,
        "can_hide": is_admin and not comment.is_deleted,
    }

    return {
        "id": comment.id,
        "author_nickname": author_nickname,
        "content": content,
        "is_deleted": comment.is_deleted,
        "is_hidden": comment.is_hidden,
        "created_at": comment.created_at.isoformat(),
        "permissions": permissions,
        "replies": replies,
    }
