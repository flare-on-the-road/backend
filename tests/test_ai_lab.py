import base64


class FakeVisionResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "detections": [
                {
                    "class_name": "fire",
                    "confidence": 0.812345,
                    "bbox_normalized": {
                        "x1": 0.1,
                        "y1": 0.2,
                        "x2": 0.4,
                        "y2": 0.7,
                    },
                },
                {
                    "class_name": "carlight",
                    "confidence": 0.95,
                    "bbox_normalized": {
                        "x1": 0.5,
                        "y1": 0.5,
                        "x2": 0.6,
                        "y2": 0.6,
                    },
                },
            ]
        }


class FakeNonJsonVisionResponse:
    def raise_for_status(self):
        return None

    def json(self):
        raise ValueError("not json")


class FakeSampleImageResponse:
    def __init__(self, status_code=200, content=b"fake-remote-sample-image-bytes"):
        self.status_code = status_code
        self.content = content


def test_ai_lab_detect_calls_vision_api(client, app, user_headers, monkeypatch):
    calls = []

    app.config["VISION_API_URL"] = "http://vision-api:8000"

    def fake_post(url, files, data, timeout):
        calls.append({"url": url, "files": files, "data": data, "timeout": timeout})
        return FakeVisionResponse()

    monkeypatch.setattr("app.services.ai_lab_service.requests.post", fake_post)

    image_base64 = base64.b64encode(b"fake-image-bytes").decode()
    response = client.post(
        "/api/ai-lab/detect",
        json={
            "models": ["rt-detr"],
            "threshold": 0.3,
            "image_base64": image_base64,
        },
        headers=user_headers,
    )

    assert response.status_code == 200
    assert calls[0]["url"] == "http://vision-api:8000/predict"
    assert calls[0]["data"]["model_key"] == "rt-detr"
    assert calls[0]["data"]["confidence"] == 0.3

    result = response.get_json()["results"]["rt-detr"]
    assert result["detections"] == [
        {
            "label": "FIRE",
            "confidence": 0.8123,
            "bbox": [0.1, 0.2, 0.3, 0.5],
        }
    ]
    assert result["inference_ms"] >= 0
    assert result["fps"] >= 0


def test_ai_lab_detect_calls_vision_api_for_each_model(client, app, user_headers, monkeypatch):
    calls = []

    app.config["VISION_API_URL"] = "http://vision-api:8000"

    def fake_post(url, files, data, timeout):
        calls.append({"url": url, "files": files, "data": data, "timeout": timeout})
        return FakeVisionResponse()

    monkeypatch.setattr("app.services.ai_lab_service.requests.post", fake_post)

    image_base64 = base64.b64encode(b"fake-image-bytes").decode()
    response = client.post(
        "/api/ai-lab/detect",
        json={
            "models": ["rt-detr", "yolov8", "yolov11"],
            "threshold": 0.3,
            "image_base64": image_base64,
        },
        headers=user_headers,
    )

    assert response.status_code == 200
    assert [call["data"]["model_key"] for call in calls] == [
        "rt-detr",
        "yolov8",
        "yolov11",
    ]
    assert set(response.get_json()["results"].keys()) == {
        "rt-detr",
        "yolov8",
        "yolov11",
    }


def test_ai_lab_detect_accepts_sample_image_key(client, app, user_headers, monkeypatch, tmp_path):
    calls = []

    sample_dir = tmp_path / "samples"
    sample_dir.mkdir()
    (sample_dir / "sample_1.png").write_bytes(b"fake-sample-image-bytes")

    app.config["VISION_API_URL"] = "http://vision-api:8000"
    app.config["VISION_SAMPLE_IMAGE_DIR"] = str(sample_dir)

    def fake_post(url, files, data, timeout):
        calls.append({"url": url, "files": files, "data": data, "timeout": timeout})
        return FakeVisionResponse()

    monkeypatch.setattr("app.services.ai_lab_service.requests.post", fake_post)

    response = client.post(
        "/api/ai-lab/detect",
        json={
            "models": ["rt-detr"],
            "threshold": 0.3,
            "image_key": "sample_1",
        },
        headers=user_headers,
    )

    assert response.status_code == 200
    assert calls[0]["files"]["image"][1] == b"fake-sample-image-bytes"


