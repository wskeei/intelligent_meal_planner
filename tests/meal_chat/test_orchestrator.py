from types import SimpleNamespace

from intelligent_meal_planner.meal_chat.orchestrator import MealChatOrchestrator
from intelligent_meal_planner.meal_chat.session_schema import ConversationMemory
from intelligent_meal_planner.meal_chat.types import CrewTurnResult


class FakeCrewRuntime:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def run_turn(self, user_message, memory):
        self.calls.append(
            {
                "user_message": user_message,
                "memory": memory,
            }
        )
        return self.result


class FakePlanner:
    def generate(self, *_args, **_kwargs):
        return {}


def _user(**overrides):
    base = {
        "id": 1,
        "gender": "male",
        "age": 24,
        "height": 175,
        "weight": 68,
        "activity_level": "moderate",
        "health_goal": "healthy",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _session(**overrides):
    base = {
        "status": "discovering",
        "collected_slots": {},
        "hidden_targets": None,
        "final_plan": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_orchestrator_allows_budget_revision_after_negotiation():
    runtime = FakeCrewRuntime(
        result=CrewTurnResult(
            phase="planning",
            assistant_message="预算调到 200 元后，我可以继续给你两套方案。",
            memory=ConversationMemory(
                phase="planning",
                preferences={"budget": 200.0},
            ),
            meal_plan=None,
        )
    )
    orchestrator = MealChatOrchestrator(runtime=runtime, planner=FakePlanner())
    session = _session(
        status="negotiating",
        collected_slots={"budget": 100.0},
    )

    response = orchestrator.advance(_user(), session, "预算设置 200 元")

    assert response["status"] == "planning"
    assert "200 元" in response["assistant_message"]
    assert session.collected_slots["preferences"]["budget"] == 200.0
    assert runtime.calls[0]["memory"].phase == "discovering"


def test_orchestrator_returns_negotiation_trace_from_runtime():
    runtime = FakeCrewRuntime(
        result=CrewTurnResult(
            phase="negotiating",
            assistant_message="当前预算偏紧，我先给你两个方向。",
            memory=ConversationMemory(
                phase="negotiating",
                preferences={"budget": 100.0},
            ),
            negotiation_options=[],
        )
    )
    orchestrator = MealChatOrchestrator(runtime=runtime, planner=FakePlanner())

    response = orchestrator.advance(_user(), _session(), "预算 100 元")

    assert response["status"] == "negotiating"
    assert response["trace"]["phase"] == "negotiating"
    assert response["trace"]["memory"]["preferences"]["budget"] == 100.0
