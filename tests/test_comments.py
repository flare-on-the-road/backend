def _create_post(client, headers, title="제목", content="내용"):
    res = client.post("/api/posts", json={"title": title, "content": content}, headers=headers)
    return res.get_json()["id"]


def _create_comment(client, headers, post_id, content, parent_id=None):
    payload = {"content": content}
    if parent_id is not None:
        payload["parent_id"] = parent_id
    return client.post(f"/api/posts/{post_id}/comments", json=payload, headers=headers)


def test_create_and_list_comment_tree(client, user_headers, other_headers):
    post_id = _create_post(client, user_headers)

    res = _create_comment(client, other_headers, post_id, "저도 재현됩니다")
    assert res.status_code == 201

    res_tree = client.get(f"/api/posts/{post_id}/comments", headers=user_headers)
    body = res_tree.get_json()
    assert body["total_count"] == 1
    assert body["comments"][0]["content"] == "저도 재현됩니다"
    assert body["comments"][0]["author_nickname"] == "qa_lee"
    assert body["comments"][0]["replies"] == []


def test_comment_validation_error(client, user_headers):
    post_id = _create_post(client, user_headers)

    res = _create_comment(client, user_headers, post_id, "   ")
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_reply_depth_limit(client, user_headers, other_headers):
    post_id = _create_post(client, user_headers)

    top_res = _create_comment(client, user_headers, post_id, "최상위 댓글")
    top_id = top_res.get_json()["id"]

    reply_res = _create_comment(client, other_headers, post_id, "대댓글", parent_id=top_id)
    assert reply_res.status_code == 201
    reply_id = reply_res.get_json()["id"]

    deep_res = _create_comment(client, user_headers, post_id, "대대댓글", parent_id=reply_id)
    assert deep_res.status_code == 400
    assert deep_res.get_json()["error"]["code"] == "MAX_DEPTH_EXCEEDED"


def test_invalid_parent_other_post(client, user_headers):
    post1_id = _create_post(client, user_headers, title="글1")
    post2_id = _create_post(client, user_headers, title="글2")

    comment_res = _create_comment(client, user_headers, post1_id, "댓글")
    comment_id = comment_res.get_json()["id"]

    res = _create_comment(client, user_headers, post2_id, "다른 글의 댓글에 대댓글", parent_id=comment_id)
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "INVALID_PARENT"


def test_comment_update_delete_owner_only(client, user_headers, other_headers):
    post_id = _create_post(client, user_headers)
    comment_res = _create_comment(client, user_headers, post_id, "원본 댓글")
    comment_id = comment_res.get_json()["id"]

    res_other = client.put(
        f"/api/comments/{comment_id}", json={"content": "수정 시도"}, headers=other_headers
    )
    assert res_other.status_code == 403
    assert res_other.get_json()["error"]["code"] == "FORBIDDEN"

    res_owner = client.put(
        f"/api/comments/{comment_id}", json={"content": "수정됨"}, headers=user_headers
    )
    assert res_owner.status_code == 200

    res_delete_other = client.delete(f"/api/comments/{comment_id}", headers=other_headers)
    assert res_delete_other.status_code == 403

    res_delete_owner = client.delete(f"/api/comments/{comment_id}", headers=user_headers)
    assert res_delete_owner.status_code == 200


def test_deleted_comment_masked_when_has_replies(client, user_headers, other_headers):
    post_id = _create_post(client, user_headers)
    comment_res = _create_comment(client, user_headers, post_id, "원본 댓글")
    comment_id = comment_res.get_json()["id"]

    _create_comment(client, other_headers, post_id, "대댓글", parent_id=comment_id)
    client.delete(f"/api/comments/{comment_id}", headers=user_headers)

    res_tree = client.get(f"/api/posts/{post_id}/comments", headers=user_headers)
    comments = res_tree.get_json()["comments"]
    assert len(comments) == 1
    assert comments[0]["content"] == "삭제된 댓글입니다"
    assert comments[0]["is_deleted"] is True
    assert len(comments[0]["replies"]) == 1


