# tests/meal_chat_v2/test_state.py
import pytest

from intelligent_meal_planner.meal_chat.models import (
    IntentResult,
    ConversationResult,
    PlanningResult,
    MemoryUpdateResult,
)
from intelligent_meal_planner.meal_chat.state import (
    MessageTurn,
    ConversationState,
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


class TestMessageTurn:
    def test_create_message_turn(self):
        msg = MessageTurn(role="user", content="我想减脂")
        assert msg.role == "user"
        assert msg.content == "我想减脂"
        assert msg.timestamp is not None


class TestConversationState:
    def test_create_state(self):
        state = ConversationState(
            session_id="test-session",
            user_id="test-user",
        )
        assert state.session_id == "test-session"
        assert state.current_phase == "discovering"
        assert len(state.recent_messages) == 0

    def test_add_message(self):
        state = ConversationState(
            session_id="test-session",
            user_id="test-user",
        )
        state.add_message("user", "我想减脂")
        state.add_message("assistant", "好的，我来帮你规划")

        assert len(state.recent_messages) == 2
        assert state.turn_count == 2

    def test_message_truncation(self):
        state = ConversationState(
            session_id="test-session",
            user_id="test-user",
        )
        # 添加 25 条消息
        for i in range(25):
            state.add_message("user", f"消息 {i}")
            state.add_message("assistant", f"回复 {i}")

        # 应该只保留最近 20 条
        assert len(state.recent_messages) == 20

    def test_get_context_for_llm(self):
        state = ConversationState(
            session_id="test-session",
            user_id="test-user",
        )
        state.add_message("user", "消息1")
        state.add_message("assistant", "回复1")
        state.add_message("user", "消息2")
        state.add_message("assistant", "回复2")

        context = state.get_context_for_llm(max_turns=1)
        # 只取最近 1 轮（2 条消息）
        assert len(context) == 2
        assert context[0]["content"] == "消息2"

    def test_profile_complete(self):
        state = ConversationState(
            session_id="test-session",
            user_id="test-user",
            collected_profile={
                "gender": "male",
                "age": 28,
                "height": 175,
                "weight": 72,
                "activity_level": "moderate",
            },
        )
        assert state.is_profile_complete() is True

    def test_profile_incomplete(self):
        state = ConversationState(
            session_id="test-session",
            user_id="test-user",
            collected_profile={"gender": "male"},
        )
        assert state.is_profile_complete() is False

    def test_preferences_complete(self):
        state = ConversationState(
            session_id="test-session",
            user_id="test-user",
            collected_preferences={
                "health_goal": "lose_weight",
                "budget": 80,
            },
        )
        assert state.is_preferences_complete() is True

    def test_ready_for_planning(self):
        state = ConversationState(
            session_id="test-session",
            user_id="test-user",
            collected_profile={
                "gender": "male",
                "age": 28,
                "height": 175,
                "weight": 72,
                "activity_level": "moderate",
            },
            collected_preferences={
                "health_goal": "lose_weight",
                "budget": 80,
            },
        )
        assert state.is_ready_for_planning() is True

    def test_merge_updates(self):
        state = ConversationState(
            session_id="test-session",
            user_id="test-user",
        )
        state.merge_updates(
            profile_updates={"height": 175, "weight": 72},
            preference_updates={"health_goal": "lose_weight"},
        )
        assert state.collected_profile["height"] == 175
        assert state.collected_preferences["health_goal"] == "lose_weight"
