"""Tests for recipe_validator module."""

import pytest

from intelligent_meal_planner.rl.autoresearch.recipe_validator import (
    validate_recipe,
    validate_recipes,
    MAX_CUSTOM_RECIPES,
)


def _valid_recipe(**overrides):
    """Return a valid recipe dict with optional overrides."""
    base = {
        "name": "测试菜品",
        "calories": 400,
        "protein": 20,
        "carbs": 50,
        "fat": 15,
        "price": 15,
        "meal_type": ["lunch", "dinner"],
        "category": "Meat",
        "tags": ["test"],
    }
    base.update(overrides)
    return base


class TestValidateRecipe:
    def test_valid_recipe_passes(self):
        ok, msg = validate_recipe(_valid_recipe())
        assert ok, msg

    def test_missing_field_fails(self):
        recipe = _valid_recipe()
        del recipe["calories"]
        ok, msg = validate_recipe(recipe)
        assert not ok
        assert "missing fields" in msg

    def test_empty_name_fails(self):
        ok, msg = validate_recipe(_valid_recipe(name=""))
        assert not ok
        assert "name" in msg

    def test_price_too_low_fails(self):
        ok, msg = validate_recipe(_valid_recipe(price=1.0))
        assert not ok
        assert "price" in msg

    def test_price_too_high_fails(self):
        ok, msg = validate_recipe(_valid_recipe(price=100.0))
        assert not ok
        assert "price" in msg

    def test_calories_too_high_fails(self):
        ok, msg = validate_recipe(_valid_recipe(calories=1000))
        assert not ok
        assert "calories" in msg

    def test_kcal_per_yuan_too_high_fails(self):
        # 800 kcal / 5 yuan = 160 kcal/yuan > 80 limit
        ok, msg = validate_recipe(_valid_recipe(calories=800, price=5))
        assert not ok
        assert "kcal/yuan" in msg

    def test_protein_per_yuan_too_high_fails(self):
        # 40g / 5 yuan = 8 protein/yuan > 5.0 limit (kcal/yuan must pass first)
        ok, msg = validate_recipe(_valid_recipe(protein=40, price=5, calories=350))
        assert not ok
        assert "protein/yuan" in msg

    def test_invalid_meal_type_fails(self):
        ok, msg = validate_recipe(_valid_recipe(meal_type=["brunch"]))
        assert not ok
        assert "meal_type" in msg

    def test_string_meal_type_accepted(self):
        ok, msg = validate_recipe(_valid_recipe(meal_type="lunch"))
        assert ok, msg

    def test_invalid_category_fails(self):
        ok, msg = validate_recipe(_valid_recipe(category="Pizza"))
        assert not ok
        assert "category" in msg

    def test_boundary_values_pass(self):
        """Test recipe at exact boundary values."""
        ok, msg = validate_recipe(_valid_recipe(
            calories=50, protein=1, carbs=0, fat=0,
            price=3, meal_type="breakfast", category="Breakfast",
        ))
        assert ok, msg


class TestValidateRecipes:
    def test_empty_list(self):
        valid, errors = validate_recipes([])
        assert valid == []
        assert errors == []

    def test_mixed_valid_invalid(self):
        recipes = [
            _valid_recipe(name="好菜"),
            _valid_recipe(name="坏菜", price=0.5),  # too cheap
            _valid_recipe(name="又一道好菜"),
        ]
        valid, errors = validate_recipes(recipes)
        assert len(valid) == 2
        assert len(errors) == 1
        assert "坏菜" in errors[0]

    def test_too_many_recipes_rejected(self):
        recipes = [_valid_recipe(name=f"菜{i}") for i in range(MAX_CUSTOM_RECIPES + 1)]
        valid, errors = validate_recipes(recipes)
        assert valid == []
        assert "too many" in errors[0]

    def test_anti_gaming_perfect_recipe_rejected(self):
        """A 'too good to be true' recipe should fail validation."""
        # 5元 800kcal 50g protein = 160 kcal/yuan, 10 protein/yuan
        ok, msg = validate_recipe({
            "name": "完美作弊菜",
            "calories": 800, "protein": 50, "carbs": 60, "fat": 20,
            "price": 5, "meal_type": ["lunch"], "category": "Meat",
        })
        assert not ok, "Perfect-value recipe should be rejected"
