from types import SimpleNamespace

from intelligent_meal_planner.meal_chat.orchestrator import MealChatOrchestrator
from intelligent_meal_planner.meal_chat.types import ParsedTurn


class FakeExtractor:
    def __init__(self, parsed_turn):
        self.parsed_turn = parsed_turn

    def parse(self, *_args, **_kwargs):
        return self.parsed_turn


class RecordingExtractor:
    def __init__(self, parsed_turn):
        self.parsed_turn = parsed_turn
        self.calls = []

    def parse(self, user_message, expected_slot=None):
        self.calls.append(
            {
                "user_message": user_message,
                "expected_slot": expected_slot,
            }
        )
        return self.parsed_turn


class FakeBudgetGuard:
    def __init__(self, feasible=True):
        self.feasible = feasible

    def check(self, *_args, **_kwargs):
        return self.feasible


class FakePlanner:
    def generate(self, *_args, **_kwargs):
        return {
            "id": "plan001",
            "created_at": "2026-04-01T10:00:00",
            "meals": [],
            "nutrition": {
                "total_calories": 1800,
                "total_protein": 120,
                "total_carbs": 180,
                "total_fat": 55,
                "total_price": 58,
                "calories_achievement": 100,
                "protein_achievement": 100,
                "budget_usage": 96.7,
            },
            "target": {
                "health_goal": "lose_weight",
                "target_calories": 1800,
                "target_protein": 120,
                "target_carbs": 180,
                "target_fat": 55,
                "max_budget": 60,
                "disliked_foods": [],
                "preferred_tags": [],
            },
            "score": 12.5,
        }


def _user(**overrides):
    base = {
        "id": 1,
        "gender": None,
        "age": None,
        "height": None,
        "weight": None,
        "activity_level": None,
        "health_goal": "healthy",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _session(**overrides):
    base = {
        "status": "collecting_profile",
        "collected_slots": {},
        "hidden_targets": None,
        "final_plan": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_orchestrator_asks_for_missing_profile_before_anything_else():
    orchestrator = MealChatOrchestrator(
        extractor=FakeExtractor(
            ParsedTurn(
                profile_updates={},
                preference_updates={},
                acknowledged_restrictions=False,
            )
        ),
        budget_guard=FakeBudgetGuard(True),
        planner=FakePlanner(),
    )

    response = orchestrator.advance(_user(), _session(), "你好")

    assert response["status"] == "collecting_profile"
    assert "性别" in response["assistant_message"]


def test_orchestrator_rejects_budget_when_guard_fails():
    parsed = ParsedTurn(
        profile_updates={},
        preference_updates={
            "budget": 30,
            "health_goal": "lose_weight",
            "disliked_foods": ["棣欒彍"],
            "preferred_tags": ["娓呮贰"],
            "restrictions_answered": True,
        },
        acknowledged_restrictions=True,
    )
    orchestrator = MealChatOrchestrator(
        extractor=FakeExtractor(parsed),
        budget_guard=FakeBudgetGuard(False),
        planner=FakePlanner(),
    )
    user = _user(
        gender="male", age=24, height=175, weight=68, activity_level="moderate"
    )

    response = orchestrator.advance(
        user,
        _session(status="collecting_preferences"),
        "预算 30 元，清淡一点，不吃香菜",
    )

    assert response["status"] == "budget_rejected"
    assert "预算过低" in response["assistant_message"]


def test_orchestrator_passes_expected_slot_before_parsing_reply():
    extractor = RecordingExtractor(
        ParsedTurn(
            profile_updates={},
            preference_updates={},
            acknowledged_restrictions=False,
        )
    )
    orchestrator = MealChatOrchestrator(
        extractor=extractor,
        budget_guard=FakeBudgetGuard(True),
        planner=FakePlanner(),
    )
    user = _user(
        gender="male",
        age=24,
        height=175,
        weight=68,
        activity_level="moderate",
        health_goal="lose_weight",
    )
    session = _session(
        status="collecting_preferences",
        collected_slots={"health_goal": "lose_weight", "budget": 100},
    )

    orchestrator.advance(user, session, "没有，都能吃")

    assert extractor.calls == [
        {
            "user_message": "没有，都能吃",
            "expected_slot": "restrictions",
        }
    ]


def test_orchestrator_advances_after_budget_answer_even_if_extractor_misclassifies_budget():
    parsed = ParsedTurn(
        profile_updates={"budget": "100元"},
        preference_updates={},
        acknowledged_restrictions=False,
    )
    orchestrator = MealChatOrchestrator(
        extractor=FakeExtractor(parsed),
        budget_guard=FakeBudgetGuard(True),
        planner=FakePlanner(),
    )
    user = _user(
        gender="male",
        age=24,
        height=175,
        weight=68,
        activity_level="moderate",
        health_goal="lose_weight",
    )
    session = _session(status="collecting_preferences")

    response = orchestrator.advance(user, session, "100元吧")

    assert (
        response["assistant_message"]
        == "你有没有忌口、过敏或者明确不吃的食物？如果没有也可以直接告诉我。"
    )
    assert session.collected_slots["budget"] == "100元"
