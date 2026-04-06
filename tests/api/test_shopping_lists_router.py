from datetime import datetime, timedelta

from intelligent_meal_planner.api.schemas import ShoppingListItemResponse
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


def seeded_weekly_plan(db_session, auth_header):
    user = (
        db_session.query(models.User)
        .filter(models.User.username == "planner_user")
        .first()
    )
    plan = models.WeeklyPlan(
        user_id=user.id,
        name="第15周计划",
        notes=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)

    day = models.WeeklyPlanDay(
        weekly_plan_id=plan.id,
        plan_date=datetime(2026, 4, 8).date(),
        source_session_id="session-1",
        meal_plan_snapshot=make_final_plan_payload(),
        nutrition_snapshot=make_final_plan_payload()["nutrition"],
    )
    db_session.add(day)
    db_session.commit()
    db_session.refresh(plan)
    return plan


def seeded_shopping_list(db_session, auth_header):
    plan = seeded_weekly_plan(db_session, auth_header)
    shopping_list = models.ShoppingList(
        user_id=plan.user_id,
        weekly_plan_id=plan.id,
        name="第15周采购",
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(shopping_list)
    db_session.commit()
    db_session.refresh(shopping_list)

    item = models.ShoppingListItem(
        shopping_list_id=shopping_list.id,
        ingredient_name="鸡胸肉",
        display_amount="400g",
        checked=False,
        category="protein",
        source_kind="weekly-plan",
        source_refs=[
            {
                "plan_date": "2026-04-08",
                "meal_type": "lunch",
                "recipe_name": "番茄鸡胸肉",
            }
        ],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(shopping_list)
    return shopping_list


def test_shopping_list_item_response_keeps_source_recipes():
    item = ShoppingListItemResponse(
        id=21,
        ingredient_name="鸡胸肉",
        display_amount="400g",
        checked=False,
        category="protein",
        source_kind="weekly-plan",
        sources=[
            {
                "plan_date": "2026-04-06",
                "meal_type": "lunch",
                "recipe_name": "香煎鸡胸",
            }
        ],
    )

    assert item.sources[0]["recipe_name"] == "香煎鸡胸"


def test_generate_shopping_list_from_weekly_plan(client, auth_header, db_session):
    plan = seeded_weekly_plan(db_session, auth_header)

    response = client.post(
        "/api/shopping-lists/generate",
        headers=auth_header,
        json={"weekly_plan_id": plan.id, "name": "第15周采购"},
    )

    assert response.status_code == 200
    assert response.json()["weekly_plan_id"] == plan.id
    ingredient_names = [item["ingredient_name"] for item in response.json()["items"]]
    assert "测试鸡胸肉" in ingredient_names
    generated_item = next(
        item for item in response.json()["items"] if item["ingredient_name"] == "测试鸡胸肉"
    )
    assert generated_item["sources"][0]["recipe_name"] == "番茄鸡胸肉"


def test_toggle_shopping_list_item_checked_state(
    client, auth_header, db_session
):
    shopping_list = seeded_shopping_list(db_session, auth_header)
    item = shopping_list.items[0]

    response = client.patch(
        f"/api/shopping-lists/{shopping_list.id}/items/{item.id}",
        headers=auth_header,
        json={"checked": True},
    )

    assert response.status_code == 200
    assert response.json()["items"][0]["checked"] is True


def test_user_can_attach_session_to_weekly_plan_then_generate_shopping_list(
    client, auth_header, db_session
):
    user = (
        db_session.query(models.User)
        .filter(models.User.username == "planner_user")
        .first()
    )
    session = models.MealChatSession(
        id="session-chain",
        user_id=user.id,
        status="finalized",
        collected_slots={},
        final_plan=make_final_plan_payload(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(session)
    db_session.commit()

    create_plan = client.post(
        "/api/weekly-plans",
        headers=auth_header,
        json={"name": "第15周"},
    )
    plan_id = create_plan.json()["id"]

    attach = client.post(
        f"/api/weekly-plans/{plan_id}/days",
        headers=auth_header,
        json={
            "plan_date": "2026-04-08",
            "meal_plan_id": "plan-001",
            "source_session_id": "session-chain",
        },
    )
    assert attach.status_code == 200

    generated = client.post(
        "/api/shopping-lists/generate",
        headers=auth_header,
        json={"weekly_plan_id": plan_id},
    )

    assert generated.status_code == 200
    assert generated.json()["items"]


def test_generate_shopping_list_aggregates_repeated_quantities(
    client, auth_header, db_session
):
    plan = seeded_weekly_plan(db_session, auth_header)
    second_day = models.WeeklyPlanDay(
        weekly_plan_id=plan.id,
        plan_date=datetime(2026, 4, 9).date(),
        source_session_id="session-2",
        meal_plan_snapshot={
            **make_final_plan_payload("plan-002"),
            "meals": [
                {
                    **make_final_plan_payload("plan-002")["meals"][0],
                    "ingredients": [
                        {"name": "测试鸡胸肉", "amount": "100g"},
                        {"name": "黑胡椒", "amount": "2g"},
                    ],
                }
            ],
        },
        nutrition_snapshot=make_final_plan_payload("plan-002")["nutrition"],
    )
    db_session.add(second_day)
    db_session.commit()

    response = client.post(
        "/api/shopping-lists/generate",
        headers=auth_header,
        json={"weekly_plan_id": plan.id, "name": "第15周采购"},
    )

    assert response.status_code == 200
    aggregated_item = next(
        item for item in response.json()["items"] if item["ingredient_name"] == "测试鸡胸肉"
    )
    assert aggregated_item["display_amount"] == "500g"
    assert len(aggregated_item["sources"]) == 2


def test_toggle_shopping_list_item_updates_parent_timestamp(
    client, auth_header, db_session
):
    shopping_list = seeded_shopping_list(db_session, auth_header)
    item = shopping_list.items[0]
    original_updated_at = shopping_list.updated_at

    db_session.query(models.ShoppingList).filter_by(id=shopping_list.id).update(
        {"updated_at": datetime.utcnow() - timedelta(days=1)}
    )
    db_session.commit()

    response = client.patch(
        f"/api/shopping-lists/{shopping_list.id}/items/{item.id}",
        headers=auth_header,
        json={"checked": True},
    )

    assert response.status_code == 200
    db_session.expire_all()
    refreshed = (
        db_session.query(models.ShoppingList)
        .filter(models.ShoppingList.id == shopping_list.id)
        .first()
    )
    assert refreshed.updated_at > original_updated_at
