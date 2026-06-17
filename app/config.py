from pathlib import Path
import os
import certifi
import platform
import ssl
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()
OS_NAME = platform.system()


def _int_env(name, default):
    value = os.getenv(name)
    if value in (None, ""):
        return default
    return int(value)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-jwt")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", 60))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", 14))
    )

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": int(os.getenv("SQLALCHEMY_POOL_RECYCLE_SECONDS", 280)),
        "pool_timeout": int(os.getenv("SQLALCHEMY_POOL_TIMEOUT_SECONDS", 30)),
    }

    if OS_NAME == "Windows":
        SQLALCHEMY_ENGINE_OPTIONS["connect_args"] = {
            "ssl": {"ca": certifi.where()}
        }

    if OS_NAME == "Darwin":  # macOS
        SQLALCHEMY_ENGINE_OPTIONS.update(
            {
                "connect_args": {
                "ssl_ca": "/etc/ssl/cert.pem",
                "ssl_verify_cert": True,
                "ssl_verify_identity": True,
                }
            }
        )
    
    

    FRONTEND_URL = os.getenv("FRONTEND_URL","http://localhost:3000")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS","http://localhost:3000")

    # Google OAuth 설정
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

    # Naver OAuth 설정
    NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
    NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
    NAVER_REDIRECT_URI = os.getenv("NAVER_REDIRECT_URI")

    # Kakao OAuth 설정
    KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID")
    KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET")
    KAKAO_CLIENT_SECRET_ENABLED = (
        os.getenv("KAKAO_CLIENT_SECRET_ENABLED", "false").lower() == "true"
    )
    KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")

    ITS_API_KEY = os.getenv("ITS_API_KEY")
    ITS_CCTV_API_URL = os.getenv("ITS_CCTV_API_URL")

    CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
    CF_R2_ACCESS_KEY_ID = (
        os.getenv("CF_R2_ACCESS_KEY_ID")
        or os.getenv("CF_ACCESS_KEY_ID")
        or os.getenv("CF_ACCESS_KEY")
    )
    CF_R2_SECRET_ACCESS_KEY = (
        os.getenv("CF_R2_SECRET_ACCESS_KEY")
        or os.getenv("CF_SECRET_ACCESS_KEY")
        or os.getenv("CF_SECRET_KEY")
    )
    CF_R2_BUCKET_NAME = os.getenv("CF_R2_BUCKET_NAME") or os.getenv("CF_BUCKET_NAME")
    CF_R2_PUBLIC_URL = os.getenv("CF_R2_PUBLIC_URL")
    CF_R2_ENDPOINT_URL = os.getenv("CF_R2_ENDPOINT_URL")
    MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", 10 * 1024 * 1024))

    VISION_API_URL = os.getenv("VISION_API_URL", "")
    VISION_API_TIMEOUT_SECONDS = _int_env("VISION_API_TIMEOUT_SECONDS", 30)
    VISION_SAMPLE_IMAGE_DIR = os.getenv(
        "VISION_SAMPLE_IMAGE_DIR",
        str(Path(__file__).resolve().parents[2] / "frontend" / "public" / "ai-lab" / "samples"),
    )


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
