from app.extensions import db


def test_change_password_success(client, user, user_headers):
    user.set_password("oldPassword123")
    db.session.add(user)
    db.session.commit()

    res = client.patch(
        "/api/users/me/password",
        json={
            "currentPassword": "oldPassword123",
            "newPassword": "newPassword123",
            "newPasswordConfirm": "newPassword123",
        },
        headers=user_headers,
    )

    db.session.refresh(user)

    assert res.status_code == 200
    assert res.get_json()["data"] == {"changed": True}
    assert user.check_password("newPassword123")


def test_change_password_rejects_wrong_current_password(client, user, user_headers):
    user.set_password("oldPassword123")
    db.session.add(user)
    db.session.commit()

    res = client.patch(
        "/api/users/me/password",
        json={
            "currentPassword": "wrongPassword123",
            "newPassword": "newPassword123",
            "newPasswordConfirm": "newPassword123",
        },
        headers=user_headers,
    )

    db.session.refresh(user)

    assert res.status_code == 400
    assert res.get_json()["message"] == "현재 비밀번호가 올바르지 않습니다."
    assert user.check_password("oldPassword123")
