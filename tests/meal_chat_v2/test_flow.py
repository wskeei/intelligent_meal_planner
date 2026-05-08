# tests/meal_chat_v2/test_flow.py
import pytest
from unittest.mock import patch, MagicMock

from intelligent_meal_planner.meal_chat.flow import (
    MealChatFlow,
    create_meal_chat_flow,
)
from intelligent_meal_planner.meal_chat.state import ConversationState
from intelligent_meal_planner.meal_chat.models.intent import IntentResult
from intelligent_meal_planner.meal_chat.models.conversation import ConversationResult
from intelligent_meal_planner.meal_chat.models.planning import PlanningResult
from intelligent_meal_planner.meal_chat.models.memory import MemoryUpdateResult


class TestMealChatFlow:
    @pytest.fixture
    def mock_managers(self):
        profile_manager = MagicMock()
        profile_manager.get_profile.return_value = MagicMock()
        profile_manager.get_profile.return_value.get_summary_for_context.return_value = "测试用户"
        return profile_manager

    def test_flow_basic_conversation(self, mock_managers):
        """测试基本对话流程"""
        with patch("intelligent_meal_planner.meal_chat.flow.IntentCrew") as mock_intent, \
             patch("intelligent_meal_planner.meal_chat.flow.ConversationCrew") as mock_conv, \
             patch("intelligent_meal_planner.meal_chat.flow.MemoryUpdateCrew") as mock_memory:

            mock_intent_instance = MagicMock()
            mock_intent_instance.run.return_value = IntentResult(
                intent="provide_info",  # Not requesting plan
                confidence=0.85,
                preference_updates={"health_goal": "lose_weight"},
                ready_for_planning=False,
            )
            mock_intent.return_value = mock_intent_instance

            mock_conv_instance = MagicMock()
            mock_conv_instance.run.return_value = ConversationResult(
                assistant_message="好的，我来帮你规划。你的身高体重是多少？",
                suggested_phase="discovering",
                needs_clarification=True,
            )
            mock_conv.return_value = mock_conv_instance

            mock_memory_instance = MagicMock()
            mock_memory_instance.run.return_value = MemoryUpdateResult(should_update=False)
            mock_memory.return_value = mock_memory_instance

            # 创建流程
            flow = create_meal_chat_flow(
                user_id="test-user",
                session_id="test-session",
                profile_manager=mock_managers,
            )

            # Set user message
            flow.state.user_message = "我想减脂"

            # 执行
            flow.kickoff()

            # 验证状态更新
            assert flow.state.turn_count == 2  # user + assistant
            assert "lose_weight" in str(flow.state.collected_preferences.get("health_goal", ""))

    def test_flow_updates_state(self, mock_managers):
        """测试状态更新"""
        with patch("intelligent_meal_planner.meal_chat.flow.IntentCrew") as mock_intent, \
             patch("intelligent_meal_planner.meal_chat.flow.ConversationCrew") as mock_conv, \
             patch("intelligent_meal_planner.meal_chat.flow.MemoryUpdateCrew") as mock_memory:

            mock_intent_instance = MagicMock()
            mock_intent_instance.run.return_value = IntentResult(
                intent="provide_info",  # Not requesting plan
                confidence=0.85,
                preference_updates={"health_goal": "lose_weight"},
                ready_for_planning=False,
            )
            mock_intent.return_value = mock_intent_instance

            mock_conv_instance = MagicMock()
            mock_conv_instance.run.return_value = ConversationResult(
                assistant_message="好的，我来帮你规划。",
                suggested_phase="discovering",
            )
            mock_conv.return_value = mock_conv_instance

            mock_memory_instance = MagicMock()
            mock_memory_instance.run.return_value = MemoryUpdateResult(should_update=False)
            mock_memory.return_value = mock_memory_instance

            flow = create_meal_chat_flow(
                user_id="test-user",
                session_id="test-session",
                profile_manager=mock_managers,
            )
            flow.state.user_message = "我想减脂"

            flow.kickoff()

            assert flow.state.last_intent == "provide_info"
            assert flow.state.last_confidence == 0.85

    def test_flow_memory_update_triggered(self, mock_managers):
        """测试记忆更新触发"""
        with patch("intelligent_meal_planner.meal_chat.flow.IntentCrew") as mock_intent, \
             patch("intelligent_meal_planner.meal_chat.flow.ConversationCrew") as mock_conv, \
             patch("intelligent_meal_planner.meal_chat.flow.MemoryUpdateCrew") as mock_memory:

            mock_intent_instance = MagicMock()
            mock_intent_instance.run.return_value = IntentResult(intent="chat", confidence=0.8)
            mock_intent.return_value = mock_intent_instance

            mock_conv_instance = MagicMock()
            mock_conv_instance.run.return_value = ConversationResult(
                assistant_message="好的",
                suggested_phase="discovering",
            )
            mock_conv.return_value = mock_conv_instance

            mock_memory_instance = MagicMock()
            mock_memory_instance.run.return_value = MemoryUpdateResult(
                should_update=True,
                update_reason="Test",
            )
            mock_memory.return_value = mock_memory_instance

            flow = create_meal_chat_flow(
                user_id="test-user",
                session_id="test-session",
                profile_manager=mock_managers,
            )
            flow.state.user_message = "测试"
            flow.kickoff()

            mock_memory_instance.run.assert_called_once()


