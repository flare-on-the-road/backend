import pytest
from flask_jwt_extended import create_access_token

from app import create_app
from app.config import TestConfig
from app.common.constants import UserRole
from app.extensions import db
from app.models.user import User


@pytest.fixture()
def app():
    flask_app = create_app(TestConfig)

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _create_user(email, name, role=UserRole.VIEWER):
    user = User(email=email, name=name, role=role)
    db.session.add(user)
    db.session.commit()
    return user


def _auth_header(user):
    token = create_access_token(
        identity=str(user.id),
        additional_claims={"email": user.email, "name": user.name, "role": user.role},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def user(app):
    return _create_user("user@example.com", "qa_kim", UserRole.VIEWER)


@pytest.fixture()
def other_user(app):
    return _create_user("other@example.com", "qa_lee", UserRole.VIEWER)


@pytest.fixture()
def admin_user(app):
    return _create_user("admin@example.com", "admin_park", UserRole.ADMIN)


@pytest.fixture()
def user_headers(user):
    return _auth_header(user)


@pytest.fixture()
def other_headers(other_user):
    return _auth_header(other_user)


@pytest.fixture()
def admin_headers(admin_user):
    return _auth_header(admin_user)
