import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from intelligent_meal_planner.db.database import Base
from intelligent_meal_planner.db import models
from intelligent_meal_planner.nutrition.smart_reminders import SmartReminderEngine


@pytest.fixture()
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/remind.db",
                           connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    user = models.User(
        username="remind_user", email="rem@test.com", hashed_password="x",
        age=30, gender="male", height=175, weight=70,
        activity_level="moderate", health_goal="healthy",
    )
    session.add(user)
    session.commit()
    yield session
    session.close()


def test_consecutive_excess_generates_reminder(db):
    user = db.query(models.User).first()
    today = date.today()
    for i in range(3):
        db.add(models.IntakeRecord(
            user_id=user.id, date=today - timedelta(days=i),
            meal_type="lunch",
            actual_calories=3000, actual_protein=150,
            actual_carbs=300, actual_fat=80,
        ))
    db.commit()

    engine = SmartReminderEngine(db)
    reminders = engine.check_and_generate(user.id)
    types = [r.type for r in reminders]
    assert "consecutive_excess" in types


def test_low_protein_generates_reminder(db):
    user = db.query(models.User).first()
    today = date.today()
    for i in range(3):
        db.add(models.IntakeRecord(
            user_id=user.id, date=today - timedelta(days=i),
            meal_type="lunch",
            actual_calories=1800, actual_protein=30,
            actual_carbs=250, actual_fat=60,
        ))
    db.commit()

    engine = SmartReminderEngine(db)
    reminders = engine.check_and_generate(user.id)
    types = [r.type for r in reminders]
    assert "protein_low" in types


def test_no_reminder_when_on_target(db):
    user = db.query(models.User).first()
    today = date.today()
    for i in range(3):
        db.add(models.IntakeRecord(
            user_id=user.id, date=today - timedelta(days=i),
            meal_type="lunch",
            actual_calories=2500, actual_protein=160,
            actual_carbs=250, actual_fat=65,
        ))
    db.commit()

    engine = SmartReminderEngine(db)
    reminders = engine.check_and_generate(user.id)
    types = [r.type for r in reminders]
    assert "consecutive_excess" not in types
    assert "protein_low" not in types
