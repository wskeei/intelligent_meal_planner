"""Dashboard REST endpoints."""

from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...db.database import get_db
from ..routers.auth import get_current_user
from ..schemas import (
    DailyDashboardResponse,
    NutritionTarget,
    ReminderResponse,
    WeeklyDashboardResponse,
    WeeklySummaryDay,
    WeightLogCreate,
    WeightLogResponse,
    ReportRequest,
    ReportResponse,
    InsightResponse,
)
from ...nutrition.dashboard_service import DashboardService
from ...db import models

router = APIRouter(prefix="/dashboard", tags=["营养看板"])


@router.get("/daily/{summary_date}")
def daily_dashboard(
    summary_date: date,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    svc = DashboardService(db)
    data = svc.daily_summary(current_user, summary_date)
    return DailyDashboardResponse(
        date=data["date"],
        target=NutritionTarget(**data["target"]),
        actual=NutritionTarget(**data["actual"]),
        remaining=NutritionTarget(**data["remaining"]),
        meals_logged=data["meals_logged"],
        completion_rate=data["completion_rate"],
    )


@router.get("/weekly")
def weekly_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    svc = DashboardService(db)
    data = svc.weekly_summary(current_user)
    return WeeklyDashboardResponse(
        days=[WeeklySummaryDay(**d) for d in data["days"]],
        avg_calories=data["avg_calories"],
        avg_protein=data["avg_protein"],
        target_adherence_rate=data["target_adherence_rate"],
    )


@router.post("/weight")
def log_weight(
    payload: WeightLogCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    svc = DashboardService(db)
    wlog = svc.log_weight(
        current_user.id, payload.date, payload.weight,
        payload.body_fat_pct, payload.note,
    )
    return WeightLogResponse.model_validate(wlog)


@router.get("/weight")
def get_weight(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    svc = DashboardService(db)
    history = svc.get_weight_history(current_user.id)
    return [WeightLogResponse.model_validate(w) for w in history]


@router.get("/reminders")
def get_reminders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    svc = DashboardService(db)
    reminders = svc.get_reminders(current_user.id)
    return [ReminderResponse.model_validate(r) for r in reminders]


@router.patch("/reminders/{reminder_id}/dismiss")
def dismiss_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    svc = DashboardService(db)
    svc.dismiss_reminder(reminder_id, current_user.id)
    return {"success": True}


@router.get("/trends")
def get_trends(
    months: int = Query(default=3, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    from ...nutrition.trend_analyzer import TrendAnalyzer
    analyzer = TrendAnalyzer(db)
    return analyzer.get_nutrition_trends(current_user.id, months=months)


@router.post("/report")
def generate_report(
    payload: ReportRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    from ...nutrition.report_generator import ReportGenerator
    gen = ReportGenerator(db)
    if payload.report_type == "monthly":
        html = gen.generate_monthly_report(current_user.id, current_user)
    else:
        html = gen.generate_weekly_report(current_user.id, current_user, payload.start_date)
    return ReportResponse(
        report_type=payload.report_type,
        html=html,
        generated_at=datetime.utcnow(),
    )


@router.get("/insights")
def get_insights(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    from ...nutrition.ai_insights import AIInsightsEngine
    engine = AIInsightsEngine(db)
    insight = engine.generate_daily_insight(current_user.id, current_user, date.today())
    return InsightResponse(insight=insight, generated_at=datetime.utcnow())
