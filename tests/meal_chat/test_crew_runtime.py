from intelligent_meal_planner.meal_chat.crew_runtime import CrewMealChatRuntime
from intelligent_meal_planner.meal_chat.session_schema import ConversationMemory


def test_runtime_routes_budget_question_to_negotiation_answer():
    runtime = CrewMealChatRuntime.__new__(CrewMealChatRuntime)
    runtime.intent_agent = lambda *_args, **_kwargs: {
        "intent": "budget_question",
        "needs_plan": False,
    }
    runtime.profile_agent = lambda *_args, **_kwargs: {
        "profile_updates": {},
        "preference_updates": {},
    }
    runtime.strategy_agent = lambda *_args, **_kwargs: {
        "target_ranges": None,
    }
    runtime.negotiator_agent = lambda *_args, **_kwargs: {
        "assistant_message": "按你现在的目标，最低建议预算大约 160 元。",
        "phase": "negotiating",
        "options": [],
    }

    result = runtime.run_turn(
        user_message="最低需要多少预算？",
        memory=ConversationMemory(phase="negotiating"),
    )

    assert result.phase == "negotiating"
    assert "最低建议预算" in result.assistant_message


def test_runtime_requests_plan_when_information_is_sufficient():
    runtime = CrewMealChatRuntime.__new__(CrewMealChatRuntime)
    runtime.intent_agent = lambda *_args, **_kwargs: {
        "intent": "plan_request",
        "needs_plan": True,
    }
    runtime.profile_agent = lambda *_args, **_kwargs: {
        "profile_updates": {},
        "preference_updates": {"budget": 200.0},
    }
    runtime.strategy_agent = lambda *_args, **_kwargs: {
        "target_ranges": {
            "calories_min": 1700,
            "calories_max": 1900,
            "protein_min": 100,
            "protein_max": 130,
            "carbs_min": 140,
            "carbs_max": 220,
            "fat_min": 40,
            "fat_max": 65,
            "strategy": "fat_loss",
        },
    }
    runtime.negotiator_agent = lambda *_args, **_kwargs: {
        "phase": "planning",
        "assistant_message": "可以正式配餐。",
        "options": [],
    }
    runtime.planning_agent = lambda *_args, **_kwargs: {
        "phase": "finalized",
        "assistant_message": "我给你整理了两套方案。",
        "meal_plan": {"primary": {}, "alternatives": [{}, {}]},
    }

    result = runtime.run_turn(
        user_message="那直接给我方案吧",
        memory=ConversationMemory(phase="discovering"),
    )

    assert result.phase == "finalized"
    assert result.meal_plan is not None
