"""Recipe Box API — BE104 course skeleton.

A working Flask + SQLite CRUD API for recipes. It stores data perfectly —
and it trusts everyone. There is no authentication and no authorization yet.
That is the point: you will add both, lesson by lesson, in Units 2 and 3.
"""

import sqlite3

import jwt

from flask import Flask, g, jsonify, request, current_app

from werkzeug.security import generate_password_hash, check_password_hash

from dotenv import load_dotenv
import os

from datetime import datetime, timedelta

load_dotenv()

JWT_SECRET = os.environ["JWT_SECRET"]

DATABASE = "recipes.db"

app = Flask(__name__)


app.config["JWT_SECRET"] = os.environ["JWT_SECRET"]

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def recipe_to_dict(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "ingredients": row["ingredients"],
        "instructions": row["instructions"],
        "is_public": bool(row["is_public"]),
    }


@app.get("/")
def hello():
    return jsonify({"message": "Recipe Box API", "recipes": "/recipes"})

@app.post("/register")
def register():
    data = request.get_json(silent=True)
    if not data or not data.get("username") or not data.get("email") or not data.get("password"):
        return jsonify({"error": "username, email, and password are required"}), 400

    password = data["password"]

    password_hash = generate_password_hash(password)

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

@app.post("/login")
def login():
    data = request.get_json(silent=True)
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"error": "username and password are required"}), 400

    username = data["username"]
    password = data["password"]

    db = get_db()
    row = db.execute(
        "SELECT id, username, email, password_hash, role FROM users WHERE username = ?",
        (username,),
    ).fetchone()

    # Generic failure response (same for unknown user and wrong password)
    generic_error = (jsonify({"error": "invalid username or password"}), 401)

    if row is None:
        return generic_error

    if not check_password_hash(row["password_hash"], password):
        return generic_error

    # Success: return authenticated identity (no password/hash)
    payload = {
        "sub": str(row["id"]),
        "username": row["username"],
        "role": row["role"],
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

@app.get("/recipes")
def list_recipes():
    rows = get_db().execute("SELECT * FROM recipes ORDER BY id").fetchall()
    return jsonify([recipe_to_dict(r) for r in rows])


@app.get("/recipes/<int:recipe_id>")
def get_recipe(recipe_id):
    db = get_db()

    row = db.execute(
        "SELECT * FROM recipes WHERE id = ?", (recipe_id,)
    ).fetchone()

    if row is None:
        return jsonify({"error": "recipe not found"}), 404

    # If public, anyone can read it
    if row["is_public"]:
        return jsonify(recipe_to_dict(row))

    # Private recipe: must be owner to read it
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        # Authenticated but unauthorized is 403, but here we don't even know who they are.
        # For a private resouce, it's safe to say forbidden.
        return jsonify({"error": "forbidden: private recipe"}), 403

    token = auth_header.split(" ", 1)[1].strip()

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

    user_id = payload.get("sub")
    if user_id is None:
        return jsonify({"error": "invalid token: missing subject"}), 401

    owner_id = row["owner_id"]
    if str(owner_id) != str(user_id):
        return jsonify({"error": "access denied. You cannot view this recipe"}), 403
    
    return jsonify(recipe_to_dict(row))


@app.post("/recipes")
def create_recipe():
    # 1. Read Authorization header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "missing or invalid Authorization header"}), 401

    token = auth_header.split(" ", 1)[1].strip()

    try:
        # 2. Verify token
        payload = jwt.decode(
            token,
            current_app.config["JWT_SECRET"],
            algorithms=["HS256"], 
        )
    except jwt.ExpiredSignatureError:
        # Token is valid in format/signature, but too old
        return jsonify({"error": "Token expired, please log in again"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "invalid or expired token"}), 401

    # 3. Extract identity (for later use)
    user_id = payload.get("sub")
    if user_id is None:
        return jsonify({"error": "invalid token: missing subject"}), 401

    data = request.get_json(silent=True)
    if not data or not data.get("title") or not data.get("ingredients"):
        return jsonify({"error": "title and ingredients are required"}), 400
    
    db = get_db()

    try:
        cur = db.execute(
            "INSERT INTO recipes (title, ingredients, instructions, is_public, owner_id)"
            " VALUES (?, ?, ?, ?, ?)",
            (
                data["title"],
                data["ingredients"],
                data.get("instructions", ""),
                1 if data.get("is_public", True) else 0,
                user_id,
            ),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "a recipe with that title already exists"}), 409
    row = db.execute(
        "SELECT * FROM recipes WHERE id = ?", (cur.lastrowid,)
    ).fetchone()
    return jsonify(recipe_to_dict(row)), 201


