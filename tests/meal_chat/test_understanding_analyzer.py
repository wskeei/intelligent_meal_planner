from intelligent_meal_planner.meal_chat.session_schema import ConversationMemory
from intelligent_meal_planner.meal_chat.understanding_analyzer import (
    analyze_understanding,
)


def test_analyze_understanding_requests_budget_when_goal_is_known_but_budget_missing():
    memory = ConversationMemory(
        phase="discovering",
        profile={
            "gender": "male",
            "age": 25,
            "height": 170.0,
            "weight": 65.0,
            "activity_level": "moderate",
        },
        preferences={"health_goal": "lose_weight"},
    )

    analysis = analyze_understanding(
        memory=memory,
        confidence=0.82,
        extracted_missing_fields=[],
    )

    assert analysis.missing_fields == ["budget"]
    assert analysis.ready_for_negotiation is False
    assert analysis.clarification_reason == "missing_required_fields"


def test_analyze_understanding_blocks_planning_when_confidence_is_low():
    memory = ConversationMemory(
        phase="discovering",
        profile={
            "gender": "male",
            "age": 25,
            "height": 170.0,
            "weight": 65.0,
            "activity_level": "moderate",
        },
        preferences={"health_goal": "lose_weight", "budget": 180.0},
    )

    analysis = analyze_understanding(
        memory=memory,
        confidence=0.32,
        extracted_missing_fields=[],
    )

    assert analysis.ready_for_negotiation is False
    assert analysis.clarification_reason == "low_confidence"
