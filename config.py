import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-ganti-di-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # CSRF token tidak kedaluwarsa

    # Session cookie
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=365)

    # Email
    MAIL_SERVER   = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT     = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS  = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'Uang Kas <noreply@uangkas.app>')

    APP_BASE_URL  = os.environ.get('APP_BASE_URL', 'http://localhost:5000')
    OWNER_EMAIL   = os.environ.get('OWNER_EMAIL', 'setyanaputra@yahoo.com')

    # Magic link expiry
    MAGIC_LINK_LOGIN_MINUTES    = 15
    MAGIC_LINK_ONBOARD_HOURS    = 24
    MAGIC_LINK_RATE_LIMIT       = 3   # max per 5 menit


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///uangkas.db')
    SESSION_COOKIE_SECURE = False
    MAIL_SUPPRESS_SEND = False  # Set True untuk skip kirim email saat dev


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SESSION_COOKIE_SECURE = True


config = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'default':     DevelopmentConfig,
}