@app.patch("/recipes/<int:recipe_id>")
def update_recipe(recipe_id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "a JSON body is required"}), 400

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "missing or invalid Authorization header"}), 401
    
    token = auth_header.split(" ", 1)[1].strip()

    try:
        # 2. Verify token
        payload = jwt.decode(
            token,
            current_app.config["JWT_SECRET"],
            algorithms=["HS256"], 
        )
    except jwt.ExpiredSignatureError:
        # Token is valid in format/signature, but too old            
        return jsonify({"error": "Token expired, please log in again"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "invalid or expired token"}), 401

    user_id = payload.get("sub")
    if user_id is None:
        return jsonify({"error": "invalid token: missing subject"}), 401

    db = get_db()

    row = db.execute(
        "SELECT * FROM recipes WHERE id = ?",
        (recipe_id,)
    ).fetchone()

    owner_id = row["owner_id"]

    is_owner = str(owner_id) == str(user_id)
    is_admin = payload.get("role") == "admin"

    if not (is_owner or is_admin):
        return (
            jsonify({"error": "access denied. You cannot upadte this recipe"}), 403
        )
    
    fields, values = [], []
    for column in ("title", "ingredients", "instructions"):
        if column in data:
            fields.append(f"{column} = ?")
            values.append(data[column])
    if "is_public" in data:
        fields.append("is_public = ?")
        values.append(1 if data["is_public"] else 0)
    if not fields:
        return jsonify({"error": "nothing to update"}), 400
    values.append(recipe_id)
    
    try:
        cur = db.execute(
            f"UPDATE recipes SET {', '.join(fields)} WHERE id = ?", values
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "a recipe with that title already exists"}), 409
    if cur.rowcount == 0:
        return jsonify({"error": "recipe not found"}), 404
    row = db.execute(
        "SELECT * FROM recipes WHERE id = ?", (recipe_id,)
    ).fetchone()
    return jsonify(recipe_to_dict(row))


@app.delete("/recipes/<int:recipe_id>")
def delete_recipe(recipe_id):

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "missing or invalid Authorization header"}), 401
    
    token = auth_header.split(" ", 1)[1].strip()

    try:
        # 2. Verify token
        payload = jwt.decode(
            token,
            current_app.config["JWT_SECRET"],
            algorithms=["HS256"], 
        )
    except jwt.ExpiredSignatureError:
        # Token is valid in format/signature, but too old            
        return jsonify({"error": "Token expired, please log in again"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "invalid or expired token"}), 401

    user_role = payload.get("role")
    
    user_id = payload.get("sub")
    if user_id is None:
        return jsonify({"error": "invalid token: missing subject"}), 401

    db = get_db()

    row = db.execute(
        "SELECT * FROM recipes WHERE id = ?",
        (recipe_id,)
    ).fetchone()

    owner_id = row["owner_id"]

    is_owner = str(owner_id) ==str(user_id)
    is_admin = user_role == "admin"

    if not (is_owner or is_admin):
        return (
            jsonify({"error": "access denied. You cannot delete this recipe"}), 403
        )

    cur = db.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify({"error": "recipe not found"}), 404
    return "", 204


if __name__ == "__main__":
    app.run(debug=True)
