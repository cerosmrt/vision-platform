import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-inseguro-cambiar")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")


class DevelopmentConfig(Config):
    DEBUG = True
    # SQLite no crea el directorio solo, y la ruta es absoluta.
    INSTANCE_DIR = BASE_DIR / "instance"
    INSTANCE_DIR.mkdir(exist_ok=True)
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{INSTANCE_DIR / 'vision.db'}"


class ProductionConfig(Config):
    DEBUG = False

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        url = os.environ["DATABASE_URL"]
        # Railway/Heroku entregan postgres://, SQLAlchemy 2 pide postgresql://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url


def get_config():
    if os.environ.get("FLASK_ENV") == "production":
        return ProductionConfig()
    return DevelopmentConfig()
