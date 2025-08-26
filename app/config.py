import os

class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SECURITY_PASSWORD_SALT = os.environ.get("SECURITY_PASSWORD_SALT", "dev-password-salt")  # ← ADD THIS

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///site.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File uploads
    UPLOAD_FOLDER = os.path.join("app", "static", "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

class DevelopmentConfig(BaseConfig):
    MAIL_SERVER = "localhost"
    MAIL_PORT = 8025
    MAIL_USE_TLS = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = ("Energy Tracker Dev", "noreply@example.com")
    MAIL_SUPPRESS_SEND = False  # ensure emails are actually sent to local SMTP

class ProductionConfig(BaseConfig):
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = ("Energy Tracker", os.environ.get("MAIL_USERNAME"))

config_dict = {
    "development": DevelopmentConfig,
    "production": ProductionConfig
}
