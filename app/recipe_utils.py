from app.db_utils import get_db

def recipe_to_dict(row):
        return {
            "id": row["id"],
            "title": row["title"],
            "ingredients": row["ingredients"],
            "instructions": row["instructions"],
            "is_public": bool(row["is_public"]),
        }

def list_public_recipes():
        db = get_db()

        rows = db.execute(
                "SELECT * FROM recipes WHERE is_public = 1 ORDER BY id"
        ).fetchall()
        return [recipe_to_dict(row) for row in rows]

def create_recipe_for_user(user_id, data):
        db = get_db()

        cur = db.execute(
                "INSERT INTO recipes (title, ingredients, instructions, is_public)"
                " VALUES (?, ?, ?, ?)",
                (
                        data["title"],
                        data["ingredients"],
                        data.get("instructions", ""),
                        1 if data.get("is_public", True) else 0,
                ),
        )
        db.commit()
        row = db.execute(
                "SELECT * FROM recipes WHERE id = ?", (cur.lastrowid, )
        ).fetchone()

        return recipe_to_dict(row)

def get_recipe_row(recipe_id):
    db = get_db()
        
    return db.execute(
           "SELECT * FROM recipes WHERE id = ?", (recipe_id,)
    ).fetchone()