def test_deleted_comment_excluded_when_no_replies(client, user_headers):
    post_id = _create_post(client, user_headers)
    comment_res = _create_comment(client, user_headers, post_id, "삭제될 댓글")
    comment_id = comment_res.get_json()["id"]

    client.delete(f"/api/comments/{comment_id}", headers=user_headers)

    res_tree = client.get(f"/api/posts/{post_id}/comments", headers=user_headers)
    assert res_tree.get_json()["comments"] == []


def test_hide_unhide_comment_admin_only_and_masking(client, user_headers, other_headers, admin_headers):
    post_id = _create_post(client, user_headers)
    comment_res = _create_comment(client, other_headers, post_id, "가려질 댓글")
    comment_id = comment_res.get_json()["id"]

    res_forbidden = client.patch(f"/api/comments/{comment_id}/hide", headers=user_headers)
    assert res_forbidden.status_code == 403
    assert res_forbidden.get_json()["error"]["code"] == "FORBIDDEN"

    res_hide = client.patch(f"/api/comments/{comment_id}/hide", headers=admin_headers)
    assert res_hide.status_code == 200

    # 일반 사용자(작성자/관리자 아님)에게는 마스킹
    res_tree_user = client.get(f"/api/posts/{post_id}/comments", headers=user_headers)
    node = res_tree_user.get_json()["comments"][0]
    assert node["content"] == "관리자에 의해 가려진 댓글입니다"
    assert node["author_nickname"] is None
    assert node["is_hidden"] is True
    assert node["permissions"] == {"can_edit": False, "can_delete": False, "can_hide": False}

    # 작성자 본인에게는 원본 + 가림 배지
    res_tree_author = client.get(f"/api/posts/{post_id}/comments", headers=other_headers)
    node_author = res_tree_author.get_json()["comments"][0]
    assert node_author["content"] == "가려질 댓글"
    assert node_author["is_hidden"] is True

    # 작성자도 가려진 댓글은 수정/삭제 불가
    res_edit = client.put(
        f"/api/comments/{comment_id}", json={"content": "수정시도"}, headers=other_headers
    )
    assert res_edit.status_code == 403

    res_unhide = client.patch(f"/api/comments/{comment_id}/unhide", headers=admin_headers)
    assert res_unhide.status_code == 200

    res_tree_after = client.get(f"/api/posts/{post_id}/comments", headers=user_headers)
    assert res_tree_after.get_json()["comments"][0]["content"] == "가려질 댓글"


def test_cannot_reply_to_hidden_comment(client, user_headers, other_headers, admin_headers):
    post_id = _create_post(client, user_headers)
    comment_res = _create_comment(client, user_headers, post_id, "댓글")
    comment_id = comment_res.get_json()["id"]

    client.patch(f"/api/comments/{comment_id}/hide", headers=admin_headers)

    res = _create_comment(client, other_headers, post_id, "대댓글 시도", parent_id=comment_id)
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "INVALID_PARENT"


def test_comments_on_hidden_post_forbidden_for_others(client, user_headers, other_headers, admin_headers):
    post_id = _create_post(client, user_headers)
    client.patch(f"/api/posts/{post_id}/hide", headers=admin_headers)

    res_get = client.get(f"/api/posts/{post_id}/comments", headers=other_headers)
    assert res_get.status_code == 403

    res_create = _create_comment(client, other_headers, post_id, "댓글 시도")
    assert res_create.status_code == 403

    # 작성자 본인과 관리자는 접근 가능
    res_owner = client.get(f"/api/posts/{post_id}/comments", headers=user_headers)
    assert res_owner.status_code == 200

    res_admin = client.get(f"/api/posts/{post_id}/comments", headers=admin_headers)
    assert res_admin.status_code == 200
