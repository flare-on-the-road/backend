from app.routes.health_routes import health_bp
from app.routes.auth_routes import auth_bp
from app.routes.post_routes import post_bp
from app.routes.comment_routes import comment_bp
from app.routes.user_routes import user_bp

__all__ = [
    'health_bp',
    'auth_bp',
    'post_bp',
    'comment_bp',
    'user_bp',
]

