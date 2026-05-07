# tests/meal_chat_v2/test_integration.py
"""
集成测试 - 验证完整对话流程

注意：这些测试需要 mock LLM 调用，否则会真正调用 DeepSeek API。
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

from intelligent_meal_planner.meal_chat import (
    create_meal_chat_flow,
    UserProfileManager,
    UserProfile,
)


class TestFullConversation:
    """完整对话流程集成测试"""

    @pytest.fixture
    def temp_profile_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def profile_manager(self, temp_profile_dir):
        return UserProfileManager(profiles_dir=temp_profile_dir)

    @patch("intelligent_meal_planner.meal_chat.flow.IntentCrew")
    @patch("intelligent_meal_planner.meal_chat.flow.ConversationCrew")
    @patch("intelligent_meal_planner.meal_chat.flow.MemoryUpdateCrew")
    def test_new_user_conversation(
        self,
        mock_memory_crew_class,
        mock_conv_crew_class,
        mock_intent_crew_class,
        profile_manager,
    ):
        """测试新用户完整对话流程"""
        from intelligent_meal_planner.meal_chat.models.intent import IntentResult

        # Mock IntentCrew
        mock_intent = MagicMock()
        mock_intent.run.return_value = IntentResult(
            intent="provide_info",
            confidence=0.85,
            preference_updates={"health_goal": "lose_weight"},
            ready_for_planning=False,
        )
        mock_intent_crew_class.return_value = mock_intent

        # Mock ConversationCrew
        from intelligent_meal_planner.meal_chat.models.conversation import ConversationResult

        mock_conv = MagicMock()
        mock_conv.run.return_value = ConversationResult(
            assistant_message="好的，我来帮你规划。你的身高体重是多少？",
            suggested_phase="discovering",
        )
        mock_conv_crew_class.return_value = mock_conv

        # Mock MemoryCrew
        from intelligent_meal_planner.meal_chat.models.memory import MemoryUpdateResult

        mock_memory = MagicMock()
        mock_memory.run.return_value = MemoryUpdateResult(should_update=False)
        mock_memory_crew_class.return_value = mock_memory

        # 创建流程
        flow = create_meal_chat_flow(
            user_id="new-user-001",
            session_id="session-001",
            profile_manager=profile_manager,
        )
        flow.state.user_message = "我想减脂，帮我配个餐"

        # 执行
        flow.kickoff()

        # 验证状态已更新
        assert flow.state.collected_preferences.get("health_goal") == "lose_weight"

        # 验证意图识别
        assert flow.state.last_intent == "provide_info"


class TestProfilePersistence:
    """用户认知文件持久化测试"""

    def test_profile_saved_after_conversation(self, tmp_path):
        """测试对话后用户认知文件被正确保存"""
        manager = UserProfileManager(profiles_dir=tmp_path)

        # 创建并更新
        manager.update_profile(
            user_id="test-user",
            profile_updates={"age": 28, "height_cm": 175},
            preference_updates={"health_goal": "lose_weight", "budget_daily": 80},
        )

        # 验证文件存在
        profile_path = tmp_path / "test-user.json"
        assert profile_path.exists()

        # 验证内容
        with open(profile_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["user_id"] == "test-user"
        assert data["profile"]["age"] == 28
        assert data["preferences"]["health_goal"] == "lose_weight"

    def test_profile_loaded_on_restart(self, tmp_path):
        """测试重启后能正确加载用户认知文件"""
        manager = UserProfileManager(profiles_dir=tmp_path)

        # 创建
        manager.update_profile(
            user_id="test-user",
            profile_updates={"age": 28},
        )

        # 清除缓存，模拟重启
        manager.clear_cache()

        # 重新加载
        profile = manager.get_profile("test-user")
        assert profile.profile["age"] == 28


class TestModuleImports:
    """验证所有公共接口可以正确导入"""

    def test_import_flow(self):
        from intelligent_meal_planner.meal_chat import MealChatFlow, create_meal_chat_flow
        assert MealChatFlow is not None
        assert create_meal_chat_flow is not None

    def test_import_state(self):
        from intelligent_meal_planner.meal_chat import ConversationState, MessageTurn
        assert ConversationState is not None
        assert MessageTurn is not None

    def test_import_models(self):
        from intelligent_meal_planner.meal_chat import (
            IntentResult,
            ConversationResult,
            PlanningResult,
            MemoryUpdateResult,
        )
        assert IntentResult is not None
        assert ConversationResult is not None
        assert PlanningResult is not None
        assert MemoryUpdateResult is not None

    def test_import_profile(self):
        from intelligent_meal_planner.meal_chat import (
            UserProfileManager,
            UserProfile,
            FeedbackRecord,
            GoalHistory,
        )
        assert UserProfileManager is not None
        assert UserProfile is not None
        assert FeedbackRecord is not None
        assert GoalHistory is not None
