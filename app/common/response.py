from flask import jsonify


def success(data=None, message="success", status_code=200):
    return jsonify({
        "success": True,
        "message": message,
        "data": data,
    }), status_code


def fail(message="error", status_code=400, data=None):
    return jsonify({
        "success": False,
        "message": message,
        "data": data,
    }), status_code