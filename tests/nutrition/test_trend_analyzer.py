import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from intelligent_meal_planner.db.database import Base
from intelligent_meal_planner.db import models
from intelligent_meal_planner.nutrition.trend_analyzer import TrendAnalyzer


@pytest.fixture()
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/trend.db",
                           connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    user = models.User(
        username="trend_user", email="trend@test.com", hashed_password="x",
        age=30, gender="male", height=175, weight=70,
        activity_level="moderate", health_goal="healthy",
    )
    session.add(user)
    session.commit()
    yield session
    session.close()


def test_weekly_trends_with_data(db):
    user = db.query(models.User).first()
    today = date.today()
    for i in range(14):
        db.add(models.IntakeRecord(
            user_id=user.id, date=today - timedelta(days=i),
            meal_type="lunch", actual_calories=600, actual_protein=40,
            actual_carbs=70, actual_fat=20,
        ))
    db.commit()

    analyzer = TrendAnalyzer(db)
    trends = analyzer.get_nutrition_trends(user.id, months=1)
    assert len(trends) >= 2
    assert all("avg_calories" in t for t in trends)


def test_weekly_trends_empty(db):
    user = db.query(models.User).first()
    analyzer = TrendAnalyzer(db)
    trends = analyzer.get_nutrition_trends(user.id, months=1)
    assert trends == []


def test_detect_patterns_weekend_difference(db):
    user = db.query(models.User).first()
    today = date.today()
    for i in range(21):
        d = today - timedelta(days=i)
        cal = 2500 if d.weekday() >= 5 else 1800
        db.add(models.IntakeRecord(
            user_id=user.id, date=d, meal_type="lunch",
            actual_calories=cal, actual_protein=80,
            actual_carbs=200, actual_fat=60,
        ))
    db.commit()

    analyzer = TrendAnalyzer(db)
    patterns = analyzer.detect_patterns(user.id)
    types = [p["type"] for p in patterns]
    assert "weekend_difference" in types
