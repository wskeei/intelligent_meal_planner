from intelligent_meal_planner.meal_chat.question_strategy import (
    build_follow_up_plan,
)
from intelligent_meal_planner.meal_chat.session_schema import ConversationMemory
from intelligent_meal_planner.meal_chat.understanding_schema import (
    UnderstandingAnalysis,
)


def test_build_follow_up_plan_asks_for_budget_with_nutritionist_tone():
    memory = ConversationMemory(
        preferences={"health_goal": "lose_weight"},
    )
    analysis = UnderstandingAnalysis(
        confidence=0.82,
        missing_fields=["budget"],
        contradiction_fields=[],
        clarification_reason="missing_required_fields",
        ready_for_negotiation=False,
    )

    follow_up = build_follow_up_plan(memory=memory, analysis=analysis)

    assert follow_up.questions == ["budget"]
    assert "预算" in follow_up.assistant_message
    assert "方案" in follow_up.assistant_message


def test_build_follow_up_plan_confirms_low_confidence_instead_of_assuming():
    memory = ConversationMemory(
        preferences={"health_goal": "lose_weight", "budget": 180.0},
    )
    analysis = UnderstandingAnalysis(
        confidence=0.35,
        missing_fields=[],
        contradiction_fields=[],
        clarification_reason="low_confidence",
        ready_for_negotiation=False,
    )

    follow_up = build_follow_up_plan(memory=memory, analysis=analysis)

    assert "我先确认一下" in follow_up.assistant_message
    assert "180" in follow_up.assistant_message


def test_build_follow_up_plan_handles_contradiction_with_targeted_clarification():
    memory = ConversationMemory(
        preferences={"health_goal": "gain_muscle"},
    )
    analysis = UnderstandingAnalysis(
        confidence=0.77,
        missing_fields=[],
        contradiction_fields=["health_goal"],
        clarification_reason="contradiction_detected",
        ready_for_negotiation=False,
    )

    follow_up = build_follow_up_plan(memory=memory, analysis=analysis)

    assert follow_up.questions == ["health_goal"]
    assert "矛盾" in follow_up.assistant_message
    assert "增肌" in follow_up.assistant_message
