from app.extensions import db
from app.models.social_account import SocialAccount


def find_by_provider(provider, provider_user_id):
    return SocialAccount.query.filter_by(
        provider=provider,
        provider_user_id=provider_user_id,
    ).first()


def find_by_user_id(user_id):
    return SocialAccount.query.filter_by(
        user_id=user_id,
    ).all()


def create_social_account(
    user_id,
    provider,
    provider_user_id,
):
    social_account = SocialAccount(
        user_id=user_id,
        provider=provider,
        provider_user_id=provider_user_id,
    )

    db.session.add(social_account)
    db.session.commit()

    return social_account


def save(social_account):
    db.session.add(social_account)
    db.session.commit()

    return social_account


def delete(social_account):
    db.session.delete(social_account)
    db.session.commit()