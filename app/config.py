import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance', 'app.db'))}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get(
        "UPLOAD_FOLDER",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "uploads")),
    )
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # LLM providers
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}


