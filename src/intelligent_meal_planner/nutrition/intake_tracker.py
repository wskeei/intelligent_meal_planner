"""Intake record CRUD and daily aggregation."""

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from ..db import models


class IntakeTracker:
    def __init__(self, db: Session):
        self.db = db

    def log_meal(
        self,
        user_id: int,
        record_date: date,
        meal_type: str,
        recipe_id: Optional[int] = None,
        custom_food_name: Optional[str] = None,
        actual_calories: Optional[float] = None,
        actual_protein: Optional[float] = None,
        actual_carbs: Optional[float] = None,
        actual_fat: Optional[float] = None,
        portion_size: float = 1.0,
        source: str = "manual",
        rating: Optional[int] = None,
        note: Optional[str] = None,
    ) -> models.IntakeRecord:
        if recipe_id is not None:
            recipe = self.db.get(models.Recipe, recipe_id)
            if not recipe:
                raise ValueError(f"Recipe {recipe_id} not found")
            actual_calories = recipe.calories * portion_size
            actual_protein = recipe.protein * portion_size
            actual_carbs = recipe.carbs * portion_size
            actual_fat = recipe.fat * portion_size
            if custom_food_name is None:
                custom_food_name = None

        record = models.IntakeRecord(
            user_id=user_id,
            date=record_date,
            meal_type=meal_type,
            recipe_id=recipe_id,
            custom_food_name=custom_food_name,
            actual_calories=actual_calories or 0,
            actual_protein=actual_protein or 0,
            actual_carbs=actual_carbs or 0,
            actual_fat=actual_fat or 0,
            portion_size=portion_size,
            source=source,
            rating=rating,
            note=note,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def update_record(
        self, record_id: int, user_id: int, **fields
    ) -> models.IntakeRecord:
        record = (
            self.db.query(models.IntakeRecord)
            .filter_by(id=record_id, user_id=user_id)
            .first()
        )
        if not record:
            raise ValueError(f"Record {record_id} not found")

        if "portion_size" in fields and record.recipe_id is not None:
            recipe = self.db.get(models.Recipe, record.recipe_id)
            if recipe:
                ps = fields["portion_size"]
                record.actual_calories = recipe.calories * ps
                record.actual_protein = recipe.protein * ps
                record.actual_carbs = recipe.carbs * ps
                record.actual_fat = recipe.fat * ps

        for k, v in fields.items():
            if v is not None:
                setattr(record, k, v)

        self.db.commit()
        self.db.refresh(record)
        return record

    def delete_record(self, record_id: int, user_id: int) -> None:
        record = (
            self.db.query(models.IntakeRecord)
            .filter_by(id=record_id, user_id=user_id)
            .first()
        )
        if not record:
            raise ValueError(f"Record {record_id} not found")
        self.db.delete(record)
        self.db.commit()

    def get_daily(self, user_id: int, record_date: date) -> dict:
        records = (
            self.db.query(models.IntakeRecord)
            .filter_by(user_id=user_id, date=record_date)
            .order_by(models.IntakeRecord.meal_type, models.IntakeRecord.id)
            .all()
        )
        totals = {
            "calories": sum(r.actual_calories for r in records),
            "protein": sum(r.actual_protein for r in records),
            "carbs": sum(r.actual_carbs for r in records),
            "fat": sum(r.actual_fat for r in records),
        }
        return {"records": records, "totals": totals, "count": len(records)}

    def recipe_name(self, record: models.IntakeRecord) -> Optional[str]:
        if record.recipe_id:
            recipe = self.db.get(models.Recipe, record.recipe_id)
            return recipe.name if recipe else None
        return record.custom_food_name
