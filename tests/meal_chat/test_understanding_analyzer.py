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


def test_analyzer_detects_contradiction_when_user_says_gain_muscle_but_eat_less():
    memory = ConversationMemory(
        preferences={"health_goal": "gain_muscle"},
        known_facts={"raw_user_message": "想增肌，但最好吃少一点"},
    )

    analysis = analyze_understanding(
        memory=memory,
        confidence=0.77,
        extracted_missing_fields=[],
        contradiction_fields=["health_goal"],
    )

    assert analysis.clarification_reason == "contradiction_detected"
    assert analysis.ready_for_negotiation is False


def test_analyzer_ignores_extracted_missing_fields_that_are_already_known():
    memory = ConversationMemory(
        profile={
            "gender": "male",
            "age": 25,
            "height": 170.0,
            "weight": 65.0,
            "activity_level": "moderate",
        },
        preferences={"health_goal": "lose_weight", "budget": 100.0},
    )

    analysis = analyze_understanding(
        memory=memory,
        confidence=0.9,
        extracted_missing_fields=[
            "gender",
            "age",
            "height",
            "weight",
            "activity_level",
            "health_goal",
            "budget",
        ],
    )

    assert analysis.missing_fields == []
    assert analysis.ready_for_negotiation is True