def test_ai_lab_detect_accepts_camel_case_image_key(client, app, user_headers, monkeypatch, tmp_path):
    calls = []

    sample_dir = tmp_path / "samples"
    sample_dir.mkdir()
    (sample_dir / "sample_1.png").write_bytes(b"fake-sample-image-bytes")

    app.config["VISION_API_URL"] = "http://vision-api:8000"
    app.config["VISION_SAMPLE_IMAGE_DIR"] = str(sample_dir)

    def fake_post(url, files, data, timeout):
        calls.append({"url": url, "files": files, "data": data, "timeout": timeout})
        return FakeVisionResponse()

    monkeypatch.setattr("app.services.ai_lab_service.requests.post", fake_post)

    response = client.post(
        "/api/ai-lab/detect",
        json={
            "models": ["rt-detr"],
            "threshold": 0.3,
            "imageKey": "sample_1",
        },
        headers=user_headers,
    )

    assert response.status_code == 200
    assert calls[0]["files"]["image"][1] == b"fake-sample-image-bytes"


def test_ai_lab_detect_finds_sample_when_config_points_to_ai_lab_dir(
    client,
    app,
    user_headers,
    monkeypatch,
    tmp_path,
):
    calls = []

    ai_lab_dir = tmp_path / "ai-lab"
    sample_dir = ai_lab_dir / "samples"
    sample_dir.mkdir(parents=True)
    (sample_dir / "sample_1.png").write_bytes(b"fake-sample-image-bytes")

    app.config["VISION_API_URL"] = "http://vision-api:8000"
    app.config["VISION_SAMPLE_IMAGE_DIR"] = str(ai_lab_dir)

    def fake_post(url, files, data, timeout):
        calls.append({"url": url, "files": files, "data": data, "timeout": timeout})
        return FakeVisionResponse()

    monkeypatch.setattr("app.services.ai_lab_service.requests.post", fake_post)

    response = client.post(
        "/api/ai-lab/detect",
        json={
            "models": ["rt-detr"],
            "threshold": 0.3,
            "image_key": "sample_1",
        },
        headers=user_headers,
    )

    assert response.status_code == 200
    assert calls[0]["files"]["image"][1] == b"fake-sample-image-bytes"


def test_ai_lab_detect_fetches_sample_from_frontend_url_when_file_is_missing(
    client,
    app,
    user_headers,
    monkeypatch,
    tmp_path,
):
    calls = []
    get_urls = []

    app.config["VISION_API_URL"] = "http://vision-api:8000"
    app.config["VISION_SAMPLE_IMAGE_DIR"] = str(tmp_path / "missing-samples")
    app.config["FRONTEND_URL"] = "http://frontend:3000"

    def fake_get(url, timeout):
        get_urls.append(url)
        if url.endswith("/sample_remote.png"):
            return FakeSampleImageResponse()
        return FakeSampleImageResponse(status_code=404, content=b"")

    def fake_post(url, files, data, timeout):
        calls.append({"url": url, "files": files, "data": data, "timeout": timeout})
        return FakeVisionResponse()

    monkeypatch.setattr("app.services.ai_lab_service.requests.get", fake_get)
    monkeypatch.setattr("app.services.ai_lab_service.requests.post", fake_post)

    response = client.post(
        "/api/ai-lab/detect",
        json={
            "models": ["rt-detr"],
            "threshold": 0.3,
            "image_key": "sample_remote",
        },
        headers=user_headers,
    )

    assert response.status_code == 200
    assert get_urls == [
        "http://frontend:3000/ai-lab/samples/sample_remote.jpg",
        "http://frontend:3000/ai-lab/samples/sample_remote.jpeg",
        "http://frontend:3000/ai-lab/samples/sample_remote.png",
    ]
    assert calls[0]["files"]["image"][1] == b"fake-remote-sample-image-bytes"


def test_ai_lab_detect_requires_vision_api_url(client, user_headers):
    image_base64 = base64.b64encode(b"fake-image-bytes").decode()
    response = client.post(
        "/api/ai-lab/detect",
        json={
            "models": ["rt-detr"],
            "threshold": 0.3,
            "image_base64": image_base64,
        },
        headers=user_headers,
    )

    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "VISION_API_UNAVAILABLE"


def test_ai_lab_detect_handles_non_json_vision_response(
    client,
    app,
    user_headers,
    monkeypatch,
):
    app.config["VISION_API_URL"] = "http://vision-api:8000"

    def fake_post(url, files, data, timeout):
        return FakeNonJsonVisionResponse()

    monkeypatch.setattr("app.services.ai_lab_service.requests.post", fake_post)

    image_base64 = base64.b64encode(b"fake-image-bytes").decode()
    response = client.post(
        "/api/ai-lab/detect",
        json={
            "models": ["rt-detr"],
            "threshold": 0.3,
            "image_base64": image_base64,
        },
        headers=user_headers,
    )

    assert response.status_code == 503
    payload = response.get_json()
    assert payload["error"]["code"] == "VISION_API_UNAVAILABLE"
    assert "JSON이 아닌 응답" in payload["error"]["details"]["reason"]
