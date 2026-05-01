import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from intelligent_meal_planner.db.database import Base
from intelligent_meal_planner.db import models
from intelligent_meal_planner.nutrition.report_generator import ReportGenerator
from intelligent_meal_planner.nutrition.ai_insights import AIInsightsEngine


@pytest.fixture()
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/report.db",
                           connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    user = models.User(
        username="report_user", email="rep@test.com", hashed_password="x",
        age=30, gender="male", height=175, weight=70,
        activity_level="moderate", health_goal="healthy",
    )
    session.add(user)
    session.commit()

    today = date.today()
    for i in range(7):
        session.add(models.IntakeRecord(
            user_id=user.id, date=today - timedelta(days=i),
            meal_type="lunch", actual_calories=600, actual_protein=40,
            actual_carbs=70, actual_fat=20, source="manual",
        ))
    session.commit()
    yield session
    session.close()


def test_weekly_report_returns_html(db):
    user = db.query(models.User).first()
    gen = ReportGenerator(db)
    html = gen.generate_weekly_report(user.id, user)
    assert "<table" in html
    assert user.username in html


def test_monthly_report_returns_html(db):
    user = db.query(models.User).first()
    gen = ReportGenerator(db)
    html = gen.generate_monthly_report(user.id, user)
    assert "Monthly" in html or "Report" in html


def test_daily_insight_no_api_key(db):
    user = db.query(models.User).first()
    engine = AIInsightsEngine(db)
    insight = engine.generate_daily_insight(user.id, user, date.today())
    assert len(insight) > 0


def test_daily_insight_empty_day(db):
    user = db.query(models.User).first()
    engine = AIInsightsEngine(db)
    insight = engine.generate_daily_insight(user.id, user, date.today() - timedelta(days=30))
    assert len(insight) > 0
