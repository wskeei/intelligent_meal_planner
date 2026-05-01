from datetime import date

from intelligent_meal_planner.db import models


def _auth(client):
    client.post("/api/auth/register", json={
        "username": "intake_user", "email": "intake@example.com",
        "password": "secret123", "age": 25, "gender": "male",
        "height": 175, "weight": 70, "activity_level": "moderate",
        "health_goal": "healthy",
    })
    token = client.post("/api/auth/token",
                        data={"username": "intake_user", "password": "secret123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _seed_recipe(db_session):
    recipe = models.Recipe(
        id=999, name="测试炒饭", category="Staple",
        calories=350, protein=12, carbs=55, fat=8,
        price=12, cooking_time=15, tags=["quick"], meal_type=["lunch", "dinner"],
    )
    db_session.add(recipe)
    db_session.commit()
    return recipe


def test_log_meal_from_recipe(client, db_session):
    headers = _auth(client)
    _seed_recipe(db_session)

    resp = client.post("/api/intake/records", json={
        "date": "2026-05-02", "meal_type": "lunch",
        "recipe_id": 999, "portion_size": 1.5, "rating": 4,
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["recipe_name"] == "测试炒饭"
    assert data["actual_calories"] == 350 * 1.5
    assert data["portion_size"] == 1.5
    assert data["rating"] == 4
    assert data["source"] == "manual"


def test_log_custom_food(client, db_session):
    headers = _auth(client)

    resp = client.post("/api/intake/records", json={
        "date": "2026-05-02", "meal_type": "snack",
        "custom_food_name": "苹果",
        "actual_calories": 95, "actual_protein": 0.5,
        "actual_carbs": 25, "actual_fat": 0.3,
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["custom_food_name"] == "苹果"
    assert data["actual_calories"] == 95


def test_get_daily_records(client, db_session):
    headers = _auth(client)
    _seed_recipe(db_session)

    client.post("/api/intake/records", json={
        "date": "2026-05-02", "meal_type": "lunch", "recipe_id": 999,
    }, headers=headers)

    resp = client.get("/api/intake/records/2026-05-02", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["meal_count"] == 1
    assert len(data["records"]) == 1


def test_update_record(client, db_session):
    headers = _auth(client)
    _seed_recipe(db_session)

    create_resp = client.post("/api/intake/records", json={
        "date": "2026-05-02", "meal_type": "lunch", "recipe_id": 999,
    }, headers=headers)
    record_id = create_resp.json()["id"]

    resp = client.patch(f"/api/intake/records/{record_id}", json={
        "portion_size": 2.0, "rating": 5,
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["portion_size"] == 2.0
    assert resp.json()["rating"] == 5


def test_delete_record(client, db_session):
    headers = _auth(client)
    _seed_recipe(db_session)

    create_resp = client.post("/api/intake/records", json={
        "date": "2026-05-02", "meal_type": "lunch", "recipe_id": 999,
    }, headers=headers)
    record_id = create_resp.json()["id"]

    resp = client.delete(f"/api/intake/records/{record_id}", headers=headers)
    assert resp.status_code == 200

    get_resp = client.get("/api/intake/records/2026-05-02", headers=headers)
    assert get_resp.json()["meal_count"] == 0


def test_quick_log(client, db_session):
    headers = _auth(client)
    _seed_recipe(db_session)

    resp = client.post("/api/intake/quick-log", json={
        "date": "2026-05-02", "recipe_id": 999, "portion_size": 1.0,
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["meal_type"] == "lunch"
