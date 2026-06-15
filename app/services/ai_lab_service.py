import hashlib

MOCK_RESULTS = {
    "rt-detr": {
        "inference_ms": 18.9,
        "fps": 53,
        "detections": [
            {"label": "SMOKE", "confidence": 0.87, "bbox": [0.05, 0.05, 0.55, 0.45]},
            {"label": "FIRE", "confidence": 0.92, "bbox": [0.15, 0.40, 0.40, 0.50]},
        ],
    },
    "yolov8": {
        "inference_ms": 12.5,
        "fps": 79,
        "detections": [
            {"label": "SMOKE", "confidence": 0.80, "bbox": [0.08, 0.04, 0.58, 0.48]},
            {"label": "FIRE", "confidence": 0.88, "bbox": [0.18, 0.42, 0.42, 0.48]},
        ],
    },
    "yolov11": {
        "inference_ms": 10.0,
        "fps": 100,
        "detections": [
            {"label": "SMOKE", "confidence": 0.89, "bbox": [0.06, 0.05, 0.56, 0.46]},
            {"label": "FIRE", "confidence": 0.94, "bbox": [0.16, 0.41, 0.41, 0.49]},
        ],
    },
}


def detect(image_key, models, threshold):
    """선택된 모델별 Mock 탐지 결과를 threshold로 필터링해 반환한다."""
    image_key = image_key or "uploaded"
    results = {}

    for model_key in models:
        base = MOCK_RESULTS[model_key]
        jitter = _jitter(image_key, model_key)

        detections = []
        for detection in base["detections"]:
            confidence = round(_clamp(detection["confidence"] + jitter, 0.0, 0.99), 2)
            if confidence < threshold:
                continue

            detections.append(
                {
                    "label": detection["label"],
                    "confidence": confidence,
                    "bbox": detection["bbox"],
                }
            )

        results[model_key] = {
            "inference_ms": base["inference_ms"],
            "fps": base["fps"],
            "detections": detections,
        }

    return results


def _jitter(image_key, model_key):
    # 이미지별/모델별로 결정적인 ±0.04 confidence 편차를 부여해 "이미지마다 약간씩
    # 다른 결과"를 재현한다 (실제 추론 미구현 단계의 Mock 데이터 보강용).
    digest = hashlib.sha1(f"{image_key}:{model_key}".encode()).hexdigest()
    ratio = int(digest[:4], 16) / 0xFFFF
    return round((ratio - 0.5) * 0.08, 3)


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))
