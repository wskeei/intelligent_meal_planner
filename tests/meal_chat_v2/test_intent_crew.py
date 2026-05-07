# tests/meal_chat_v2/test_intent_crew.py
import pytest
from unittest.mock import patch, MagicMock

from intelligent_meal_planner.meal_chat.crews.intent_crew import (
    IntentCrew,
    create_intent_analyst_agent,
    create_info_extractor_agent,
)
from intelligent_meal_planner.meal_chat.models.intent import IntentResult


def create_mock_llm():
    """Create a mock LLM with required CrewAI attributes."""
    mock = MagicMock()
    mock.model = "deepseek/deepseek-chat"
    return mock


class TestIntentCrewAgents:
    @patch("intelligent_meal_planner.meal_chat.crews.intent_crew.get_extraction_llm")
    def test_create_analyst_agent(self, mock_llm):
        mock_llm.return_value = create_mock_llm()
        agent = create_intent_analyst_agent()
        assert agent.role == "对话分析师"
        assert "分析" in agent.goal

    @patch("intelligent_meal_planner.meal_chat.crews.intent_crew.get_extraction_llm")
    def test_create_extractor_agent(self, mock_llm):
        mock_llm.return_value = create_mock_llm()
        agent = create_info_extractor_agent()
        assert agent.role == "信息提取员"
        assert "提取" in agent.goal


class TestIntentCrew:
    @pytest.fixture
    def mock_crew_result(self):
        """模拟 Crew 执行结果"""
        result = MagicMock()
        result.pydantic = IntentResult(
            intent="request_plan",
            confidence=0.85,
            context_summary="用户想要减脂方案",
            preference_updates={"health_goal": "lose_weight"},
            ready_for_planning=False,
        )
        return result

    @patch("intelligent_meal_planner.meal_chat.crews.intent_crew.Crew")
    @patch("intelligent_meal_planner.meal_chat.crews.intent_crew.get_extraction_llm")
    def test_intent_crew_run(
        self,
        mock_llm,
        mock_crew_class,
        mock_crew_result,
    ):
        """测试 IntentCrew 执行"""
        mock_llm.return_value = create_mock_llm()

        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = mock_crew_result
        mock_crew_class.return_value = mock_crew

        crew = IntentCrew()
        result = crew.run(
            user_message="我想减脂，帮我配个餐",
            recent_messages=[],
            profile_summary="新用户",
        )

        assert result.intent == "request_plan"
        assert result.confidence == 0.85
        assert result.preference_updates["health_goal"] == "lose_weight"

    @patch("intelligent_meal_planner.meal_chat.crews.intent_crew.Crew")
    @patch("intelligent_meal_planner.meal_chat.crews.intent_crew.get_extraction_llm")
    def test_intent_crew_with_context(
        self,
        mock_llm,
        mock_crew_class,
    ):
        """测试带上下文的意图理解"""
        mock_llm.return_value = create_mock_llm()

        result = MagicMock()
        result.pydantic = IntentResult(
            intent="provide_info",
            confidence=0.9,
            profile_updates={"height_cm": 175, "weight_kg": 72},
        )
        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = result
        mock_crew_class.return_value = mock_crew

        crew = IntentCrew()
        intent_result = crew.run(
            user_message="我175，72公斤",
            recent_messages=[
                {"role": "assistant", "content": "你的身高体重是多少？"},
            ],
            profile_summary="新用户，目标是减脂",
            expected_slot="height_weight",
        )

        assert intent_result.intent == "provide_info"
        assert intent_result.profile_updates.get("height_cm") == 175
