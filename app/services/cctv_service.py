import requests
from flask import current_app


DEFAULT_BOUNDS = {
    "minX": 124.0,
    "maxX": 132.0,
    "minY": 33.0,
    "maxY": 39.5,
}

MONITORED_CCTV_LOCATIONS = [
    {
        "id": "goduck_tunnel_1",
        "displayName": "[세종] 고덕터널(세종12)",
        "locationName": "고덕터널(세종12)",
        "searchNames": ["고덕터널(세종 12)", "세종 12)"],
        "searchRegions": [{"lat": 37.5472, "lon": 127.1562, "delta": 0.05}],
    },
    {
        "id": "dongtan_tunnel",
        "displayName": "[부산] 경부동탄터널",
        "locationName": "경부동탄터널",
        "searchNames": ["경부동탄터널(부산3)", "부산3)"],
        "searchRegions": [{"lat": 37.2001, "lon": 127.0952, "delta": 0.05}],
    },
    {
        "id": "pogok_tunnel",
        "displayName": "[세종] 포곡2터널",
        "locationName": "포곡2터널",
        "searchNames": ["포곡2터널(포천 2)", "포천 2)"],
        "searchRegions": [{"lat": 37.2816, "lon": 127.2507, "delta": 0.05}],
    },
    {
        'id': 'godeok_tunnel',
        'display_name': '[세종포천선] 고덕터널',
        'location_name': '고덕터널',
        'search_names': ['[세종] 고덕터널', '고덕터널', '세종 2'],
        'search_regions': [{'lat': 37.5436, 'lon': 127.1685, 'delta': 0.05},],
    },
    {
        "id": "dallaenae_2",
        "displayName": "[경부선] 달래내2",
        "locationName": "달래내고개",
        "searchNames": ["달래내2", "달래내"],
        "searchRegions": [{"lat": 37.4208, "lon": 127.0545, "delta": 0.05}],
    },
]


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


def get_monitored_cctvs():
    items = []

    for location in MONITORED_CCTV_LOCATIONS:
        matched = _find_monitored_cctv(location)
        if matched:
            items.append(matched)
        else:
            items.append({
                "id": location["id"],
                "name": location["displayName"],
                "roadName": location["locationName"],
                "streamUrl": "",
                "format": "",
                "type": "1",
                "lat": location["searchRegions"][0]["lat"],
                "lng": location["searchRegions"][0]["lon"],
            })

    return {
        "items": items,
        "total": len(items),
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


def _find_monitored_cctv(location):
    api_key = current_app.config["ITS_API_KEY"]
    api_url = current_app.config["ITS_CCTV_API_URL"]

    if not api_key or not api_url:
        raise ValueError("ITS CCTV API 설정이 누락되었습니다.")

    for region in location["searchRegions"]:
        params = {
            "apiKey": api_key,
            "type": "all",
            "cctvType": "1",
            "minX": region["lon"] - region["delta"],
            "maxX": region["lon"] + region["delta"],
            "minY": region["lat"] - region["delta"],
            "maxY": region["lat"] + region["delta"],
            "getType": "json",
        }

        response = requests.get(api_url, params=params, timeout=12)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict) and "response" in payload:
            payload = payload["response"]

        raw_items = payload.get("data", []) if isinstance(payload, dict) else []
        for keyword in location["searchNames"]:
            keyword_lower = keyword.lower()
            for item in raw_items:
                name = (item.get("cctvname") or item.get("cctvName") or "").lower()
                if keyword_lower in name:
                    normalized = normalize_cctv(item)
                    normalized["id"] = location["id"]
                    normalized["name"] = location["displayName"]
                    normalized["roadName"] = normalized["roadName"] or location["locationName"]
                    return normalized

    return None


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