class TestMealChatFlowWithPlanning:
    @pytest.fixture
    def mock_managers(self):
        profile_manager = MagicMock()
        profile_manager.get_profile.return_value = MagicMock()
        profile_manager.get_profile.return_value.get_summary_for_context.return_value = "测试用户"
        return profile_manager

    def test_flow_transitions_to_planning_ready(self, mock_managers):
        """测试请求配餐时流程转换到 planning_ready（不自动生成方案）"""
        with patch("intelligent_meal_planner.meal_chat.flow.IntentCrew") as mock_intent, \
             patch("intelligent_meal_planner.meal_chat.flow.ConversationCrew") as mock_conv, \
             patch("intelligent_meal_planner.meal_chat.flow.MemoryUpdateCrew") as mock_memory:

            mock_intent_instance = MagicMock()
            mock_intent_instance.run.return_value = IntentResult(
                intent="request_plan",
                confidence=0.9,
                ready_for_planning=True,
            )
            mock_intent.return_value = mock_intent_instance

            mock_conv_instance = MagicMock()
            mock_conv_instance.run.return_value = ConversationResult(
                assistant_message="信息已齐全，点击生成配餐方案按钮开始。",
                suggested_phase="planning_ready",
                should_generate_plan=True,
            )
            mock_conv.return_value = mock_conv_instance

            mock_memory_instance = MagicMock()
            mock_memory_instance.run.return_value = MemoryUpdateResult(should_update=False)
            mock_memory.return_value = mock_memory_instance

            # 创建完整状态
            flow = create_meal_chat_flow(
                user_id="test-user",
                session_id="test-session",
                profile_manager=mock_managers,
            )

            flow.state.collected_profile = {
                "gender": "male",
                "age": 28,
                "height_cm": 175,
                "weight_kg": 72,
                "activity_level": "moderate",
            }
            flow.state.collected_preferences = {
                "health_goal": "lose_weight",
                "budget": 80,
            }
            flow.state.user_message = "帮我配个餐"

            # 执行
            flow.kickoff()

            # 验证：流程转换到 planning_ready（前端显示按钮）
            assert flow.state.current_phase == "planning_ready"
            # 不再自动生成方案（由 generate_session 端点触发）
            assert flow.state.current_meal_plan is None


class TestCreateMealChatFlow:
    def test_create_flow(self):
        flow = create_meal_chat_flow(
            user_id="test-user",
            session_id="test-session",
        )
        assert flow.state.user_id == "test-user"
        assert flow.state.session_id == "test-session"
        assert flow.state.current_phase == "discovering"

    def test_create_flow_with_profile_manager(self):
        mock_manager = MagicMock()
        flow = create_meal_chat_flow(
            user_id="test-user",
            session_id="test-session",
            profile_manager=mock_manager,
        )
        assert flow.profile_manager is mock_manager
