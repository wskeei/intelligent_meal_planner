from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import User
from ..schemas import (
    WeeklyPlanAttachDayRequest,
    WeeklyPlanCreateRequest,
    WeeklyPlanResponse,
    WeeklyPlanSummaryResponse,
)
from ..services import weekly_plan_service
from .auth import get_current_user

router = APIRouter(prefix="/weekly-plans", tags=["周计划"])


@router.post("", response_model=WeeklyPlanResponse)
async def create_weekly_plan(
    payload: WeeklyPlanCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return weekly_plan_service.create_plan(
        db,
        current_user.id,
        payload.name,
        payload.notes,
    )


@router.get("", response_model=list[WeeklyPlanSummaryResponse])
async def list_weekly_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return weekly_plan_service.list_plans(db, current_user.id)


@router.get("/{plan_id}", response_model=WeeklyPlanResponse)
async def get_weekly_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return weekly_plan_service.get_plan(db, current_user.id, plan_id)


@router.post("/{plan_id}/days", response_model=WeeklyPlanResponse)
async def attach_weekly_plan_day(
    plan_id: int,
    payload: WeeklyPlanAttachDayRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return weekly_plan_service.attach_day_from_session(
        db,
        current_user.id,
        plan_id,
        payload.plan_date,
        payload.meal_plan_id,
        payload.source_session_id,
    )


@router.delete("/{plan_id}/days/{day_id}", response_model=WeeklyPlanResponse)
async def remove_weekly_plan_day(
    plan_id: int,
    day_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return weekly_plan_service.remove_day(db, current_user.id, plan_id, day_id)
