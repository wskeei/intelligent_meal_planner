# tests/meal_chat_v2/test_state.py
import pytest

from intelligent_meal_planner.meal_chat.models import (
    IntentResult,
    ConversationResult,
    PlanningResult,
    MemoryUpdateResult,
)


class TestIntentResult:
    def test_create_with_defaults(self):
        result = IntentResult(
            intent="chat",
            confidence=0.8,
        )
        assert result.intent == "chat"
        assert result.confidence == 0.8
        assert result.profile_updates == {}
        assert result.ready_for_planning is False

    def test_create_with_updates(self):
        result = IntentResult(
            intent="provide_info",
            confidence=0.95,
            profile_updates={"height_cm": 175, "weight_kg": 72},
            preference_updates={"health_goal": "lose_weight"},
        )
        assert result.profile_updates["height_cm"] == 175
        assert result.preference_updates["health_goal"] == "lose_weight"

    def test_confidence_bounds(self):
        with pytest.raises(Exception):
            IntentResult(intent="chat", confidence=1.5)

        with pytest.raises(Exception):
            IntentResult(intent="chat", confidence=-0.1)


class TestConversationResult:
    def test_create_with_message(self):
        result = ConversationResult(
            assistant_message="好的，我来帮你规划减脂方案。",
            suggested_phase="discovering",
        )
        assert result.assistant_message == "好的，我来帮你规划减脂方案。"
        assert result.needs_clarification is False

    def test_create_with_clarification(self):
        result = ConversationResult(
            assistant_message="你的身高体重是多少？",
            needs_clarification=True,
            clarification_questions=["身高", "体重"],
        )
        assert result.needs_clarification is True
        assert len(result.clarification_questions) == 2


class TestPlanningResult:
    def test_create_with_meal_plan(self):
        result = PlanningResult(
            meal_plan={"breakfast_0": 1, "lunch_0": 2, "dinner_0": 3},
            total_calories=1800,
            total_cost=75.0,
            explanation="这是根据你的目标生成的方案。",
        )
        assert result.meal_plan["breakfast_0"] == 1
        assert result.total_calories == 1800


class TestMemoryUpdateResult:
    def test_no_update_needed(self):
        result = MemoryUpdateResult(should_update=False)
        assert result.should_update is False
        assert result.profile_updates == {}

    def test_update_with_preference(self):
        result = MemoryUpdateResult(
            should_update=True,
            update_reason="用户明确表达了不喜欢豆腐",
            taste_profile_updates={"avoid_ingredients": ["豆腐"]},
            confidence=0.9,
        )
        assert result.should_update is True
        assert "豆腐" in result.taste_profile_updates["avoid_ingredients"]
