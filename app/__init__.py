import sqlite3

import jwt

from flask import Flask, g, jsonify, request, current_app

from werkzeug.security import generate_password_hash, check_password_hash

from dotenv import load_dotenv
import os

from functools import wraps

from datetime import datetime, timedelta

from app.config import DevelopmentConfig, ProductionConfig, TestingConfig

from app.routes.recipes import recipes_bp
from app.routes.auth import auth_bp

from app.db_utils import get_db

load_dotenv()

def create_app(config_name="default"):
    app = Flask(__name__)

    config_map = {
        "development": DevelopmentConfig,
        "testing": TestingConfig,
        "production": ProductionConfig,
    }

    config_class = config_map.get(config_name)
    app.config.from_object(config_class)

    app.register_blueprint(recipes_bp, url_prefix="")

    app.register_blueprint(auth_bp, url_prefix="")


    print("APP_IDENTITY in factory:", app.config.get("APP_IDENTITY"))

    app.config["JWT_SECRET"] = os.environ["JWT_SECRET"]

    @app.teardown_appcontext
    def close_db(exception):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.get("/")
    def hello():
        return jsonify({"message": "Recipe Box API", "recipes": "/recipes"})

    return app