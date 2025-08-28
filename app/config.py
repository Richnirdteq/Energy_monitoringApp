import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class BaseConfig:
    # Security
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SECURITY_PASSWORD_SALT = os.environ.get("SECURITY_PASSWORD_SALT", "dev-password-salt")

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///site.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File uploads
    UPLOAD_FOLDER = "static/profile_pics"
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

class DevelopmentConfig(BaseConfig):
    MAIL_SERVER = "localhost"
    MAIL_PORT = 8025
    MAIL_USE_TLS = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = ("Energy Tracker Dev", "noreply@example.com")
    MAIL_SUPPRESS_SEND = False  # Emails are sent locally for testing

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
