import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwtsecret")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Celery / Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

    # OTP
    OTP_EXPIRY_SECONDS = int(os.getenv("OTP_EXPIRY_SECONDS", 600))
    OTP_RESEND_LIMIT_PER_HOUR = int(os.getenv("OTP_RESEND_LIMIT_PER_HOUR", 5))

    # 📧 Email config
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() in ["true", "1", "yes"]
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", MAIL_USERNAME)
