from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from app.config import Config
from app.extensions import db, cors, migrate, swagger
from app.common.errors import register_error_handlers
from app.routes import health_bp, auth_bp, post_bp, comment_bp, user_bp, file_bp, cctv_bp, admin_bp, event_bp, ai_lab_bp


jwt = JWTManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    jwt.init_app(app)
    register_error_handlers(app)

    @jwt.unauthorized_loader
    def handle_missing_token(reason):
        return jsonify({"error": {"code": "AUTH_REQUIRED", "message": "인증이 필요합니다."}}), 401

    @jwt.invalid_token_loader
    def handle_invalid_token(reason):
        return jsonify({"error": {"code": "AUTH_REQUIRED", "message": "유효하지 않은 토큰입니다."}}), 401

    @jwt.expired_token_loader
    def handle_expired_token(jwt_header, jwt_payload):
        return jsonify({"error": {"code": "AUTH_REQUIRED", "message": "토큰이 만료되었습니다."}}), 401

    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": app.config["CORS_ORIGINS"]
            }
        },
        supports_credentials=True,
    )

    app.config["SWAGGER"] = {
        "title": "Flare Backend API",
        "uiversion": 3,
        "description": (
            "Flare 백엔드 API 문서입니다.\n\n"
            "제공 기능:\n"
            "- Auth API\n"
            "- Admin API\n"
            "- CCTV API\n\n"
            "Swagger UI에서 직접 API 테스트가 가능합니다."
        ),
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                # Header 위치
                "in": "header",
                # Swagger UI 설명
                "description": (
                    "JWT 인증 토큰 입력\n\n"
                    "형식:\n"
                    "Bearer {accessToken}\n\n"
                    "예시:\n"
                    "Bearer eyJhbGciOiJIUzI1NiIs..."
                ),
            }
        },
    }
    swagger.init_app(app)

    from app import models

    # FIXME : 이부분만 수정해주세요!
    app.register_blueprint(health_bp, url_prefix="/api/health")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(post_bp, url_prefix="/api/posts")
    app.register_blueprint(comment_bp, url_prefix="/api")
    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(file_bp, url_prefix="/api/files")
    app.register_blueprint(cctv_bp, url_prefix="/api/cctvs")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    # app.register_blueprint(cctv_bp, url_prefix="/api/cctv")
    app.register_blueprint(event_bp, url_prefix="/api/events")
    app.register_blueprint(ai_lab_bp, url_prefix="/api/ai-lab")
    # FIXME end

    return app
