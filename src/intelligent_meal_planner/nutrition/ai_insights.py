"""DeepSeek LLM-powered health insights."""

import logging
import os
from datetime import date, timedelta

from sqlalchemy.orm import Session

from ..db import models
from ..meal_chat.target_mapper import build_hidden_targets

logger = logging.getLogger(__name__)


class AIInsightsEngine:
    def __init__(self, db: Session):
        self.db = db

    def generate_daily_insight(
        self, user_id: int, user: models.User, target_date: date,
    ) -> str:
        records = (
            self.db.query(models.IntakeRecord)
            .filter_by(user_id=user_id, date=target_date)
            .all()
        )

        total_cal = sum(r.actual_calories for r in records)
        total_prot = sum(r.actual_protein for r in records)

        api_key = os.getenv("DEEPSEEK_API_KEY")
        if api_key:
            try:
                return self._call_llm(user, records, target_date)
            except Exception as exc:
                logger.warning("LLM insight failed, using fallback: %s", exc)

        return self._rule_based_insight(user, total_cal, total_prot, len(records))

    def generate_weekly_insight(
        self, user_id: int, user: models.User,
    ) -> str:
        today = date.today()
        start = today - timedelta(days=6)
        records = (
            self.db.query(models.IntakeRecord)
            .filter(
                models.IntakeRecord.user_id == user_id,
                models.IntakeRecord.date >= start,
            )
            .all()
        )

        if not records:
            return "No data for this week yet. Start logging your meals!"

        total_cal = sum(r.actual_calories for r in records)
        days = len(set(r.date for r in records)) or 1
        avg_cal = total_cal / days

        return f"This week: avg {avg_cal:.0f} kcal/day over {days} days. {'On track!' if 1500 < avg_cal < 2500 else 'Consider adjusting portion sizes.'}"

    def _rule_based_insight(
        self, user: models.User, total_cal: float, total_prot: float, meal_count: int,
    ) -> str:
        if meal_count == 0:
            targets = {}
            if all([user.weight, user.height, user.age, user.gender, user.activity_level]):
                targets = build_hidden_targets(
                    {"weight": user.weight, "height": user.height,
                     "age": user.age, "gender": user.gender,
                     "activity_level": user.activity_level},
                    user.health_goal or "healthy",
                )
            cal_target = int(targets.get("target_calories", 2000))
            return f"No meals logged today. Your target: {cal_target} kcal. Start with a balanced lunch!"

        insights = []
        if total_cal < 1200:
            insights.append(f"Low intake today ({total_cal:.0f} kcal). Make sure to eat enough.")
        elif total_cal > 2500:
            insights.append(f"Higher intake today ({total_cal:.0f} kcal). Consider lighter dinner.")
        else:
            insights.append(f"Good intake today ({total_cal:.0f} kcal, {total_prot:.0f}g protein).")

        if total_prot < 50:
            insights.append("Protein is low — add eggs, chicken, or tofu to your next meal.")

        return " ".join(insights)

    def _call_llm(self, user, records, target_date):
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
            openai_api_base=os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1"),
            temperature=0.7,
        )

        intake_summary = "; ".join(
            f"{r.meal_type}: {r.actual_calories:.0f}kcal, {r.actual_protein:.0f}g protein"
            for r in records
        )

        prompt = (
            f"You are a nutrition advisor. User: {user.username}, goal: {user.health_goal}. "
            f"Today's intake ({target_date}): {intake_summary or 'no meals logged'}. "
            f"Give 1-2 short actionable suggestions in the user's language. Keep under 100 words."
        )

        response = llm.invoke(prompt)
        return response.content
