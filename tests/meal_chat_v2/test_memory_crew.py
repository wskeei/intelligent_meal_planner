# tests/meal_chat_v2/test_memory_crew.py
import pytest
from unittest.mock import patch, MagicMock

from intelligent_meal_planner.meal_chat.crews.memory_crew import (
    MemoryUpdateCrew,
    create_memory_evaluator_agent,
    create_archivist_agent,
)
from intelligent_meal_planner.meal_chat.models.intent import IntentResult
from intelligent_meal_planner.meal_chat.models.memory import MemoryUpdateResult


def create_mock_llm():
    """Create a mock LLM that satisfies CrewAI's Agent requirements."""
    mock_llm = MagicMock()
    mock_llm.model = "deepseek/deepseek-chat"
    return mock_llm


class TestMemoryUpdateCrewAgents:
    @patch("intelligent_meal_planner.meal_chat.crews.memory_crew.get_extraction_llm")
    def test_create_evaluator_agent(self, mock_llm):
        mock_llm.return_value = create_mock_llm()
        agent = create_memory_evaluator_agent()
        assert agent.role == "记忆评估员"

    @patch("intelligent_meal_planner.meal_chat.crews.memory_crew.get_extraction_llm")
    def test_create_archivist_agent(self, mock_llm):
        mock_llm.return_value = create_mock_llm()
        agent = create_archivist_agent()
        assert agent.role == "档案管理员"


class TestMemoryUpdateCrew:
    @pytest.fixture
    def mock_profile_manager(self):
        manager = MagicMock()
        manager.get_profile.return_value = MagicMock()
        manager.get_profile.return_value.get_summary_for_context.return_value = "测试用户画像"
        return manager

    @patch("intelligent_meal_planner.meal_chat.crews.memory_crew.Crew")
    @patch("intelligent_meal_planner.meal_chat.crews.memory_crew.get_extraction_llm")
    def test_memory_crew_should_update(
        self,
        mock_llm,
        mock_crew_class,
        mock_profile_manager,
    ):
        mock_llm.return_value = create_mock_llm()

        mock_result = MagicMock()
        mock_result.pydantic = MemoryUpdateResult(
            should_update=True,
            update_reason="用户明确表达不喜欢豆腐",
            taste_profile_updates={"avoid_ingredients": ["豆腐"]},
            confidence=0.9,
        )
        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew

        crew = MemoryUpdateCrew(profile_manager=mock_profile_manager)
        result = crew.run(
            user_id="test-user",
            user_message="我不喜欢吃豆腐，下次别给我配了",
            assistant_message="好的，记住了，以后避开豆腐。",
            intent_result=IntentResult(
                intent="provide_info",
                confidence=0.95,
                preference_updates={"disliked_foods": ["豆腐"]},
            ),
        )

        assert result.should_update is True
        assert "豆腐" in result.taste_profile_updates.get("avoid_ingredients", [])

    @patch("intelligent_meal_planner.meal_chat.crews.memory_crew.Crew")
    @patch("intelligent_meal_planner.meal_chat.crews.memory_crew.get_extraction_llm")
    def test_memory_crew_should_not_update(
        self,
        mock_llm,
        mock_crew_class,
        mock_profile_manager,
    ):
        mock_llm.return_value = create_mock_llm()

        mock_result = MagicMock()
        mock_result.pydantic = MemoryUpdateResult(should_update=False)
        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew

        crew = MemoryUpdateCrew(profile_manager=mock_profile_manager)
        result = crew.run(
            user_id="test-user",
            user_message="今天天气真好",
            assistant_message="是啊，天气不错。对了，你的身高体重是多少？",
            intent_result=IntentResult(intent="chat", confidence=0.8),
        )

        assert result.should_update is False

    @patch("intelligent_meal_planner.meal_chat.crews.memory_crew.Crew")
    @patch("intelligent_meal_planner.meal_chat.crews.memory_crew.get_extraction_llm")
    def test_memory_crew_with_feedback(
        self,
        mock_llm,
        mock_crew_class,
        mock_profile_manager,
    ):
        mock_llm.return_value = create_mock_llm()

        mock_result = MagicMock()
        mock_result.pydantic = MemoryUpdateResult(
            should_update=True,
            update_reason="用户对菜品给出明确反馈",
            feedback_to_add={
                "meal_plan_id": "plan-001",
                "liked_dishes": ["宫保鸡丁"],
                "disliked_dishes": ["麻婆豆腐"],
                "comment": "豆腐太辣了",
            },
            confidence=0.9,
        )
        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew

        crew = MemoryUpdateCrew(profile_manager=mock_profile_manager)
        result = crew.run(
            user_id="test-user",
            user_message="宫保鸡丁很好吃，但是麻婆豆腐太辣了",
            assistant_message="好的，记住了你的反馈。",
            intent_result=IntentResult(intent="provide_info", confidence=0.9),
        )

        assert result.should_update is True
        assert result.feedback_to_add is not None

    @patch("intelligent_meal_planner.meal_chat.crews.memory_crew.Crew")
    @patch("intelligent_meal_planner.meal_chat.crews.memory_crew.get_extraction_llm")
    def test_memory_crew_profile_correction(
        self,
        mock_llm,
        mock_crew_class,
        mock_profile_manager,
    ):
        mock_llm.return_value = create_mock_llm()

        mock_result = MagicMock()
        mock_result.pydantic = MemoryUpdateResult(
            should_update=True,
            update_reason="用户纠正了目标",
            preference_updates={"health_goal": "maintain"},
            confidence=0.95,
        )
        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew

        crew = MemoryUpdateCrew(profile_manager=mock_profile_manager)
        result = crew.run(
            user_id="test-user",
            user_message="其实我是要维持体重，不是减脂",
            assistant_message="好的，我来调整你的目标。",
            intent_result=IntentResult(
                intent="provide_info",
                confidence=0.9,
                preference_updates={"health_goal": "maintain"},
            ),
        )

        assert result.should_update is True
        assert result.preference_updates.get("health_goal") == "maintain"

    @patch("intelligent_meal_planner.meal_chat.crews.memory_crew.Crew")
    @patch("intelligent_meal_planner.meal_chat.crews.memory_crew.get_extraction_llm")
    def test_memory_crew_fallback_no_pydantic(
        self,
        mock_llm,
        mock_crew_class,
        mock_profile_manager,
    ):
        mock_llm.return_value = create_mock_llm()

        mock_result = MagicMock()
        del mock_result.pydantic  # No pydantic output
        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew

        crew = MemoryUpdateCrew(profile_manager=mock_profile_manager)
        result = crew.run(
            user_id="test-user",
            user_message="测试消息",
            assistant_message="测试回复",
            intent_result=IntentResult(intent="chat", confidence=0.5),
        )

        assert result.should_update is False
