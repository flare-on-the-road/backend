from flask_jwt_extended import create_access_token

from app.common.constants import AdminAccessRequestStatus, UserRole
from app.extensions import db
from app.models.user import User


def _auth_header(user):
    token = create_access_token(
        identity=str(user.id),
        additional_claims={"email": user.email, "name": user.name, "role": user.role},
    )
    return {"Authorization": f"Bearer {token}"}


def test_user_can_request_admin_board_access_and_admin_can_approve(
    client,
    app,
    user,
    user_headers,
    admin_headers,
):
    res = client.post(
        "/api/admin/access-requests",
        json={"reason": "QA 확인용"},
        headers=user_headers,
    )

    assert res.status_code == 201
    body = res.get_json()
    assert body["status"] == AdminAccessRequestStatus.PENDING
    assert body["requester_email"] == user.email

    list_res = client.get("/api/admin/access-requests", headers=admin_headers)
    assert list_res.status_code == 200
    request_id = list_res.get_json()["requests"][0]["id"]

    review_res = client.patch(
        f"/api/admin/access-requests/{request_id}",
        json={"status": AdminAccessRequestStatus.APPROVED},
        headers=admin_headers,
    )

    assert review_res.status_code == 200
    assert review_res.get_json()["status"] == AdminAccessRequestStatus.APPROVED

    db.session.refresh(user)
    assert user.role == UserRole.ADMIN_VIEWER


def test_admin_viewer_can_read_admin_board_but_cannot_manage_users_or_posts(
    client,
    app,
):
    member = User(
        email="member@example.com",
        name="member",
        phone="010-1234-5678",
        role=UserRole.VIEWER,
    )
    admin_viewer = User(
        email="viewer-admin@example.com",
        name="read_only_admin",
        role=UserRole.ADMIN_VIEWER,
    )
    db.session.add(member)
    db.session.add(admin_viewer)
    db.session.commit()
    headers = _auth_header(admin_viewer)

    summary_res = client.get("/api/admin/summary", headers=headers)
    posts_res = client.get("/api/admin/posts", headers=headers)
    users_res = client.get("/api/admin/users", headers=headers)
    hide_res = client.patch("/api/admin/posts/1/hide", headers=headers)

    assert summary_res.status_code == 200
    assert posts_res.status_code == 200
    assert users_res.status_code == 200
    users = users_res.get_json()["users"]
    member_row = next(row for row in users if row["name"] == "member")
    assert member_row["email"] == "me****@example.com"
    assert member_row["phone"] == "010-****-5678"
    assert hide_res.status_code == 403


def test_visit_tracking_counts_daily_unique_visitors(client, admin_headers):
    first = client.post(
        "/api/visits",
        json={"visitorKey": "browser-1", "path": "/"},
    )
    duplicate = client.post(
        "/api/visits",
        json={"visitorKey": "browser-1", "path": "/overview"},
    )
    second = client.post(
        "/api/visits",
        json={"visitorKey": "browser-2", "path": "/login"},
    )

    assert first.status_code == 200
    assert first.get_json()["recorded"] is True
    assert duplicate.status_code == 200
    assert duplicate.get_json()["recorded"] is False
    assert second.status_code == 200
    assert second.get_json()["recorded"] is True

    summary = client.get("/api/admin/summary", headers=admin_headers)
    assert summary.status_code == 200
    metrics = summary.get_json()["metrics"]
    assert metrics["today_visitors"] == 2
    assert metrics["total_visitors"] == 2
