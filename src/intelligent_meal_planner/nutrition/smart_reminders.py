"""Rule-based smart reminder engine."""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from ..db import models
from ..meal_chat.target_mapper import build_hidden_targets


class SmartReminderEngine:
    def __init__(self, db: Session):
        self.db = db

    def _get_targets(self, user: models.User) -> dict:
        if not all([user.weight, user.height, user.age, user.gender, user.activity_level]):
            return {"target_calories": 2000, "target_protein": 100}
        return build_hidden_targets(
            {"weight": user.weight, "height": user.height,
             "age": user.age, "gender": user.gender,
             "activity_level": user.activity_level},
            user.health_goal or "healthy",
        )

    def _has_recent_reminder(self, user_id: int, rtype: str, days: int = 1) -> bool:
        cutoff = date.today() - timedelta(days=days)
        return (
            self.db.query(models.Reminder)
            .filter(
                models.Reminder.user_id == user_id,
                models.Reminder.type == rtype,
                models.Reminder.created_at >= cutoff,
            )
            .count()
            > 0
        )

    def check_and_generate(self, user_id: int) -> list[models.Reminder]:
        user = self.db.get(models.User, user_id)
        if not user:
            return []

        targets = self._get_targets(user)
        today = date.today()
        reminders = []

        recent_records = []
        for i in range(3):
            d = today - timedelta(days=i)
            day_records = (
                self.db.query(models.IntakeRecord)
                .filter_by(user_id=user_id, date=d)
                .all()
            )
            if day_records:
                recent_records.append({
                    "date": d,
                    "calories": sum(r.actual_calories for r in day_records),
                    "protein": sum(r.actual_protein for r in day_records),
                })

        if len(recent_records) < 3:
            return []

        cal_target = targets["target_calories"]
        if all(d["calories"] > cal_target * 1.1 for d in recent_records):
            if not self._has_recent_reminder(user_id, "consecutive_excess"):
                r = self._create_reminder(
                    user_id, "consecutive_excess", "warning",
                    "Calorie Intake Alert",
                    f"You've exceeded your {int(cal_target)} kcal target for 3 consecutive days. Consider lighter options.",
                )
                reminders.append(r)

        prot_target = targets["target_protein"]
        if all(d["protein"] < prot_target * 0.7 for d in recent_records):
            if not self._has_recent_reminder(user_id, "protein_low"):
                r = self._create_reminder(
                    user_id, "protein_low", "warning",
                    "Low Protein Alert",
                    f"Protein has been below {int(prot_target * 0.7)}g for 3 days. Add eggs, chicken, or tofu.",
                )
                reminders.append(r)

        return reminders

    def _create_reminder(
        self, user_id: int, rtype: str, severity: str, title: str, message: str,
    ) -> models.Reminder:
        r = models.Reminder(
            user_id=user_id, type=rtype, title=title,
            message=message, severity=severity,
        )
        self.db.add(r)
        self.db.commit()
        self.db.refresh(r)
        return r

    def get_unread(self, user_id: int) -> list[models.Reminder]:
        return (
            self.db.query(models.Reminder)
            .filter_by(user_id=user_id, is_read=False)
            .order_by(models.Reminder.created_at.desc())
            .all()
        )
