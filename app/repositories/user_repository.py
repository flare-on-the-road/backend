from app.extensions import db
from app.models.user import User


def find_by_id(user_id):
    return User.query.get(user_id)


def find_by_email(email):
    return User.query.filter_by(email=email).first()


def find_by_provider(provider, provider_user_id):
    return User.query.filter_by(
        provider=provider,
        provider_user_id=provider_user_id,
    ).first()


def find_all():
    return User.query.order_by(User.id.desc()).all()


def create_user(
    email,
    name,
    password=None,
    role="viewer",
    provider="local",
    provider_user_id=None,
    department=None,
    phone=None,
):
    user = User(
        email=email,
        name=name,
        role=role,
        provider=provider,
        provider_user_id=provider_user_id,
        department=department,
        phone=phone,
    )

    if password:
        user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return user


def save(user):
    db.session.add(user)
    db.session.commit()

    return user


def delete(user):
    db.session.delete(user)
    db.session.commit()