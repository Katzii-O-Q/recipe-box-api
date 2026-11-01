import sqlite3
import jwt
from datetime import datetime, timedelta

from flask import jsonify, request, current_app, Blueprint, g

from werkzeug.security import generate_password_hash, check_password_hash

from app.services.auth_service import verify_login, hash_password, require_auth, get_user_by_id

from app.db_utils import get_db

auth_bp = Blueprint("auth", __name__)

@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True)
    if not data or not data.get("username") or not data.get("email") or not data.get("password"):
        return jsonify({"error": "username, email, and password are required"}), 400

    password = data["password"]

    password_hash = hash_password(password)

    db = get_db()

    try:
        cur = db.execute(
            "INSERT INTO users (username, email, password_hash)"
            " VALUES (?, ?, ?)",
            (
                data["username"],
                data["email"],
                password_hash
            ),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "username or email already in use"}), 409
    return (
        jsonify(
            {
                "id": cur.lastrowid,
                "username": data["username"],
                "email": data["email"],
            }
        ),
        201,
    )

@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True)
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"error": "username and password are required"}), 400

    username = data["username"]
    password = data["password"]

    row = verify_login(username, password)
    
    if row is None:
        return jsonify({"error": "invalid username or password"}), 401

    user_role = "user"
        
    # Success: return authenticated identity (no password/hash)
    payload = {
        "sub": str(row["id"]),
        "username": row["username"],
        "role": user_role,
        "exp": datetime.utcnow() + timedelta(hours=1),
    }

    token = jwt.encode(
        payload, current_app.config["JWT_SECRET"],
        algorithm="HS256",
        )
    
    return jsonify(
        {
            "id": row["id"],
            "username": row["username"],
            "email": row["email"],
            "token": token,
        }
    ), 200

@auth_bp.get("/me")
@require_auth
def get_current_user():
    user_id = g.current_user["id"]
    row = get_user_by_id(user_id)

    if row is None:
        return jsonify({"error": "user not found"}), 404

    return jsonify(
        {
            "id": row["id"],
            "username": row["username"],
            "email": row["email"],
        }
    ), 200