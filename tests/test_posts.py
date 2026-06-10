def _create_post(client, headers, title="제목", content="내용"):
    res = client.post("/api/posts", json={"title": title, "content": content}, headers=headers)
    return res.get_json()["id"]


def test_create_post_success(client, user_headers):
    res = client.post(
        "/api/posts",
        json={"title": "로그인 버그", "content": "재현 경로: ..."},
        headers=user_headers,
    )
    assert res.status_code == 201
    assert "id" in res.get_json()


def test_create_post_validation_error(client, user_headers):
    res = client.post(
        "/api/posts",
        json={"title": "   ", "content": "내용"},
        headers=user_headers,
    )
    assert res.status_code == 400
    body = res.get_json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "title" in body["error"]["details"]


def test_requires_auth(client):
    res = client.get("/api/posts")
    assert res.status_code == 401
    assert res.get_json()["error"]["code"] == "AUTH_REQUIRED"


def test_list_pagination_and_size_clamp(client, user_headers):
    for i in range(15):
        _create_post(client, user_headers, title=f"title-{i}")

    res = client.get("/api/posts?page=1&size=10", headers=user_headers)
    body = res.get_json()
    assert len(body["posts"]) == 10
    assert body["pagination"]["total_count"] == 15
    assert body["pagination"]["total_pages"] == 2

    res2 = client.get("/api/posts?page=2&size=10", headers=user_headers)
    assert len(res2.get_json()["posts"]) == 5

    res3 = client.get("/api/posts?size=100", headers=user_headers)
    assert res3.get_json()["pagination"]["size"] == 50


def test_search_by_title_and_content(client, user_headers):
    _create_post(client, user_headers, title="버그 발생", content="아무 내용")
    _create_post(client, user_headers, title="다른 글", content="여기에 버그 키워드 포함")

    res_title = client.get("/api/posts?keyword=버그&search_type=title", headers=user_headers)
    titles = [p["title"] for p in res_title.get_json()["posts"]]
    assert titles == ["버그 발생"]

    res_content = client.get("/api/posts?keyword=버그&search_type=content", headers=user_headers)
    titles_content = [p["title"] for p in res_content.get_json()["posts"]]
    assert titles_content == ["다른 글"]


def test_get_post_increments_view_count(client, user_headers):
    post_id = _create_post(client, user_headers)

    res1 = client.get(f"/api/posts/{post_id}", headers=user_headers)
    assert res1.get_json()["view_count"] == 1

    res2 = client.get(f"/api/posts/{post_id}", headers=user_headers)
    assert res2.get_json()["view_count"] == 2
    assert res2.get_json()["permissions"] == {
        "can_edit": True,
        "can_delete": True,
        "can_hide": False,
    }


def test_get_post_not_found(client, user_headers):
    res = client.get("/api/posts/99999", headers=user_headers)
    assert res.status_code == 404
    assert res.get_json()["error"]["code"] == "POST_NOT_FOUND"


def test_update_post_owner_only(client, user_headers, other_headers):
    post_id = _create_post(client, user_headers)

    res_other = client.put(
        f"/api/posts/{post_id}",
        json={"title": "수정 시도", "content": "수정 내용"},
        headers=other_headers,
    )
    assert res_other.status_code == 403
    assert res_other.get_json()["error"]["code"] == "FORBIDDEN"

    res_owner = client.put(
        f"/api/posts/{post_id}",
        json={"title": "수정됨", "content": "수정된 내용"},
        headers=user_headers,
    )
    assert res_owner.status_code == 200


def test_admin_cannot_edit_others_post(client, user_headers, admin_headers):
    post_id = _create_post(client, user_headers)

    res = client.put(
        f"/api/posts/{post_id}",
        json={"title": "관리자 수정 시도", "content": "내용"},
        headers=admin_headers,
    )
    assert res.status_code == 403


def test_delete_post_owner_only_and_soft_delete(client, user_headers, other_headers):
    post_id = _create_post(client, user_headers)

    res_other = client.delete(f"/api/posts/{post_id}", headers=other_headers)
    assert res_other.status_code == 403

    res_owner = client.delete(f"/api/posts/{post_id}", headers=user_headers)
    assert res_owner.status_code == 200

    res_get = client.get(f"/api/posts/{post_id}", headers=user_headers)
    assert res_get.status_code == 404
    assert res_get.get_json()["error"]["code"] == "POST_NOT_FOUND"


def test_hide_unhide_post_admin_only_and_masking(client, user_headers, other_headers, admin_headers):
    post_id = _create_post(client, user_headers, title="버그 제보")

    res_forbidden = client.patch(f"/api/posts/{post_id}/hide", headers=user_headers)
    assert res_forbidden.status_code == 403
    assert res_forbidden.get_json()["error"]["code"] == "FORBIDDEN"

    res_hide = client.patch(f"/api/posts/{post_id}/hide", headers=admin_headers)
    assert res_hide.status_code == 200

    # 일반 사용자에게는 목록에서 마스킹
    res_list_other = client.get("/api/posts", headers=other_headers)
    masked = next(p for p in res_list_other.get_json()["posts"] if p["id"] == post_id)
    assert masked["title"] == "관리자에 의해 가려진 게시물입니다"
    assert masked["author_nickname"] is None

    # 작성자에게는 원본 노출
    res_list_owner = client.get("/api/posts", headers=user_headers)
    original = next(p for p in res_list_owner.get_json()["posts"] if p["id"] == post_id)
    assert original["title"] == "버그 제보"
    assert original["is_hidden"] is True

    # 타인은 상세 조회 불가
    res_detail_forbidden = client.get(f"/api/posts/{post_id}", headers=other_headers)
    assert res_detail_forbidden.status_code == 403

    # 작성자도 가려진 글은 수정/삭제 불가
    res_edit_hidden = client.put(
        f"/api/posts/{post_id}",
        json={"title": "x", "content": "y"},
        headers=user_headers,
    )
    assert res_edit_hidden.status_code == 403

    res_unhide = client.patch(f"/api/posts/{post_id}/unhide", headers=admin_headers)
    assert res_unhide.status_code == 200

    res_detail_after = client.get(f"/api/posts/{post_id}", headers=other_headers)
    assert res_detail_after.status_code == 200


def test_like_toggle(client, user_headers, other_headers):
    post_id = _create_post(client, user_headers)

    res1 = client.post(f"/api/posts/{post_id}/like", headers=other_headers)
    assert res1.get_json() == {"liked": True, "like_count": 1}

    res2 = client.post(f"/api/posts/{post_id}/like", headers=other_headers)
    assert res2.get_json() == {"liked": False, "like_count": 0}


def test_like_own_post_allowed(client, user_headers):
    post_id = _create_post(client, user_headers)

    res = client.post(f"/api/posts/{post_id}/like", headers=user_headers)
    assert res.get_json() == {"liked": True, "like_count": 1}


def test_like_hidden_post_forbidden(client, user_headers, other_headers, admin_headers):
    post_id = _create_post(client, user_headers)
    client.patch(f"/api/posts/{post_id}/hide", headers=admin_headers)

    res = client.post(f"/api/posts/{post_id}/like", headers=other_headers)
    assert res.status_code == 403
    assert res.get_json()["error"]["code"] == "FORBIDDEN"
