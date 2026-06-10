import requests
from flask import current_app


DEFAULT_BOUNDS = {
    "minX": 124.0,
    "maxX": 132.0,
    "minY": 33.0,
    "maxY": 39.5,
}


def get_cctvs(
    min_x=None,
    max_x=None,
    min_y=None,
    max_y=None,
    cctv_type="all",
    limit=500,
):
    api_key = current_app.config["ITS_API_KEY"]
    api_url = current_app.config["ITS_CCTV_API_URL"]

    if not api_key or not api_url:
        raise ValueError("ITS CCTV API 설정이 누락되었습니다.")

    params = {
        "apiKey": api_key,
        "type": "all",
        "minX": min_x if min_x is not None else DEFAULT_BOUNDS["minX"],
        "maxX": max_x if max_x is not None else DEFAULT_BOUNDS["maxX"],
        "minY": min_y if min_y is not None else DEFAULT_BOUNDS["minY"],
        "maxY": max_y if max_y is not None else DEFAULT_BOUNDS["maxY"],
        "getType": "json",
    }

    params["cctvType"] = "1" if cctv_type == "all" else cctv_type

    response = requests.get(api_url, params=params, timeout=12)
    response.raise_for_status()

    payload = response.json()
    if isinstance(payload, dict) and "response" in payload:
        payload = payload["response"]

    raw_items = payload.get("data", []) if isinstance(payload, dict) else []
    items = [normalize_cctv(item) for item in raw_items if isinstance(item, dict)]
    items = [item for item in items if item["streamUrl"] and item["lat"] and item["lng"]]

    return {
        "items": items[:limit],
        "total": len(items),
        "bounds": {
            "minX": float(params["minX"]),
            "maxX": float(params["maxX"]),
            "minY": float(params["minY"]),
            "maxY": float(params["maxY"]),
        },
    }


def normalize_cctv(item):
    name = item.get("cctvname") or item.get("cctvName") or "이름 없는 CCTV"
    coord_x = item.get("coordx") or item.get("coordX") or item.get("x")
    coord_y = item.get("coordy") or item.get("coordY") or item.get("y")

    return {
        "id": f"{name}-{coord_x}-{coord_y}",
        "name": name,
        "roadName": item.get("roadsectionid") or item.get("roadName") or "",
        "streamUrl": item.get("cctvurl") or item.get("cctvUrl") or "",
        "format": item.get("cctvformat") or item.get("cctvFormat") or "",
        "type": str(item.get("cctvtype") or item.get("cctvType") or ""),
        "lat": _to_float(coord_y),
        "lng": _to_float(coord_x),
    }


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
