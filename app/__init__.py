from flask import Flask
from app.config import Config
from app.extensions import db, cors
from app.routes.health import health_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": app.config["CORS_ORIGINS"]
            }
        }
    )

    app.register_blueprint(health_bp)

    return app