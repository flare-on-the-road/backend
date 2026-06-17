from flask import jsonify


class ErrorCode:
    AUTH_REQUIRED = "AUTH_REQUIRED"
    FORBIDDEN = "FORBIDDEN"
    POST_NOT_FOUND = "POST_NOT_FOUND"
    COMMENT_NOT_FOUND = "COMMENT_NOT_FOUND"
    EVENT_NOT_FOUND = "EVENT_NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MAX_DEPTH_EXCEEDED = "MAX_DEPTH_EXCEEDED"
    INVALID_PARENT = "INVALID_PARENT"
    VISION_API_UNAVAILABLE = "VISION_API_UNAVAILABLE"


class ApiError(Exception):
    def __init__(self, code, message, status_code=400, details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details

    def to_response(self):
        body = {"error": {"code": self.code, "message": self.message}}
        if self.details:
            body["error"]["details"] = self.details
        return jsonify(body), self.status_code


class ValidationError(ApiError):
    def __init__(self, details, message="입력값을 확인해주세요."):
        super().__init__(ErrorCode.VALIDATION_ERROR, message, 400, details)


class ForbiddenError(ApiError):
    def __init__(self, message="권한이 없습니다."):
        super().__init__(ErrorCode.FORBIDDEN, message, 403)


class PostNotFoundError(ApiError):
    def __init__(self, message="게시글을 찾을 수 없습니다."):
        super().__init__(ErrorCode.POST_NOT_FOUND, message, 404)


class CommentNotFoundError(ApiError):
    def __init__(self, message="댓글을 찾을 수 없습니다."):
        super().__init__(ErrorCode.COMMENT_NOT_FOUND, message, 404)


class EventNotFoundError(ApiError):
    def __init__(self, message="이벤트를 찾을 수 없습니다."):
        super().__init__(ErrorCode.EVENT_NOT_FOUND, message, 404)


class MaxDepthExceededError(ApiError):
    def __init__(self, message="대댓글에는 댓글을 작성할 수 없습니다."):
        super().__init__(ErrorCode.MAX_DEPTH_EXCEEDED, message, 400)


class InvalidParentError(ApiError):
    def __init__(self, message="유효하지 않은 부모 댓글입니다."):
        super().__init__(ErrorCode.INVALID_PARENT, message, 400)


class VisionApiUnavailableError(ApiError):
    def __init__(self, message="Vision 모델 서버를 사용할 수 없습니다.", details=None):
        super().__init__(ErrorCode.VISION_API_UNAVAILABLE, message, 503, details)


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(err):
        return err.to_response()
