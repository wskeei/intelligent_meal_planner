"""Intake tracking REST endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...db.database import get_db
from ..routers.auth import get_current_user
from ..schemas import (
    DailyIntakeSummary,
    IntakeRecordCreate,
    IntakeRecordUpdate,
)
from ...nutrition.intake_tracker import IntakeTracker
from ...db import models

router = APIRouter(prefix="/intake", tags=["摄入追踪"])


def _to_response(record: models.IntakeRecord, tracker: IntakeTracker) -> dict:
    return {
        "id": record.id,
        "date": record.date,
        "meal_type": record.meal_type,
        "recipe_id": record.recipe_id,
        "recipe_name": tracker.recipe_name(record),
        "custom_food_name": record.custom_food_name,
        "actual_calories": record.actual_calories,
        "actual_protein": record.actual_protein,
        "actual_carbs": record.actual_carbs,
        "actual_fat": record.actual_fat,
        "portion_size": record.portion_size,
        "source": record.source,
        "rating": record.rating,
        "note": record.note,
        "created_at": record.created_at,
    }


@router.post("/records")
def log_meal(
    payload: IntakeRecordCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    tracker = IntakeTracker(db)
    try:
        record = tracker.log_meal(
            user_id=current_user.id,
            record_date=payload.date,
            meal_type=payload.meal_type,
            recipe_id=payload.recipe_id,
            custom_food_name=payload.custom_food_name,
            actual_calories=payload.actual_calories,
            actual_protein=payload.actual_protein,
            actual_carbs=payload.actual_carbs,
            actual_fat=payload.actual_fat,
            portion_size=payload.portion_size,
            rating=payload.rating,
            note=payload.note,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_response(record, tracker)


@router.post("/quick-log")
def quick_log(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Quick log: just recipe_id + optional portion_size. Meal type auto-detected."""
    recipe_id = payload.get("recipe_id")
    if not recipe_id:
        raise HTTPException(status_code=400, detail="recipe_id required")

    recipe = db.get(models.Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    meal_types = recipe.meal_type or ["lunch"]
    auto_meal = meal_types[0] if meal_types else "lunch"

    raw_date = payload.get("date")
    if isinstance(raw_date, str):
        from datetime import date as date_cls
        record_date = date_cls.fromisoformat(raw_date)
    elif isinstance(raw_date, date):
        record_date = raw_date
    else:
        record_date = date.today()

    tracker = IntakeTracker(db)
    record = tracker.log_meal(
        user_id=current_user.id,
        record_date=record_date,
        meal_type=payload.get("meal_type", auto_meal),
        recipe_id=recipe_id,
        portion_size=payload.get("portion_size", 1.0),
    )
    return _to_response(record, tracker)


@router.get("/records/{record_date}")
def get_daily_records(
    record_date: date,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    tracker = IntakeTracker(db)
    result = tracker.get_daily(current_user.id, record_date)
    return DailyIntakeSummary(
        date=record_date,
        total_calories=result["totals"]["calories"],
        total_protein=result["totals"]["protein"],
        total_carbs=result["totals"]["carbs"],
        total_fat=result["totals"]["fat"],
        meal_count=result["count"],
        records=[_to_response(r, tracker) for r in result["records"]],
    )


@router.patch("/records/{record_id}")
def update_record(
    record_id: int,
    payload: IntakeRecordUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    tracker = IntakeTracker(db)
    try:
        fields = payload.model_dump(exclude_unset=True)
        record = tracker.update_record(record_id, current_user.id, **fields)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _to_response(record, tracker)


@router.delete("/records/{record_id}")
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    tracker = IntakeTracker(db)
    try:
        tracker.delete_record(record_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"success": True}
