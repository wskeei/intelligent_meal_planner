from datetime import date, datetime, timedelta

from intelligent_meal_planner.api.schemas import (
    WeeklyPlanDayResponse,
    WeeklyPlanResponse,
)
from intelligent_meal_planner.db import models


def make_final_plan_payload(plan_id: str = "plan-001") -> dict:
    return {
        "id": plan_id,
        "created_at": "2026-04-06T10:00:00",
        "meals": [
            {
                "meal_type": "lunch",
                "recipe_id": 1,
                "recipe_name": "番茄鸡胸肉",
                "calories": 420,
                "protein": 36,
                "carbs": 18,
                "fat": 14,
                "price": 22,
                "ingredients": [
                    {"name": "测试鸡胸肉", "amount": "400g"},
                    {"name": "黑胡椒", "amount": "5g"},
                ],
            }
        ],
        "nutrition": {
            "total_calories": 420,
            "total_protein": 36,
            "total_carbs": 18,
            "total_fat": 14,
            "total_price": 22,
            "calories_achievement": 24,
            "protein_achievement": 36,
            "budget_usage": 18,
        },
        "target": {
            "health_goal": "healthy",
            "target_calories": 1800,
            "target_protein": 100,
            "target_carbs": 180,
            "target_fat": 60,
            "max_budget": 120,
            "disliked_foods": [],
            "preferred_tags": [],
        },
        "score": 0,
    }


def seeded_meal_chat_session(db_session, auth_header):
    user = (
        db_session.query(models.User)
        .filter(models.User.username == "planner_user")
        .first()
    )
    session = models.MealChatSession(
        id="session-1",
        user_id=user.id,
        status="finalized",
        collected_slots={},
        final_plan=make_final_plan_payload(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


def test_weekly_plan_response_serializes_day_snapshots():
    payload = WeeklyPlanResponse(
        id=1,
        name="本周控卡计划",
        notes=None,
        created_at=datetime(2026, 4, 6, 10, 0, 0),
        updated_at=datetime(2026, 4, 6, 10, 0, 0),
        days=[
            WeeklyPlanDayResponse(
                id=11,
                plan_date=date(2026, 4, 6),
                source_session_id="session-1",
                meal_plan_snapshot=make_final_plan_payload("plan-1"),
                nutrition_snapshot={"total_calories": 420},
            )
        ],
    )

    assert payload.days[0].source_session_id == "session-1"


def test_create_weekly_plan_requires_auth_and_returns_empty_days(client, auth_header):
    response = client.post(
        "/api/weekly-plans",
        headers=auth_header,
        json={"name": "本周减脂计划"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "本周减脂计划"
    assert response.json()["days"] == []


def test_attach_finalized_meal_plan_snapshot_to_weekly_plan(
    client, auth_header, db_session
):
    seeded_meal_chat_session(db_session, auth_header)

    plan_response = client.post(
        "/api/weekly-plans",
        headers=auth_header,
        json={"name": "第15周计划"},
    )
    plan_id = plan_response.json()["id"]

    response = client.post(
        f"/api/weekly-plans/{plan_id}/days",
        headers=auth_header,
        json={
            "plan_date": "2026-04-07",
            "meal_plan_id": "plan-001",
            "source_session_id": "session-1",
        },
    )

    assert response.status_code == 200
    assert response.json()["days"][0]["plan_date"] == "2026-04-07"
    assert response.json()["days"][0]["source_session_id"] == "session-1"


def test_attach_negotiated_primary_meal_plan_snapshot_to_weekly_plan(
    client, auth_header, db_session
):
    user = (
        db_session.query(models.User)
        .filter(models.User.username == "planner_user")
        .first()
    )
    session = models.MealChatSession(
        id="session-negotiated",
        user_id=user.id,
        status="finalized",
        collected_slots={},
        final_plan={
            "primary": make_final_plan_payload(),
            "alternatives": [],
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(session)
    db_session.commit()

    plan_response = client.post(
        "/api/weekly-plans",
        headers=auth_header,
        json={"name": "协商结果挂载"},
    )

    response = client.post(
        f"/api/weekly-plans/{plan_response.json()['id']}/days",
        headers=auth_header,
        json={
            "plan_date": "2026-04-09",
            "meal_plan_id": "plan-001",
            "source_session_id": "session-negotiated",
        },
    )

    assert response.status_code == 200
    assert response.json()["days"][0]["meal_plan_snapshot"]["id"] == "plan-001"


def test_attach_day_updates_weekly_plan_timestamp(client, auth_header, db_session):
    seeded_meal_chat_session(db_session, auth_header)
    plan = models.WeeklyPlan(
        user_id=(
            db_session.query(models.User)
            .filter(models.User.username == "planner_user")
            .first()
            .id
        ),
        name="时间戳测试",
        notes=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow() - timedelta(days=1),
    )
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)
    original_updated_at = plan.updated_at

    response = client.post(
        f"/api/weekly-plans/{plan.id}/days",
        headers=auth_header,
        json={
            "plan_date": "2026-04-10",
            "meal_plan_id": "plan-001",
            "source_session_id": "session-1",
        },
    )

    assert response.status_code == 200
    db_session.expire_all()
    refreshed = (
        db_session.query(models.WeeklyPlan)
        .filter(models.WeeklyPlan.id == plan.id)
        .first()
    )
    assert refreshed.updated_at > original_updated_at
