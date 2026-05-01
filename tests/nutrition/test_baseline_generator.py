import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from intelligent_meal_planner.db.database import Base
from intelligent_meal_planner.db import models
from intelligent_meal_planner.nutrition.baseline_generator import BaselineGenerator


@pytest.fixture()
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/baseline.db",
                           connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    for i in range(10):
        session.add(models.Recipe(
            id=i + 1, name=f"菜品{i+1}", category="Meat",
            calories=300 + i * 20, protein=20 + i, carbs=40, fat=10,
            price=15, cooking_time=15, tags=[], meal_type=["lunch", "dinner"],
        ))
    for i in range(5):
        session.add(models.Recipe(
            id=100 + i, name=f"早餐{i+1}", category="Breakfast",
            calories=200, protein=10, carbs=30, fat=8,
            price=8, cooking_time=10, tags=[], meal_type=["breakfast"],
        ))

    user = models.User(
        username="baseline_user", email="bl@test.com",
        hashed_password="x", age=28, gender="female",
        height=163, weight=58, activity_level="light", health_goal="lose_weight",
    )
    session.add(user)
    session.commit()
    yield session
    session.close()


def test_baseline_creates_virtual_intake(db):
    user = db.query(models.User).first()
    gen = BaselineGenerator(db)
    gen.initialize_for_user(user)

    records = db.query(models.IntakeRecord).filter_by(user_id=user.id).all()
    assert len(records) >= 7
    assert all(r.source == "auto" for r in records)


def test_baseline_creates_preferences(db):
    user = db.query(models.User).first()
    gen = BaselineGenerator(db)
    gen.initialize_for_user(user)

    prefs = db.query(models.UserPreference).filter_by(user_id=user.id).count()
    assert prefs == 15


def test_baseline_creates_welcome_reminder(db):
    user = db.query(models.User).first()
    gen = BaselineGenerator(db)
    gen.initialize_for_user(user)

    reminders = db.query(models.Reminder).filter_by(user_id=user.id).all()
    assert len(reminders) >= 1
    assert "welcome" in reminders[0].type or "goal" in reminders[0].type


def test_baseline_idempotent(db):
    user = db.query(models.User).first()
    gen = BaselineGenerator(db)
    gen.initialize_for_user(user)
    count_first = db.query(models.IntakeRecord).filter_by(user_id=user.id).count()

    gen.initialize_for_user(user)
    count_second = db.query(models.IntakeRecord).filter_by(user_id=user.id).count()
    assert count_first == count_second
