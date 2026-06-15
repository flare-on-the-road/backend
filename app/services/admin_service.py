import re

from sqlalchemy import case, func, or_, select

from app.common.constants import AuthProvider, PostBoardType, UserRole
from app.common.errors import ForbiddenError, ValidationError
from app.extensions import db
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.services import comment_service

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50
ALLOWED_ROLES = {UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER}
ALLOWED_BOARD_TYPES = set(PostBoardType.ALL)
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def get_summary():
    total_users = _count(select(func.count(User.id)))
    active_users = _count(select(func.count(User.id)).where(User.is_active.is_(True)))
    total_posts = _count(select(func.count(Post.id)).where(Post.is_deleted.is_(False)))
    hidden_posts = _count(
        select(func.count(Post.id)).where(
            Post.is_deleted.is_(False),
            Post.is_hidden.is_(True),
        )
    )
    hidden_comments = _count(
        select(func.count(Comment.id)).where(
            Comment.is_deleted.is_(False),
            Comment.is_hidden.is_(True),
        )
    )
    open_inquiries = _count(_open_inquiry_count_stmt())

    board_counts = {
        board_type: _count(
            select(func.count(Post.id)).where(
                Post.is_deleted.is_(False),
                Post.board_type == board_type,
            )
        )
        for board_type in PostBoardType.ALL
    }

    latest_inquiries = [
        _serialize_admin_post(row, include_inquiry_status=True)
        for row in _latest_posts_stmt(PostBoardType.INQUIRY, 5)
    ]
    latest_posts = [
        _serialize_admin_post(row)
        for row in _latest_posts_stmt(None, 6)
    ]

    return {
        "metrics": {
            "total_users": total_users,
            "active_users": active_users,
            "total_posts": total_posts,
            "hidden_posts": hidden_posts,
            "hidden_comments": hidden_comments,
            "open_inquiries": open_inquiries,
        },
        "board_counts": board_counts,
        "latest_inquiries": latest_inquiries,
        "latest_posts": latest_posts,
    }


