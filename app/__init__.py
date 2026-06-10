from flask import Flask
from flask_jwt_extended import JWTManager
from app.config import Config
from app.extensions import db, cors, migrate, swagger
from app.routes import health_bp, auth_bp, user_bp, file_bp

jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    jwt.init_app(app)

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
    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(file_bp, url_prefix="/api/files")
    # app.register_blueprint(admin_bp, url_prefix="/api/admin")
    # app.register_blueprint(cctv_bp, url_prefix="/api/cctv")
    # app.register_blueprint(event_bp, url_prefix="/api/events")
    # FIXME end

    return app
