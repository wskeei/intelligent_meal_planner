from intelligent_meal_planner.meal_chat.question_strategy import build_follow_up_plan
from intelligent_meal_planner.meal_chat.session_schema import ConversationMemory
from intelligent_meal_planner.meal_chat.understanding_schema import UnderstandingAnalysis


def test_build_follow_up_plan_returns_english_prompt_when_session_locale_is_english():
    memory = ConversationMemory(
        known_facts={"locale": "en"},
        preferences={"health_goal": "lose_weight", "budget": 100},
    )
    analysis = UnderstandingAnalysis(
        confidence=0.6,
        missing_fields=["budget", "health_goal"],
        contradiction_fields=[],
        clarification_reason=None,
        ready_for_negotiation=False,
    )

    follow_up = build_follow_up_plan(memory=memory, analysis=analysis)

    assert follow_up.questions == ["budget", "health_goal"]
    assert "I need two key details first" in follow_up.assistant_message
    assert "What daily budget do you want to stay within?" in follow_up.assistant_message
