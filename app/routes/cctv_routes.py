from flask import Blueprint, request

from app.common.response import fail, success
from app.services import cctv_service

cctv_bp = Blueprint("cctv", __name__)


@cctv_bp.get("")
def list_cctvs():
    try:
        result = cctv_service.get_cctvs(
            min_x=_float_arg("minX"),
            max_x=_float_arg("maxX"),
            min_y=_float_arg("minY"),
            max_y=_float_arg("maxY"),
            cctv_type=request.args.get("cctvType", "all"),
            limit=_int_arg("limit", 500),
        )
        return success(result, "CCTV 목록 조회 성공")
    except ValueError as e:
        return fail(str(e), 400)
    except Exception as e:
        return fail(str(e) or type(e).__name__, 502)


@cctv_bp.get("/monitored")
def list_monitored_cctvs():
    try:
        result = cctv_service.get_monitored_cctvs()
        return success(result, "관제 CCTV 목록 조회 성공")
    except ValueError as e:
        return fail(str(e), 400)
    except Exception as e:
        return fail(str(e) or type(e).__name__, 502)


def _float_arg(name):
    value = request.args.get(name)

    if value is None or value == "":
        return None

    return float(value)


def _int_arg(name, default):
    value = request.args.get(name)

    if value is None or value == "":
        return default

    return int(value)
