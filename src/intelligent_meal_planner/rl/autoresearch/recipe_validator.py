"""Recipe validation for DQN autoresearch.

Validates AI-agent-generated custom recipes to prevent unrealistic entries
that could game the evaluation system. Bounds are derived from the existing
150-recipe Chinese database with small margins.
"""

from typing import Any, Dict, List, Tuple

# --- Validation bounds (derived from existing 150 recipes + margin) ---

PRICE_MIN = 3.0
PRICE_MAX = 50.0

CALORIES_MIN = 50.0
CALORIES_MAX = 800.0

PROTEIN_MIN = 1.0
PROTEIN_MAX = 50.0

CARBS_MIN = 0.0
CARBS_MAX = 90.0

FAT_MIN = 0.0
FAT_MAX = 55.0

# Value ratios: prevent "too good to be true" recipes
KCAL_PER_YUAN_MIN = 8.0
KCAL_PER_YUAN_MAX = 80.0

PROTEIN_PER_YUAN_MIN = 0.15
PROTEIN_PER_YUAN_MAX = 5.0

VALID_MEAL_TYPES = {"breakfast", "lunch", "dinner"}
VALID_CATEGORIES = {
    "Meat", "Vegan", "Poultry", "Breakfast", "Seafood",
    "Staple", "Cold", "Tofu", "Soup",
}

REQUIRED_FIELDS = {"name", "calories", "protein", "carbs", "fat", "price", "meal_type", "category"}

MAX_CUSTOM_RECIPES = 150


def validate_recipe(recipe: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate a single custom recipe.

    Args:
        recipe: Dict with recipe fields.

    Returns:
        (True, "") if valid, (False, error_message) if invalid.
    """
    # Check required fields
    missing = REQUIRED_FIELDS - set(recipe.keys())
    if missing:
        return False, f"missing fields: {', '.join(sorted(missing))}"

    name = recipe["name"]
    if not isinstance(name, str) or len(name.strip()) == 0:
        return False, "name must be a non-empty string"

    # Numeric range checks
    cal = recipe["calories"]
    if not isinstance(cal, (int, float)) or not (CALORIES_MIN <= cal <= CALORIES_MAX):
        return False, f"calories={cal} out of range [{CALORIES_MIN}, {CALORIES_MAX}]"

    protein = recipe["protein"]
    if not isinstance(protein, (int, float)) or not (PROTEIN_MIN <= protein <= PROTEIN_MAX):
        return False, f"protein={protein} out of range [{PROTEIN_MIN}, {PROTEIN_MAX}]"

    carbs = recipe["carbs"]
    if not isinstance(carbs, (int, float)) or not (CARBS_MIN <= carbs <= CARBS_MAX):
        return False, f"carbs={carbs} out of range [{CARBS_MIN}, {CARBS_MAX}]"

    fat = recipe["fat"]
    if not isinstance(fat, (int, float)) or not (FAT_MIN <= fat <= FAT_MAX):
        return False, f"fat={fat} out of range [{FAT_MIN}, {FAT_MAX}]"

    price = recipe["price"]
    if not isinstance(price, (int, float)) or not (PRICE_MIN <= price <= PRICE_MAX):
        return False, f"price={price} out of range [{PRICE_MIN}, {PRICE_MAX}]"

    # Value ratio checks (prevent "too good to be true")
    kcal_per_yuan = cal / price
    if not (KCAL_PER_YUAN_MIN <= kcal_per_yuan <= KCAL_PER_YUAN_MAX):
        return False, f"kcal/yuan={kcal_per_yuan:.1f} out of range [{KCAL_PER_YUAN_MIN}, {KCAL_PER_YUAN_MAX}]"

    protein_per_yuan = protein / price
    if not (PROTEIN_PER_YUAN_MIN <= protein_per_yuan <= PROTEIN_PER_YUAN_MAX):
        return False, f"protein/yuan={protein_per_yuan:.2f} out of range [{PROTEIN_PER_YUAN_MIN}, {PROTEIN_PER_YUAN_MAX}]"

    # meal_type validation
    meal_type = recipe["meal_type"]
    if isinstance(meal_type, str):
        meal_type = [meal_type]
    if not isinstance(meal_type, list) or not meal_type:
        return False, "meal_type must be a non-empty list or string"
    invalid_types = set(meal_type) - VALID_MEAL_TYPES
    if invalid_types:
        return False, f"invalid meal_type: {invalid_types}"

    # category validation
    category = recipe["category"]
    if category not in VALID_CATEGORIES:
        return False, f"invalid category '{category}', must be one of {sorted(VALID_CATEGORIES)}"

    return True, ""


def validate_recipes(recipes: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Validate a list of custom recipes.

    Args:
        recipes: List of recipe dicts.

    Returns:
        (valid_recipes, errors) where errors contains messages for rejected recipes.
    """
    if len(recipes) > MAX_CUSTOM_RECIPES:
        return [], [f"too many custom recipes: {len(recipes)} > {MAX_CUSTOM_RECIPES}"]

    valid = []
    errors = []

    for i, recipe in enumerate(recipes):
        ok, msg = validate_recipe(recipe)
        if ok:
            valid.append(recipe)
        else:
            errors.append(f"recipe[{i}] '{recipe.get('name', '?')}': {msg}")

    return valid, errors
