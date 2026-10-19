class Config:
    APP_IDENTITY = "base"
    DATABASE = "recipes.db"

class DevelopmentConfig(Config):
    APP_IDENTITY = "development"
    DATABASE = "recipes-dev.db"

class TestingConfig(Config):
    APP_IDENTITY = "testing"
    DATABASE = "recipes-test.db"

class ProductionConfig(Config):
    APP_IDENTITY = "production"
    DATABASE = "recipes.db"