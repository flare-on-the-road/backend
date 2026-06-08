from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.get("/")
def health_check():
    return jsonify({
        "status": "ok",
        "message": "Flare backend is running"
    })