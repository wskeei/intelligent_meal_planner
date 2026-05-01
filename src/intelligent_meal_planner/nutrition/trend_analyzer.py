"""Long-term nutrition and weight trend analysis."""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from ..db import models


class TrendAnalyzer:
    def __init__(self, db: Session):
        self.db = db

    def get_nutrition_trends(self, user_id: int, months: int = 3) -> list[dict]:
        today = date.today()
        start = today - timedelta(days=months * 30)
        records = (
            self.db.query(models.IntakeRecord)
            .filter(
                models.IntakeRecord.user_id == user_id,
                models.IntakeRecord.date >= start,
                models.IntakeRecord.date <= today,
            )
            .all()
        )

        weeks: dict[str, list] = {}
        for r in records:
            week_start = r.date - timedelta(days=r.date.weekday())
            key = week_start.isoformat()
            weeks.setdefault(key, []).append(r)

        result = []
        for week_key in sorted(weeks.keys()):
            recs = weeks[week_key]
            days_with_data = len(set(r.date for r in recs))
            if days_with_data == 0:
                continue
            result.append({
                "period": week_key,
                "avg_calories": sum(r.actual_calories for r in recs) / days_with_data,
                "avg_protein": sum(r.actual_protein for r in recs) / days_with_data,
                "avg_carbs": sum(r.actual_carbs for r in recs) / days_with_data,
                "avg_fat": sum(r.actual_fat for r in recs) / days_with_data,
                "adherence_rate": min(1.0, days_with_data / 7),
            })

        return result

    def get_weight_trend(self, user_id: int, months: int = 3) -> list[dict]:
        today = date.today()
        start = today - timedelta(days=months * 30)
        logs = (
            self.db.query(models.WeightLog)
            .filter(
                models.WeightLog.user_id == user_id,
                models.WeightLog.date >= start,
            )
            .order_by(models.WeightLog.date)
            .all()
        )

        result = []
        for w in logs:
            result.append({
                "date": w.date.isoformat(),
                "weight": w.weight,
                "body_fat_pct": w.body_fat_pct,
            })
        return result

    def detect_patterns(self, user_id: int) -> list[dict]:
        today = date.today()
        start = today - timedelta(days=28)
        records = (
            self.db.query(models.IntakeRecord)
            .filter(
                models.IntakeRecord.user_id == user_id,
                models.IntakeRecord.date >= start,
            )
            .all()
        )

        patterns = []

        weekday_cals = [r.actual_calories for r in records if r.date.weekday() < 5]
        weekend_cals = [r.actual_calories for r in records if r.date.weekday() >= 5]
        if weekday_cals and weekend_cals:
            wd_avg = sum(weekday_cals) / len(weekday_cals)
            we_avg = sum(weekend_cals) / len(weekend_cals)
            if wd_avg > 0 and abs(we_avg - wd_avg) / wd_avg > 0.15:
                patterns.append({
                    "type": "weekend_difference",
                    "message": f"Weekend intake {'higher' if we_avg > wd_avg else 'lower'} than weekday by {abs(we_avg - wd_avg):.0f} kcal",
                })

        from collections import Counter
        meal_counts = Counter(r.meal_type for r in records)
        total_days = len(set(r.date for r in records))
        if total_days > 7:
            for meal in ["breakfast", "lunch", "dinner"]:
                rate = meal_counts.get(meal, 0) / total_days
                if rate < 0.5:
                    patterns.append({
                        "type": "meal_skip",
                        "message": f"Frequently skipping {meal} (logged {rate:.0%} of days)",
                    })

        return patterns
