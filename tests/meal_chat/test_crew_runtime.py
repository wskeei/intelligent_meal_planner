from intelligent_meal_planner.meal_chat.crew_runtime import CrewMealChatRuntime
from intelligent_meal_planner.meal_chat.session_schema import (
    ConversationMemory,
    NegotiationOption,
    TargetRanges,
)
from intelligent_meal_planner.meal_chat.types import ParsedTurn


class FakePlanningTool:
    def __init__(self):
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "id": f"plan{len(self.calls)}",
            "meals": [],
            "nutrition": {"total_price": kwargs["budget"]},
        }


class FakeExtractor:
    def __init__(self, parsed_turn=None, error=None):
        self.parsed_turn = parsed_turn
        self.error = error
        self.calls = []

    def parse(self, user_message, expected_slot=None):
        self.calls.append(
            {
                "user_message": user_message,
                "expected_slot": expected_slot,
            }
        )
        if self.error is not None:
            raise self.error
        return self.parsed_turn


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


def test_runtime_requests_two_rl_plan_variants_when_negotiation_prefers_dual_options():
    runtime = CrewMealChatRuntime(planning_tool=FakePlanningTool())
    memory = ConversationMemory(
        phase="planning",
        target_ranges=TargetRanges(
            calories_min=1700,
            calories_max=1900,
            protein_min=100,
            protein_max=130,
            carbs_min=140,
            carbs_max=220,
            fat_min=40,
            fat_max=65,
            strategy="fat_loss",
        ),
        preferences={"budget": 120.0},
        negotiation_options=[
            NegotiationOption(
                key="budget_cut",
                title="保守减脂",
                rationale="...",
                budget=120.0,
            ),
            NegotiationOption(
                key="protein_priority",
                title="高蛋白优先",
                rationale="...",
                budget=150.0,
            ),
        ],
    )

    result = runtime._build_dual_plan(memory)

    assert len(result["alternatives"]) == 2
    assert result["alternatives"][0]["option_key"] == "budget_cut"
    assert result["alternatives"][1]["option_key"] == "protein_priority"


def test_profile_agent_extracts_goal_and_budget_from_natural_language():
    runtime = CrewMealChatRuntime(planning_tool=None)
    result = runtime.profile_agent(
        user_message="我想减肥，预算200元以内",
        memory=ConversationMemory(
            phase="discovering",
            preferences={"health_goal": "healthy"},
        ),
        intent={"intent": "general_chat", "needs_plan": False},
    )

    assert result["preference_updates"]["health_goal"] == "lose_weight"
    assert result["preference_updates"]["budget"] == 200.0


def test_runtime_updates_memory_from_user_goal_and_budget_message():
    runtime = CrewMealChatRuntime(planning_tool=None)
    result = runtime.run_turn(
        user_message="我想减肥，预算200元以内",
        memory=ConversationMemory(
            phase="discovering",
            profile={
                "gender": "male",
                "age": 25,
                "height": 170.0,
                "weight": 65.0,
                "activity_level": "moderate",
            },
            preferences={"health_goal": "healthy"},
        ),
    )

    assert result.memory.preferences["health_goal"] == "lose_weight"
    assert result.memory.preferences["budget"] == 200.0
    assert result.phase == "planning"


def test_profile_agent_extracts_more_natural_budget_goal_and_preferences():
    runtime = CrewMealChatRuntime(planning_tool=None)
    result = runtime.profile_agent(
        user_message="我想瘦一点，控制在两百以内，不吃香菜，口味清淡",
        memory=ConversationMemory(
            phase="discovering",
            preferences={"health_goal": "healthy"},
        ),
        intent={"intent": "general_chat", "needs_plan": False},
    )

    assert result["preference_updates"]["health_goal"] == "lose_weight"
    assert result["preference_updates"]["budget"] == 200.0
    assert result["preference_updates"]["disliked_foods"] == ["香菜"]
    assert result["preference_updates"]["preferred_tags"] == ["清淡"]


def test_profile_agent_supports_chinese_numerals_and_muscle_gain_phrasing():
    runtime = CrewMealChatRuntime(planning_tool=None)
    result = runtime.profile_agent(
        user_message="最近想练壮一点，预算别超过一百五",
        memory=ConversationMemory(
            phase="discovering",
            preferences={"health_goal": "healthy"},
        ),
        intent={"intent": "general_chat", "needs_plan": False},
    )

    assert result["preference_updates"]["health_goal"] == "gain_muscle"
    assert result["preference_updates"]["budget"] == 150.0


def test_profile_agent_prefers_ai_extractor_for_freeform_user_message():
    extractor = FakeExtractor(
        parsed_turn=ParsedTurn(
            preference_updates={
                "health_goal": "lose_weight",
                "budget": 180.0,
                "disliked_foods": ["海鲜"],
                "preferred_tags": ["清淡", "高蛋白"],
            }
        )
    )
    runtime = CrewMealChatRuntime(planning_tool=None, extractor=extractor)

    result = runtime.profile_agent(
        user_message="最近应酬多，想把体脂往下压一点，花费别太夸张，海鲜别安排，做清爽点但蛋白要够。",
        memory=ConversationMemory(
            phase="discovering",
            preferences={"health_goal": "healthy"},
        ),
        intent={"intent": "general_chat", "needs_plan": False},
    )

    assert result["preference_updates"]["health_goal"] == "lose_weight"
    assert result["preference_updates"]["budget"] == 180.0
    assert result["preference_updates"]["disliked_foods"] == ["海鲜"]
    assert result["preference_updates"]["preferred_tags"] == ["清淡", "高蛋白"]
    assert extractor.calls[0]["expected_slot"] is None


def test_profile_agent_falls_back_to_heuristics_when_ai_extractor_fails():
    extractor = FakeExtractor(error=RuntimeError("llm unavailable"))
    runtime = CrewMealChatRuntime(planning_tool=None, extractor=extractor)

    result = runtime.profile_agent(
        user_message="我想瘦一点，控制在两百以内，不吃香菜，口味清淡",
        memory=ConversationMemory(
            phase="discovering",
            preferences={"health_goal": "healthy"},
        ),
        intent={"intent": "general_chat", "needs_plan": False},
    )

    assert result["preference_updates"]["health_goal"] == "lose_weight"
    assert result["preference_updates"]["budget"] == 200.0


def test_profile_agent_normalizes_ai_output_into_canonical_schema():
    extractor = FakeExtractor(
        parsed_turn=ParsedTurn(
            preference_updates={
                "health_goal": "练壮一点",
                "budget": "一百五十元以内",
                "disliked_foods": "香菜",
                "preferred_tags": "清淡",
            }
        )
    )
    runtime = CrewMealChatRuntime(planning_tool=None, extractor=extractor)

    result = runtime.profile_agent(
        user_message="随便你理解",
        memory=ConversationMemory(
            phase="discovering",
            preferences={"health_goal": "healthy"},
        ),
        intent={"intent": "general_chat", "needs_plan": False},
    )

    assert result["preference_updates"]["health_goal"] == "gain_muscle"
    assert result["preference_updates"]["budget"] == 150.0
    assert result["preference_updates"]["disliked_foods"] == ["香菜"]
    assert result["preference_updates"]["preferred_tags"] == ["清淡"]
