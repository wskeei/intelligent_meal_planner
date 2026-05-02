import copy
from datetime import date, datetime, timezone

from sqlalchemy.orm.attributes import flag_modified

from intelligent_meal_planner.db import models


def make_final_plan_payload(plan_id: str = "plan-001") -> dict:
    return {
        "id": plan_id,
        "created_at": "2026-04-06T10:00:00",
        "meals": [
            {
                "meal_type": "lunch",
                "recipe_id": 101,
                "recipe_name": "测试鸡胸肉",
                "calories": 400,
                "protein": 35,
                "carbs": 20,
                "fat": 12,
                "price": 22,
            },
            {
                "meal_type": "dinner",
                "recipe_id": 102,
                "recipe_name": "测试炒饭",
                "calories": 350,
                "protein": 10,
                "carbs": 50,
                "fat": 8,
                "price": 15,
            },
        ],
        "nutrition": {
            "total_calories": 750,
            "total_protein": 45,
            "total_carbs": 70,
            "total_fat": 20,
            "total_price": 37,
        },
        "target": {
            "health_goal": "healthy",
            "target_calories": 2000,
            "target_protein": 100,
            "target_carbs": 250,
            "target_fat": 65,
            "max_budget": 100,
        },
        "score": 0,
    }


def _auth(client):
    client.post("/api/auth/register", json={
        "username": "confirm_user", "email": "confirm@example.com",
        "password": "secret123", "age": 25, "gender": "male",
        "height": 175, "weight": 70, "activity_level": "moderate",
        "health_goal": "healthy",
    })
    token = client.post("/api/auth/token",
                        data={"username": "confirm_user", "password": "secret123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _seed_recipes(db_session):
    recipes = [
        models.Recipe(
            id=101, name="测试鸡胸肉", category="Meat",
            calories=400, protein=35, carbs=20, fat=12,
            price=22, cooking_time=15, tags=["high-protein"], meal_type=["lunch"],
        ),
        models.Recipe(
            id=102, name="测试炒饭", category="Staple",
            calories=350, protein=10, carbs=50, fat=8,
            price=15, cooking_time=10, tags=["quick"], meal_type=["dinner"],
        ),
    ]
    for r in recipes:
        db_session.add(r)
    db_session.commit()


def _create_plan_with_day(client, auth_header, db_session):
    _seed_recipes(db_session)
    plan_resp = client.post("/api/weekly-plans", headers=auth_header, json={"name": "确认测试"})
    plan_id = plan_resp.json()["id"]

    user = db_session.query(models.User).filter(models.User.username == "confirm_user").first()
    session = models.MealChatSession(
        id="session-confirm",
        user_id=user.id,
        status="finalized",
        collected_slots={},
        final_plan=make_final_plan_payload(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(session)
    db_session.commit()

    attach_resp = client.post(
        f"/api/weekly-plans/{plan_id}/days",
        headers=auth_header,
        json={"plan_date": "2026-04-07", "meal_plan_id": "plan-001", "source_session_id": "session-confirm"},
    )
    return plan_id, attach_resp.json()["days"][0]["id"]


def test_confirm_day_creates_intake_records(client, db_session):
    headers = _auth(client)
    plan_id, day_id = _create_plan_with_day(client, headers, db_session)

    resp = client.post(f"/api/weekly-plans/{plan_id}/days/2026-04-07/confirm", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["synced_count"] == 2

    plan = client.get(f"/api/weekly-plans/{plan_id}", headers=headers).json()
    day = plan["days"][0]
    assert day["completed"] is True
    assert day["completed_at"] is not None

    daily = client.get("/api/intake/records/2026-04-07", headers=headers).json()
    assert daily["meal_count"] == 2
    records = daily["records"]
    sources = {r["source"] for r in records}
    assert sources == {"plan"}
    plan_day_ids = {r["source_plan_day_id"] for r in records}
    assert plan_day_ids == {day_id}


def test_confirm_day_scales_nutrition_by_portion_size(client, db_session):
    headers = _auth(client)
    plan_id, day_id = _create_plan_with_day(client, headers, db_session)

    day = db_session.query(models.WeeklyPlanDay).filter(models.WeeklyPlanDay.id == day_id).first()
    snapshot = copy.deepcopy(day.meal_plan_snapshot)
    snapshot["meals"][0]["portion_size"] = 1.5
    day.meal_plan_snapshot = snapshot
    flag_modified(day, "meal_plan_snapshot")
    db_session.commit()

    resp = client.post(f"/api/weekly-plans/{plan_id}/days/2026-04-07/confirm", headers=headers)
    assert resp.status_code == 200

    daily = client.get("/api/intake/records/2026-04-07", headers=headers).json()
    records = {r["meal_type"]: r for r in daily["records"]}
    assert records["lunch"]["actual_calories"] == 400 * 1.5
    assert records["lunch"]["actual_protein"] == 35 * 1.5
    assert records["lunch"]["actual_carbs"] == 20 * 1.5
    assert records["lunch"]["actual_fat"] == 12 * 1.5
    assert records["lunch"]["portion_size"] == 1.5


def test_duplicate_confirm_returns_409(client, db_session):
    headers = _auth(client)
    plan_id, _ = _create_plan_with_day(client, headers, db_session)

    resp = client.post(f"/api/weekly-plans/{plan_id}/days/2026-04-07/confirm", headers=headers)
    assert resp.status_code == 200

    resp2 = client.post(f"/api/weekly-plans/{plan_id}/days/2026-04-07/confirm", headers=headers)
    assert resp2.status_code == 409


def test_confirm_empty_plan_returns_422(client, db_session):
    headers = _auth(client)
    plan_id, day_id = _create_plan_with_day(client, headers, db_session)

    day = db_session.query(models.WeeklyPlanDay).filter(models.WeeklyPlanDay.id == day_id).first()
    snapshot = copy.deepcopy(day.meal_plan_snapshot)
    snapshot["meals"] = []
    day.meal_plan_snapshot = snapshot
    flag_modified(day, "meal_plan_snapshot")
    db_session.commit()

    resp = client.post(f"/api/weekly-plans/{plan_id}/days/2026-04-07/confirm", headers=headers)
    assert resp.status_code == 422


def test_cancel_confirm_removes_intake_records(client, db_session):
    headers = _auth(client)
    plan_id, _ = _create_plan_with_day(client, headers, db_session)

    client.post(f"/api/weekly-plans/{plan_id}/days/2026-04-07/confirm", headers=headers)
    daily_before = client.get("/api/intake/records/2026-04-07", headers=headers).json()
    assert daily_before["meal_count"] == 2

    cancel_resp = client.post(f"/api/weekly-plans/{plan_id}/days/2026-04-07/cancel-confirm", headers=headers)
    assert cancel_resp.status_code == 200

    plan = client.get(f"/api/weekly-plans/{plan_id}", headers=headers).json()
    day = plan["days"][0]
    assert day["completed"] is False
    assert day["completed_at"] is None

    daily_after = client.get("/api/intake/records/2026-04-07", headers=headers).json()
    assert daily_after["meal_count"] == 0


def test_cancel_unconfirmed_day_returns_409(client, db_session):
    headers = _auth(client)
    plan_id, _ = _create_plan_with_day(client, headers, db_session)

    resp = client.post(f"/api/weekly-plans/{plan_id}/days/2026-04-07/cancel-confirm", headers=headers)
    assert resp.status_code == 409


def test_confirm_day_with_missing_recipe_returns_422(client, db_session):
    headers = _auth(client)
    plan_id, day_id = _create_plan_with_day(client, headers, db_session)

    day = db_session.query(models.WeeklyPlanDay).filter(models.WeeklyPlanDay.id == day_id).first()
    snapshot = copy.deepcopy(day.meal_plan_snapshot)
    snapshot["meals"][0]["recipe_id"] = 99999
    day.meal_plan_snapshot = snapshot
    flag_modified(day, "meal_plan_snapshot")
    db_session.commit()

    resp = client.post(f"/api/weekly-plans/{plan_id}/days/2026-04-07/confirm", headers=headers)
    assert resp.status_code == 422
