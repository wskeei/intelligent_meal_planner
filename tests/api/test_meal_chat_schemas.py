from intelligent_meal_planner.api.schemas import MealChatSessionResponse, MealPlanResponse


def test_meal_chat_session_response_parses_structured_meal_plan_payload():
    payload = {
        "session_id": "session001",
        "status": "finalized",
        "messages": [{"role": "assistant", "content": "完成"}],
        "meal_plan": {
            "id": "plan001",
            "created_at": "2026-04-04T10:00:00",
            "meals": [],
            "nutrition": {
                "total_calories": 1800,
                "total_protein": 120,
                "total_carbs": 180,
                "total_fat": 55,
                "total_price": 120,
                "calories_achievement": 100,
                "protein_achievement": 100,
                "budget_usage": 100,
            },
            "target": {
                "health_goal": "gain_muscle",
                "target_calories": 2000,
                "target_protein": 130,
                "target_carbs": 220,
                "target_fat": 60,
                "max_budget": 120,
                "disliked_foods": [],
                "preferred_tags": ["高蛋白"],
            },
            "score": 9.8,
        },
        "crew_trace": [],
    }

    response = MealChatSessionResponse.model_validate(payload)

    assert isinstance(response.meal_plan, MealPlanResponse)
