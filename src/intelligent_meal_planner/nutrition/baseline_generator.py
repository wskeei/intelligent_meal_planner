"""Auto-initialize virtual intake history and preferences from user profile."""

import random
from datetime import date, timedelta

from sqlalchemy.orm import Session

from ..db import models
from ..meal_chat.target_mapper import build_hidden_targets


class BaselineGenerator:
    def __init__(self, db: Session):
        self.db = db

    def initialize_for_user(self, user: models.User) -> None:
        if self._already_initialized(user.id):
            return

        recipes = self.db.query(models.Recipe).all()
        if not recipes:
            return

        self._create_virtual_intake(user, recipes)
        self._create_preferences(user, recipes)
        self._create_welcome_reminder(user)

    def _already_initialized(self, user_id: int) -> bool:
        return (
            self.db.query(models.IntakeRecord)
            .filter_by(user_id=user_id, source="auto")
            .count()
            > 0
        )

    def _create_virtual_intake(self, user: models.User, recipes: list) -> None:
        breakfast_recipes = [r for r in recipes if "breakfast" in (r.meal_type or [])]
        lunch_recipes = [r for r in recipes if "lunch" in (r.meal_type or [])]
        dinner_recipes = [r for r in recipes if "dinner" in (r.meal_type or [])]

        if not lunch_recipes:
            lunch_recipes = recipes
        if not dinner_recipes:
            dinner_recipes = recipes

        today = date.today()
        for day_offset in range(7, 0, -1):
            d = today - timedelta(days=day_offset)

            recipe = random.choice(lunch_recipes)
            self.db.add(models.IntakeRecord(
                user_id=user.id, date=d, meal_type="lunch",
                recipe_id=recipe.id,
                actual_calories=recipe.calories,
                actual_protein=recipe.protein,
                actual_carbs=recipe.carbs,
                actual_fat=recipe.fat,
                source="auto",
            ))

            recipe = random.choice(dinner_recipes)
            self.db.add(models.IntakeRecord(
                user_id=user.id, date=d, meal_type="dinner",
                recipe_id=recipe.id,
                actual_calories=recipe.calories,
                actual_protein=recipe.protein,
                actual_carbs=recipe.carbs,
                actual_fat=recipe.fat,
                source="auto",
            ))

        self.db.commit()

    def _create_preferences(self, user: models.User, recipes: list) -> None:
        for recipe in recipes:
            self.db.add(models.UserPreference(
                user_id=user.id,
                recipe_id=recipe.id,
                preference_score=0.5,
            ))
        self.db.commit()

    def _create_welcome_reminder(self, user: models.User) -> None:
        targets = {}
        if all([user.weight, user.height, user.age, user.gender, user.activity_level]):
            targets = build_hidden_targets(
                {"weight": user.weight, "height": user.height,
                 "age": user.age, "gender": user.gender,
                 "activity_level": user.activity_level},
                user.health_goal or "healthy",
            )

        cal_display = int(targets.get("target_calories", 2000))
        self.db.add(models.Reminder(
            user_id=user.id,
            type="goal_milestone",
            title="Welcome to Nutrition Tracking",
            message=f"Your daily target: {cal_display} kcal. Start logging your meals!",
            severity="info",
        ))
        self.db.commit()