def list_users(page=1, size=DEFAULT_PAGE_SIZE, keyword=None, role=None, active=None):
    page, size = _normalize_page(page, size)
    keyword = (keyword or "").strip()

    stmt = select(User)

    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                User.email.like(pattern),
                User.name.like(pattern),
                User.department.like(pattern),
                User.phone.like(pattern),
            )
        )

    if role in ALLOWED_ROLES:
        stmt = stmt.where(User.role == role)

    if active in {"true", "false"}:
        stmt = stmt.where(User.is_active.is_(active == "true"))

    total_count = _count(select(func.count()).select_from(stmt.subquery()))
    users = db.session.execute(
        stmt.order_by(User.created_at.desc(), User.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).scalars().all()

    return _paginated([_serialize_user(user) for user in users], page, size, total_count, "users")


def create_user(data):
    email = _normalize_required(data.get("email"), "email", "이메일을 입력해주세요.")
    name = _normalize_required(data.get("name"), "name", "이름을 입력해주세요.")
    password = str(data.get("password") or "")
    role = data.get("role") or UserRole.VIEWER

    if not EMAIL_PATTERN.match(email):
        raise ValidationError({"email": "유효한 이메일을 입력해주세요."})

    if role not in ALLOWED_ROLES:
        raise ValidationError({"role": "유효하지 않은 역할입니다."})

    if len(password) < 8:
        raise ValidationError({"password": "비밀번호는 8자 이상 입력해주세요."})

    if db.session.execute(select(User.id).where(User.email == email)).first():
        raise ValidationError({"email": "이미 가입된 이메일입니다."})

    user = User(
        email=email,
        name=name,
        role=role,
        provider=AuthProvider.LOCAL,
        department=_normalize_optional(data.get("department")),
        phone=_normalize_optional(data.get("phone")),
        is_active=bool(data.get("is_active", True)),
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()
    return _serialize_user(user)


def get_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        raise ValidationError({"user_id": "사용자를 찾을 수 없습니다."})

    return _serialize_user(user)


def update_user(user_id, data, actor_id):
    user = db.session.get(User, user_id)
    if user is None:
        raise ValidationError({"user_id": "사용자를 찾을 수 없습니다."})

    if "email" in data:
        email = _normalize_required(data.get("email"), "email", "이메일을 입력해주세요.")
        if not EMAIL_PATTERN.match(email):
            raise ValidationError({"email": "유효한 이메일을 입력해주세요."})

        duplicate = db.session.execute(
            select(User.id).where(User.email == email, User.id != user.id)
        ).first()
        if duplicate:
            raise ValidationError({"email": "이미 가입된 이메일입니다."})
        user.email = email

    if "name" in data:
        user.name = _normalize_required(data.get("name"), "name", "이름을 입력해주세요.")

    if "department" in data:
        user.department = _normalize_optional(data.get("department"))

    if "phone" in data:
        user.phone = _normalize_optional(data.get("phone"))

    if "role" in data:
        role = data.get("role")
        if role not in ALLOWED_ROLES:
            raise ValidationError({"role": "유효하지 않은 역할입니다."})
        if user.id == actor_id and role != UserRole.ADMIN:
            raise ForbiddenError("본인의 관리자 권한은 직접 해제할 수 없습니다.")
        user.role = role

    if "is_active" in data:
        is_active = bool(data.get("is_active"))
        if user.id == actor_id and not is_active:
            raise ForbiddenError("본인 계정은 비활성화할 수 없습니다.")
        user.is_active = is_active

    password = str(data.get("password") or "")
    if password:
        if user.provider != AuthProvider.LOCAL:
            raise ValidationError(
                {"password": "소셜 로그인 계정은 비밀번호를 변경할 수 없습니다."}
            )

        if len(password) < 8:
            raise ValidationError({"password": "비밀번호는 8자 이상 입력해주세요."})
        user.set_password(password)

    db.session.commit()
    return _serialize_user(user)


def update_user_role(user_id, role, actor_id):
    if role not in ALLOWED_ROLES:
        raise ValidationError({"role": "유효하지 않은 역할입니다."})

    user = db.session.get(User, user_id)
    if user is None:
        raise ValidationError({"user_id": "사용자를 찾을 수 없습니다."})

    if user.id == actor_id and role != UserRole.ADMIN:
        raise ForbiddenError("본인의 관리자 권한은 직접 해제할 수 없습니다.")

    user.role = role
    db.session.commit()
    return _serialize_user(user)


def update_user_active(user_id, is_active, actor_id):
    user = db.session.get(User, user_id)
    if user is None:
        raise ValidationError({"user_id": "사용자를 찾을 수 없습니다."})

    if user.id == actor_id and not is_active:
        raise ForbiddenError("본인 계정은 비활성화할 수 없습니다.")

    user.is_active = bool(is_active)
    db.session.commit()
    return _serialize_user(user)


def list_posts(page=1, size=DEFAULT_PAGE_SIZE, keyword=None, board_type=None, visibility=None):
    page, size = _normalize_page(page, size)
    keyword = (keyword or "").strip()

    stmt = _admin_post_select()

    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                Post.title.like(pattern),
                Post.content.like(pattern),
                User.name.like(pattern),
                User.email.like(pattern),
            )
        )

    if board_type in ALLOWED_BOARD_TYPES:
        stmt = stmt.where(Post.board_type == board_type)

    if visibility == "hidden":
        stmt = stmt.where(Post.is_hidden.is_(True))
    elif visibility == "visible":
        stmt = stmt.where(Post.is_hidden.is_(False))

    total_count = _count(select(func.count()).select_from(stmt.subquery()))
    rows = db.session.execute(
        stmt.order_by(Post.created_at.desc(), Post.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()

    return _paginated([_serialize_admin_post(row) for row in rows], page, size, total_count, "posts")


def list_inquiries(page=1, size=DEFAULT_PAGE_SIZE, keyword=None, status=None):
    page, size = _normalize_page(page, size)
    keyword = (keyword or "").strip()

    stmt = _admin_post_select().where(Post.board_type == PostBoardType.INQUIRY)

    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                Post.title.like(pattern),
                Post.content.like(pattern),
                User.name.like(pattern),
                User.email.like(pattern),
            )
        )

    if status == "open":
        stmt = stmt.where(_admin_comment_count_expr() == 0)
    elif status == "answered":
        stmt = stmt.where(_admin_comment_count_expr() > 0)

    total_count = _count(select(func.count()).select_from(stmt.subquery()))
    rows = db.session.execute(
        stmt.order_by(Post.created_at.desc(), Post.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()

    return _paginated(
        [_serialize_admin_post(row, include_inquiry_status=True) for row in rows],
        page,
        size,
        total_count,
        "inquiries",
    )


def answer_inquiry(post_id, admin_id, content):
    post = db.session.get(Post, post_id)
    if post is None or post.is_deleted:
        raise ValidationError({"post_id": "문의를 찾을 수 없습니다."})

    if post.board_type != PostBoardType.INQUIRY:
        raise ValidationError({"post_id": "문의 게시글만 답변할 수 있습니다."})

    return comment_service.create_comment(
        post_id=post_id,
        user_id=admin_id,
        role=UserRole.ADMIN,
        data={"content": content},
    )


def _normalize_page(page, size):
    page = max(page or 1, 1)
    size = min(max(size or DEFAULT_PAGE_SIZE, 1), MAX_PAGE_SIZE)
    return page, size


def _normalize_required(value, field, message):
    normalized = str(value or "").strip()
    if not normalized:
        raise ValidationError({field: message})
    return normalized


def _normalize_optional(value):
    normalized = str(value or "").strip()
    return normalized or None


def _count(stmt):
    return db.session.execute(stmt).scalar_one()


def _paginated(items, page, size, total_count, key):
    total_pages = (total_count + size - 1) // size if total_count else 0
    return {
        key: items,
        "pagination": {
            "current_page": page,
            "size": size,
            "total_count": total_count,
            "total_pages": total_pages,
        },
    }


def _admin_comment_count_expr():
    return (
        select(func.count(Comment.id))
        .join(User, User.id == Comment.author_id)
        .where(
            Comment.post_id == Post.id,
            Comment.is_deleted.is_(False),
            User.role == UserRole.ADMIN,
        )
        .correlate(Post)
        .scalar_subquery()
    )


def _visible_comment_count_expr():
    return (
        select(func.count(Comment.id))
        .where(
            Comment.post_id == Post.id,
            Comment.is_deleted.is_(False),
            Comment.is_hidden.is_(False),
        )
        .correlate(Post)
        .scalar_subquery()
    )


def _admin_post_select():
    return (
        select(
            Post,
            User.name.label("author_name"),
            User.email.label("author_email"),
            _visible_comment_count_expr().label("comment_count"),
            _admin_comment_count_expr().label("admin_comment_count"),
        )
        .join(User, User.id == Post.author_id)
        .where(Post.is_deleted.is_(False))
    )


def _latest_posts_stmt(board_type, limit):
    stmt = _admin_post_select()
    if board_type:
        stmt = stmt.where(Post.board_type == board_type)
    return db.session.execute(stmt.order_by(Post.created_at.desc()).limit(limit)).all()


def _open_inquiry_count_stmt():
    return (
        select(func.count(Post.id))
        .where(
            Post.is_deleted.is_(False),
            Post.board_type == PostBoardType.INQUIRY,
            _admin_comment_count_expr() == 0,
        )
    )


def _serialize_user(user):
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "provider": user.provider,
        "department": user.department,
        "phone": user.phone,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


def _serialize_admin_post(row, include_inquiry_status=False):
    post = row.Post
    admin_comment_count = int(row.admin_comment_count)
    data = {
        "id": post.id,
        "title": post.title,
        "author_name": row.author_name,
        "author_email": row.author_email,
        "board_type": post.board_type,
        "is_important": post.is_important,
        "is_hidden": post.is_hidden,
        "view_count": post.view_count,
        "comment_count": int(row.comment_count),
        "admin_comment_count": admin_comment_count,
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "updated_at": post.updated_at.isoformat() if post.updated_at else None,
    }

    if include_inquiry_status:
        data["inquiry_status"] = "answered" if admin_comment_count > 0 else "open"

    return data
