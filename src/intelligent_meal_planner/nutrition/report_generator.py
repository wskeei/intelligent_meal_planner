"""HTML nutrition report generator."""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from ..db import models


class ReportGenerator:
    def __init__(self, db: Session):
        self.db = db

    def generate_weekly_report(
        self, user_id: int, user: models.User, start_date: date | None = None,
    ) -> str:
        if start_date is None:
            start_date = date.today() - timedelta(days=6)
        end_date = start_date + timedelta(days=6)

        records = (
            self.db.query(models.IntakeRecord)
            .filter(
                models.IntakeRecord.user_id == user_id,
                models.IntakeRecord.date >= start_date,
                models.IntakeRecord.date <= end_date,
            )
            .all()
        )

        days_html = ""
        for i in range(7):
            d = start_date + timedelta(days=i)
            day_recs = [r for r in records if r.date == d]
            cal = sum(r.actual_calories for r in day_recs)
            prot = sum(r.actual_protein for r in day_recs)
            days_html += f"""
            <tr>
                <td>{d.strftime('%m/%d %a')}</td>
                <td>{cal:.0f} kcal</td>
                <td>{prot:.0f}g</td>
                <td>{len(day_recs)}</td>
            </tr>"""

        from collections import Counter
        recipe_counts = Counter()
        for r in records:
            if r.recipe_id:
                recipe = self.db.get(models.Recipe, r.recipe_id)
                if recipe:
                    recipe_counts[recipe.name] += 1
        top_html = "".join(
            f"<li>{name} ({count}x)</li>"
            for name, count in recipe_counts.most_common(5)
        )

        total_cal = sum(r.actual_calories for r in records)
        total_protein = sum(r.actual_protein for r in records)
        days_count = len(set(r.date for r in records)) or 1

        return f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: auto;">
            <h2>Nutrition Report: {start_date} ~ {end_date}</h2>
            <p>User: {user.username} | Goal: {user.health_goal}</p>
            <p>Avg: {total_cal/days_count:.0f} kcal/day | {total_protein/days_count:.0f}g protein/day</p>
            <table style="width:100%; border-collapse: collapse;">
                <thead><tr>
                    <th style="border-bottom:1px solid #ccc; text-align:left;">Day</th>
                    <th style="border-bottom:1px solid #ccc;">Calories</th>
                    <th style="border-bottom:1px solid #ccc;">Protein</th>
                    <th style="border-bottom:1px solid #ccc;">Meals</th>
                </tr></thead>
                <tbody>{days_html}</tbody>
            </table>
            <h3>Top Recipes</h3>
            <ul>{top_html or '<li>No recipe data yet</li>'}</ul>
        </div>
        """

    def generate_monthly_report(self, user_id: int, user: models.User) -> str:
        start_date = date.today().replace(day=1)
        end_date = date.today()
        records = (
            self.db.query(models.IntakeRecord)
            .filter(
                models.IntakeRecord.user_id == user_id,
                models.IntakeRecord.date >= start_date,
                models.IntakeRecord.date <= end_date,
            )
            .all()
        )

        total_cal = sum(r.actual_calories for r in records)
        days_count = len(set(r.date for r in records)) or 1

        return f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: auto;">
            <h2>Monthly Nutrition Report: {start_date.strftime('%B %Y')}</h2>
            <p>User: {user.username} | Goal: {user.health_goal}</p>
            <p>Total meals logged: {len(records)} over {days_count} days</p>
            <p>Average daily calories: {total_cal/days_count:.0f} kcal</p>
            <p>Average daily protein: {sum(r.actual_protein for r in records)/days_count:.0f}g</p>
        </div>
        """
