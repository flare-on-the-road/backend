from app.routes.health_routes import health_bp
from app.routes.auth_routes import auth_bp
from app.routes.user_routes import user_bp
from app.routes.file_routes import file_bp

__all__ = [
    'health_bp',
    'auth_bp',
    'user_bp',
    'file_bp',
]
