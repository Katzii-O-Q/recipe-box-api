import os

def get_env_or_raise(name: str) -> str:
    value = os.environ.get(name)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

class Config:
    APP_IDENTITY = "base"
    DATABASE = "recipes.db"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE}"

class DevelopmentConfig(Config):
    APP_IDENTITY = "development"
    DATABASE = get_env_or_raise("DEV_DATABASE")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE}"

class TestingConfig(Config):
    APP_IDENTITY = "testing"
    DATABASE = get_env_or_raise("TEST_DATABASE")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE}"

class ProductionConfig(Config):
    APP_IDENTITY = "production"
    DATABASE = os.environ.get("PROD_DATABASE", "recipes-prod.db")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE}"