from app.routes.health_routes import health_bp
from app.routes.auth_routes import auth_bp
from app.routes.post_routes import post_bp
from app.routes.comment_routes import comment_bp
from app.routes.user_routes import user_bp
from app.routes.file_routes import file_bp
from app.routes.cctv_routes import cctv_bp
from app.routes.admin_routes import admin_bp
from app.routes.event_routes import event_bp
from app.routes.ai_lab_routes import ai_lab_bp

__all__ = [
    'health_bp',
    'auth_bp',
    'post_bp',
    'comment_bp',
    'user_bp',
    'file_bp',
    'cctv_bp',
    'admin_bp',
    'event_bp',
    'ai_lab_bp',
]
