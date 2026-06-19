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
