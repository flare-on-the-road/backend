import base64
import time
from pathlib import Path
from typing import Any

import requests
from flask import current_app

from app.common.errors import ValidationError, VisionApiUnavailableError


SAMPLE_EXTENSIONS = ("jpg", "jpeg", "png")


def detect(image_key, image_base64, models, threshold):
    """Vision FastAPI 서버를 호출하고 프론트의 AI Lab 응답 형태로 변환한다."""
    image_bytes = _resolve_image_bytes(image_key=image_key, image_base64=image_base64)
    results = {}

    for model_key in models:
        raw_result, elapsed_ms = _call_vision_api(
            image_bytes=image_bytes,
            model_key=model_key,
            confidence=threshold,
        )
        results[model_key] = _to_model_result(raw_result, elapsed_ms)

    return results


def _resolve_image_bytes(image_key, image_base64):
    if image_base64:
        try:
            if "," in image_base64:
                image_base64 = image_base64.split(",", 1)[1]
            return base64.b64decode(image_base64, validate=True)
        except Exception:
            raise ValidationError({"image_base64": "올바른 base64 이미지가 아닙니다."})

    sample_path = _find_sample_image(image_key)
    if sample_path is not None:
        return sample_path.read_bytes()

    sample_bytes = _fetch_sample_image(image_key)
    if sample_bytes is None:
        searched_dirs = [str(path) for path in _sample_image_dirs()]
        searched_urls = _sample_image_urls(image_key)
        raise ValidationError(
            {
                "image_key": "샘플 이미지를 찾을 수 없습니다.",
                "searched_dirs": ", ".join(searched_dirs),
                "searched_urls": ", ".join(searched_urls),
            }
        )

    return sample_bytes


def _find_sample_image(image_key):
    if not image_key or "/" in image_key or "\\" in image_key or ".." in image_key:
        return None

    for sample_dir in _sample_image_dirs():
        for extension in SAMPLE_EXTENSIONS:
            candidate = sample_dir / f"{image_key}.{extension}"
            if candidate.is_file():
                return candidate

    return None


def _sample_image_dirs():
    configured_dir = Path(current_app.config["VISION_SAMPLE_IMAGE_DIR"]).expanduser()
    project_root = Path(__file__).resolve().parents[3]

    candidates = [
        configured_dir,
        configured_dir / "samples",
        project_root / "frontend" / "public" / "ai-lab" / "samples",
        project_root / "frontend" / "public" / "ai-lab",
        Path.cwd() / "frontend" / "public" / "ai-lab" / "samples",
        Path.cwd() / "frontend" / "public" / "ai-lab",
    ]

    seen = set()
    unique_candidates = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique_candidates.append(resolved)

    return unique_candidates


def _fetch_sample_image(image_key):
    for url in _sample_image_urls(image_key):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200 and response.content:
                return response.content
        except requests.exceptions.RequestException:
            continue

    return None


def _sample_image_urls(image_key):
    frontend_url = current_app.config.get("FRONTEND_URL", "").rstrip("/")
    if not frontend_url:
        return []

    return [
        f"{frontend_url}/ai-lab/samples/{image_key}.{extension}"
        for extension in SAMPLE_EXTENSIONS
    ]


def _call_vision_api(image_bytes, model_key, confidence):
    base_url = current_app.config.get("VISION_API_URL", "").rstrip("/")
    timeout = current_app.config.get("VISION_API_TIMEOUT_SECONDS", 30)

    if not base_url:
        raise VisionApiUnavailableError(
            details={"VISION_API_URL": "Vision FastAPI 서버 URL이 설정되지 않았습니다."}
        )

    start = time.perf_counter()
    try:
        response = requests.post(
            f"{base_url}/predict",
            files={"image": ("frame.jpg", image_bytes, "image/jpeg")},
            data={
                "model_key": model_key,
                "confidence": confidence,
                "max_detections": 100,
            },
            timeout=timeout,
        )
        response.raise_for_status()
        raw_result = response.json()
    except requests.exceptions.RequestException as exc:
        raise VisionApiUnavailableError(details={"reason": str(exc)})
    except ValueError:
        raise VisionApiUnavailableError(
            details={
                "reason": "Vision 모델 서버가 JSON이 아닌 응답을 반환했습니다.",
                "model_key": model_key,
            }
        )

    if not isinstance(raw_result, dict):
        raise VisionApiUnavailableError(
            details={
                "reason": "Vision 모델 서버 응답 형식이 올바르지 않습니다.",
                "model_key": model_key,
            }
        )

    elapsed_ms = (time.perf_counter() - start) * 1000
    return raw_result, elapsed_ms


def _to_model_result(raw_result: dict[str, Any], elapsed_ms: float):
    detections = []

    for detection in raw_result.get("detections", []):
        if not isinstance(detection, dict):
            continue

        class_name = detection.get("class_name", "")
        if class_name not in {"fire", "smoke"}:
            continue

        bbox = detection.get("bbox_normalized", {})
        if not isinstance(bbox, dict):
            continue

        x1 = _clamp(float(bbox.get("x1", 0.0)), 0.0, 1.0)
        y1 = _clamp(float(bbox.get("y1", 0.0)), 0.0, 1.0)
        x2 = _clamp(float(bbox.get("x2", 0.0)), 0.0, 1.0)
        y2 = _clamp(float(bbox.get("y2", 0.0)), 0.0, 1.0)

        if x2 <= x1 or y2 <= y1:
            continue

        detections.append(
            {
                "label": class_name.upper(),
                "confidence": round(float(detection.get("confidence", 0.0)), 4),
                "bbox": [
                    round(x1, 6),
                    round(y1, 6),
                    round(x2 - x1, 6),
                    round(y2 - y1, 6),
                ],
            }
        )

    fps = round(1000 / elapsed_ms, 1) if elapsed_ms > 0 else 0
    return {
        "inference_ms": round(elapsed_ms, 1),
        "fps": fps,
        "detections": detections,
    }


def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))
