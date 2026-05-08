# tests/meal_chat_v2/test_conversation_crew.py
import pytest
from unittest.mock import patch, MagicMock

from intelligent_meal_planner.meal_chat.crews.conversation_crew import (
    ConversationCrew,
    create_nutritionist_agent,
    create_explainer_agent,
)
from intelligent_meal_planner.meal_chat.models.intent import IntentResult
from intelligent_meal_planner.meal_chat.models.conversation import ConversationResult


def create_mock_llm():
    """Create a mock LLM that satisfies CrewAI's Agent requirements."""
    mock_llm = MagicMock()
    mock_llm.model = "deepseek/deepseek-chat"
    return mock_llm


class TestConversationCrewAgents:
    @patch("intelligent_meal_planner.meal_chat.crews.conversation_crew.get_conversation_llm")
    def test_create_nutritionist_agent(self, mock_llm):
        mock_llm.return_value = create_mock_llm()
        agent = create_nutritionist_agent()
        assert agent.role == "营养师"
        assert "信息" in agent.goal

    @patch("intelligent_meal_planner.meal_chat.crews.conversation_crew.get_conversation_llm")
    def test_create_explainer_agent(self, mock_llm):
        mock_llm.return_value = create_mock_llm()
        agent = create_explainer_agent()
        assert agent.role == "方案解读员"


class TestConversationCrew:
    @pytest.fixture
    def mock_result(self):
        result = MagicMock()
        result.pydantic = ConversationResult(
            assistant_message="好的，我来帮你规划减脂方案。你身高体重大概多少？",
            suggested_phase="discovering",
            needs_clarification=True,
            clarification_questions=["身高", "体重"],
        )
        return result

    @patch("intelligent_meal_planner.meal_chat.crews.conversation_crew.Crew")
    @patch("intelligent_meal_planner.meal_chat.crews.conversation_crew.get_conversation_llm")
    def test_conversation_crew_run(
        self,
        mock_llm,
        mock_crew_class,
        mock_result,
    ):
        mock_llm.return_value = create_mock_llm()

        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew

        crew = ConversationCrew()
        intent = IntentResult(
            intent="request_plan",
            confidence=0.85,
            preference_updates={"health_goal": "lose_weight"},
        )

        result = crew.run(
            intent_result=intent,
            recent_messages=[],
            profile_summary="新用户",
            current_phase="discovering",
        )

        assert "身高" in result.assistant_message or "体重" in result.assistant_message
        assert result.needs_clarification is True

    @patch("intelligent_meal_planner.meal_chat.crews.conversation_crew.Crew")
    @patch("intelligent_meal_planner.meal_chat.crews.conversation_crew.get_conversation_llm")
    def test_explain_plan(self, mock_llm, mock_crew_class):
        mock_llm.return_value = create_mock_llm()

        mock_result = MagicMock()
        mock_result.raw = "这个方案的高蛋白配比能帮你保住肌肉..."
        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew

        crew = ConversationCrew()
        explanation = crew.explain_plan(
            meal_plan={"breakfast": "燕麦粥"},
            target_ranges={"calories_min": 1500, "calories_max": 1800},
            user_goal="lose_weight",
        )

        assert "蛋白" in explanation or "方案" in explanation

    @patch("intelligent_meal_planner.meal_chat.crews.conversation_crew.Crew")
    @patch("intelligent_meal_planner.meal_chat.crews.conversation_crew.get_conversation_llm")
    def test_conversation_crew_with_context(self, mock_llm, mock_crew_class):
        """测试带上下文的对话生成"""
        mock_llm.return_value = create_mock_llm()

        mock_result = MagicMock()
        mock_result.pydantic = ConversationResult(
            assistant_message="收到，175cm、72kg。你的活动量怎么样？",
            suggested_phase="discovering",
        )
        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew

        crew = ConversationCrew()
        intent = IntentResult(
            intent="provide_info",
            confidence=0.9,
            profile_updates={"height_cm": 175, "weight_kg": 72},
        )

        result = crew.run(
            intent_result=intent,
            recent_messages=[
                {"role": "assistant", "content": "你身高体重是多少？"},
            ],
            profile_summary="新用户，目标是减脂",
            current_phase="discovering",
        )

        assert "175" in result.assistant_message or "活动" in result.assistant_message

    @patch("intelligent_meal_planner.meal_chat.crews.conversation_crew.Crew")
    @patch("intelligent_meal_planner.meal_chat.crews.conversation_crew.get_conversation_llm")
    def test_conversation_crew_fallback(self, mock_llm, mock_crew_class):
        """测试默认回复回退"""
        mock_llm.return_value = create_mock_llm()

        mock_result = MagicMock()
        # 没有 pydantic 属性
        del mock_result.pydantic
        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew

        crew = ConversationCrew()
        intent = IntentResult(intent="chat", confidence=0.8)

        result = crew.run(
            intent_result=intent,
            recent_messages=[],
            profile_summary="新用户",
            current_phase="discovering",
        )

        assert result.assistant_message == "抱歉，我需要再确认一下你的需求。"
