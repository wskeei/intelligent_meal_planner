from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import User
from ..exceptions import (
    DayAlreadyConfirmedError,
    DayNotConfirmedError,
    EmptyMealPlanError,
    RecipeMissingError,
    WeeklyPlanDayNotFoundError,
)
from ..schemas import (
    CancelConfirmResponse,
    ConfirmDayResponse,
    WeeklyPlanAttachDayRequest,
    WeeklyPlanCreateRequest,
    WeeklyPlanResponse,
    WeeklyPlanSummaryResponse,
    WeeklyPlanUpdateRequest,
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


@router.patch("/{plan_id}", response_model=WeeklyPlanResponse)
async def update_weekly_plan(
    plan_id: int,
    payload: WeeklyPlanUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return weekly_plan_service.update_plan(
        db,
        current_user.id,
        plan_id,
        payload.name,
        payload.notes,
    )


@router.delete("/{plan_id}")
async def delete_weekly_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    weekly_plan_service.delete_plan(db, current_user.id, plan_id)
    return {"success": True}


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


@router.post("/{plan_id}/days/{plan_date}/confirm", response_model=ConfirmDayResponse)
async def confirm_weekly_plan_day(
    plan_id: int,
    plan_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return weekly_plan_service.confirm_day(db, current_user.id, plan_id, plan_date)
    except WeeklyPlanDayNotFoundError:
        raise HTTPException(status_code=404, detail="Weekly plan day not found")
    except DayAlreadyConfirmedError:
        raise HTTPException(status_code=409, detail="Day already confirmed")
    except EmptyMealPlanError:
        raise HTTPException(status_code=422, detail="No meals in plan for this day")
    except RecipeMissingError:
        raise HTTPException(status_code=422, detail="Recipe data missing for planned meal")


@router.post("/{plan_id}/days/{plan_date}/cancel-confirm", response_model=CancelConfirmResponse)
async def cancel_confirm_weekly_plan_day(
    plan_id: int,
    plan_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        weekly_plan_service.cancel_confirm(db, current_user.id, plan_id, plan_date)
    except WeeklyPlanDayNotFoundError:
        raise HTTPException(status_code=404, detail="Weekly plan day not found")
    except DayNotConfirmedError:
        raise HTTPException(status_code=409, detail="Day not confirmed yet")
    return CancelConfirmResponse()
