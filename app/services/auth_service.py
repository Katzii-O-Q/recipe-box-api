from werkzeug.security import generate_password_hash, check_password_hash
from app.db_utils import get_db

import jwt

from flask import request, jsonify, current_app, g

from functools import wraps


def require_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 1. Read Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "missing or invalid Authorization header"}), 401

        token = auth_header.split(" ", 1)[1].strip()

        # 2. Verify token
        try:
            payload = jwt.decode(
                token,
                current_app.config["JWT_SECRET"],
                algorithms=["HS256"],
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired, please log in again"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "invalid or expired token"}), 401

        user_role = payload.get("role")
        user_id = payload.get("sub")
        if user_id is None:
            return jsonify({"error": "invalid token: missing subject"}), 401

        # 3. Store on g so routes can use it
        g.current_user = {
            "id": str(user_id),
            "role": user_role,
            "payload": payload, # optional but can be handy
        }

        # 4. Call the original route
        return func(*args, **kwargs)

    return wrapper

def hash_password(plain_password: str) -> str:
    """
    Take a plaintext password and return a one-way hash string
    suitable for storing in the database.
    """
    return generate_password_hash(plain_password)

def verify_password(stored_hash: str, candidate_password: str) -> bool:
    """
    Check a candidate password against a stored password hash.
    Returns True if they match, False otherwise.
    """
    return check_password_hash(stored_hash, candidate_password)

def verify_login(username, password):
    db = get_db()
    row = db.execute(
        "SELECT id, username, email, password_hash FROM users WHERE username = ?",
        (username,),
    ).fetchone()

    if row is None:
        return None
    
    if not check_password_hash(row["password_hash"], password):
        return None

    return row

def get_user_by_id(user_id):
    db = get_db()

    row = db.execute(
        "SELECT id, username, email FROM users WHERE id = ?", (user_id,)
    ).fetchone()

    return row