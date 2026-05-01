"""Dashboard aggregation: daily/weekly stats, weight logs, reminders."""

from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from ..db import models
from ..meal_chat.target_mapper import build_hidden_targets


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def _get_targets(self, user: models.User) -> dict:
        if not all([user.weight, user.height, user.age, user.gender, user.activity_level]):
            return {
                "target_calories": 2000, "target_protein": 100,
                "target_carbs": 250, "target_fat": 65,
            }
        return build_hidden_targets(
            {"weight": user.weight, "height": user.height,
             "age": user.age, "gender": user.gender,
             "activity_level": user.activity_level},
            user.health_goal or "healthy",
        )

    def daily_summary(self, user: models.User, summary_date: date) -> dict:
        targets = self._get_targets(user)
        records = (
            self.db.query(models.IntakeRecord)
            .filter_by(user_id=user.id, date=summary_date)
            .all()
        )
        actual = {
            "calories": sum(r.actual_calories for r in records),
            "protein": sum(r.actual_protein for r in records),
            "carbs": sum(r.actual_carbs for r in records),
            "fat": sum(r.actual_fat for r in records),
        }
        remaining = {
            "calories": max(0, targets["target_calories"] - actual["calories"]),
            "protein": max(0, targets["target_protein"] - actual["protein"]),
            "carbs": max(0, targets["target_carbs"] - actual["carbs"]),
            "fat": max(0, targets["target_fat"] - actual["fat"]),
        }
        return {
            "date": summary_date,
            "target": {
                "calories": targets["target_calories"],
                "protein": targets["target_protein"],
                "carbs": targets["target_carbs"],
                "fat": targets["target_fat"],
            },
            "actual": actual,
            "remaining": remaining,
            "meals_logged": len(records),
            "completion_rate": min(1.0, actual["calories"] / targets["target_calories"]) if targets["target_calories"] else 0,
        }

    def weekly_summary(self, user: models.User) -> dict:
        today = date.today()
        targets = self._get_targets(user)
        days = []
        total_cal = 0
        total_protein = 0
        on_target_count = 0

        for i in range(7):
            d = today - timedelta(days=6 - i)
            records = (
                self.db.query(models.IntakeRecord)
                .filter_by(user_id=user.id, date=d)
                .all()
            )
            cal = sum(r.actual_calories for r in records)
            prot = sum(r.actual_protein for r in records)
            carbs = sum(r.actual_carbs for r in records)
            fat = sum(r.actual_fat for r in records)
            on_target = abs(cal - targets["target_calories"]) / targets["target_calories"] < 0.15 if targets["target_calories"] else False
            if on_target:
                on_target_count += 1
            total_cal += cal
            total_protein += prot
            days.append({
                "date": d,
                "calories": cal, "protein": prot,
                "carbs": carbs, "fat": fat,
                "meal_count": len(records),
                "on_target": on_target,
            })

        return {
            "days": days,
            "avg_calories": total_cal / 7,
            "avg_protein": total_protein / 7,
            "target_adherence_rate": on_target_count / 7,
        }

    def log_weight(self, user_id: int, log_date: date, weight: float,
                   body_fat_pct: Optional[float] = None, note: Optional[str] = None) -> models.WeightLog:
        wlog = models.WeightLog(
            user_id=user_id, date=log_date, weight=weight,
            body_fat_pct=body_fat_pct, note=note,
        )
        self.db.add(wlog)
        self.db.commit()
        self.db.refresh(wlog)
        return wlog

    def get_weight_history(self, user_id: int, limit: int = 90) -> list:
        return (
            self.db.query(models.WeightLog)
            .filter_by(user_id=user_id)
            .order_by(models.WeightLog.date.desc())
            .limit(limit)
            .all()
        )

    def get_reminders(self, user_id: int) -> list:
        return (
            self.db.query(models.Reminder)
            .filter_by(user_id=user_id, is_read=False)
            .order_by(models.Reminder.created_at.desc())
            .all()
        )

    def dismiss_reminder(self, reminder_id: int, user_id: int) -> None:
        r = self.db.query(models.Reminder).filter_by(id=reminder_id, user_id=user_id).first()
        if r:
            r.is_read = True
            self.db.commit()
