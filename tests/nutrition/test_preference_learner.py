import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from intelligent_meal_planner.db.database import Base
from intelligent_meal_planner.db import models
from intelligent_meal_planner.nutrition.preference_learner import PreferenceLearner


@pytest.fixture()
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/pref.db",
                           connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    user = models.User(
        username="pref_user", email="pref@test.com", hashed_password="x",
        age=30, gender="male", height=175, weight=70,
        activity_level="moderate", health_goal="healthy",
    )
    recipe = models.Recipe(
        id=1, name="测试菜", category="Meat", calories=300, protein=25,
        carbs=30, fat=10, price=15, cooking_time=15, tags=[], meal_type=["lunch"],
    )
    session.add_all([user, recipe])
    session.commit()

    session.add(models.UserPreference(
        user_id=user.id, recipe_id=recipe.id, preference_score=0.5,
    ))
    session.commit()
    yield session
    session.close()


def test_update_from_rating_increases(db):
    learner = PreferenceLearner(db)
    user = db.query(models.User).first()
    learner.update_from_rating(user.id, 1, 5)
    pref = db.query(models.UserPreference).filter_by(user_id=user.id, recipe_id=1).first()
    assert pref.preference_score > 0.5
    assert pref.avg_rating == 5.0


def test_update_from_rating_decreases(db):
    learner = PreferenceLearner(db)
    user = db.query(models.User).first()
    learner.update_from_rating(user.id, 1, 1)
    pref = db.query(models.UserPreference).filter_by(user_id=user.id, recipe_id=1).first()
    assert pref.preference_score < 0.5


def test_update_from_selection(db):
    learner = PreferenceLearner(db)
    user = db.query(models.User).first()
    learner.update_from_selection(user.id, 1)
    pref = db.query(models.UserPreference).filter_by(user_id=user.id, recipe_id=1).first()
    assert pref.times_eaten == 1
    assert pref.preference_score > 0.5


def test_update_from_skip(db):
    learner = PreferenceLearner(db)
    user = db.query(models.User).first()
    learner.update_from_skip(user.id, 1)
    pref = db.query(models.UserPreference).filter_by(user_id=user.id, recipe_id=1).first()
    assert pref.times_skipped == 1
    assert pref.preference_score < 0.5


def test_taste_profile(db):
    learner = PreferenceLearner(db)
    user = db.query(models.User).first()
    profile = learner.get_user_taste_profile(user.id)
    assert "preferred_categories" in profile
    assert "disliked_recipes" in profile
