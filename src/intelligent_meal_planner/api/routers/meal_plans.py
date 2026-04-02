from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import User
from ..schemas import MealPlanResponse
from ..services import meal_chat_app
from .auth import get_current_user

router = APIRouter(prefix="/meal-plans", tags=["配餐历史"])


@router.get("", response_model=List[MealPlanResponse], summary="获取历史正式配餐")
async def get_history(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return meal_chat_app.get_completed_plans(db, current_user.id, limit)
