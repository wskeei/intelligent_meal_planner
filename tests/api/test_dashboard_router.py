from datetime import date, timedelta

from intelligent_meal_planner.db import models


def _auth(client):
    client.post("/api/auth/register", json={
        "username": "dash_user", "email": "dash@example.com",
        "password": "secret123", "age": 30, "gender": "male",
        "height": 175, "weight": 70, "activity_level": "moderate",
        "health_goal": "healthy",
    })
    token = client.post("/api/auth/token",
                        data={"username": "dash_user", "password": "secret123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_daily_dashboard_empty(client):
    headers = _auth(client)
    resp = client.get(f"/api/dashboard/daily/{date.today()}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["actual"]["calories"] == 0
    assert data["meals_logged"] == 0


def test_weekly_dashboard(client, db_session):
    headers = _auth(client)

    user = db_session.query(models.User).filter_by(username="dash_user").first()
    for i in range(3):
        db_session.add(models.IntakeRecord(
            user_id=user.id,
            date=date.today() - timedelta(days=i),
            meal_type="lunch",
            actual_calories=500,
            actual_protein=30,
            actual_carbs=60,
            actual_fat=15,
        ))
    db_session.commit()

    resp = client.get("/api/dashboard/weekly", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["days"]) == 7


def test_weight_log_crud(client):
    headers = _auth(client)

    resp = client.post("/api/dashboard/weight", json={
        "date": str(date.today()), "weight": 70.5,
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["weight"] == 70.5

    resp = client.get("/api/dashboard/weight", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_reminders_empty(client):
    headers = _auth(client)
    resp = client.get("/api/dashboard/reminders", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []
