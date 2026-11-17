from app.extensions import db
from app.models import Recipe
from app.recipe_utils import recipe_to_dict

def list_public_recipes_orm():
    public_recipes = Recipe.query.filter_by(is_public=1).order_by(Recipe.id).all()
    return [
        {
            "id": recipe.id,
            "title": recipe.title,
            "ingredients": recipe.ingredients,
            "instructions": recipe.instructions,
            "is_public": bool(recipe.is_public),
        }
        for recipe in public_recipes
    ]

def get_recipe_by_id_orm(recipe_id):
    return Recipe.query.get(recipe_id)