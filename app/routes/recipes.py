import sqlite3
import jwt


from flask import Blueprint, jsonify, request, current_app, g

from app.db_utils import get_db
from app.recipe_utils import recipe_to_dict, list_public_recipes, create_recipe_for_user, get_recipe_row

from app.services.auth_service import require_auth

recipes_bp = Blueprint("recipes", __name__)

@recipes_bp.get("/recipes")
def list_recipes():
    recipes = list_public_recipes()
    return jsonify(recipes)


@recipes_bp.get("/recipes/<int:recipe_id>")
def get_recipe(recipe_id):
    row = get_recipe_row(recipe_id)
    if row is None:
        return jsonify({"error": "recipe not found"}), 404
    
    # If public, anyone can read it
    if row["is_public"]:
        return jsonify(recipe_to_dict(row))

    # Private recipe: must be owner to read it
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):

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


@recipes_bp.post("/recipes")
@require_auth
def create_recipe():
    data = request.get_json(silent=True)

    if not data or not data.get("title") or not data.get("ingredients"):
        return jsonify({"error": "title and ingredients are required"}), 400

    user_id = g.current_user["id"]

    recipe = create_recipe_for_user(user_id, data)

    return jsonify(recipe), 201


@recipes_bp.patch("/recipes/<int:recipe_id>")
@require_auth
def update_recipe(recipe_id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "a JSON body is required"}), 400

    user_id = g.current_user["id"]
    user_role = g.current_user["role"]

    db = get_db()

    row = db.execute(
        "SELECT * FROM recipes WHERE id = ?",
        (recipe_id,)
    ).fetchone()

    if row is None:
        return jsonify({"error": "recipe not found"}), 404

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


@recipes_bp.delete("/recipes/<int:recipe_id>")
@require_auth
def delete_recipe(recipe_id):

    db = get_db()

    row = db.execute(
        "SELECT * FROM recipes WHERE id = ?",
        (recipe_id,)
    ).fetchone()

    if row is None:
        return jsonify({"error": "recipe not found"}), 404

    cur = db.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify({"error": "recipe not found"}), 404
    return "", 204
