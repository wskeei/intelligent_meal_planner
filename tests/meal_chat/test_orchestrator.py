from intelligent_meal_planner.meal_chat.orchestrator import MealChatOrchestrator
from intelligent_meal_planner.meal_chat.session_schema import ConversationMemory


class FakeIntake:
    def run_turn(self, user_message, memory):
        memory.phase = "planning_ready"
        memory.preferences["budget"] = 120.0
        return type(
            "Result",
            (),
            {
                "phase": "planning_ready",
                "assistant_message": "信息已齐，可以开始协作配餐。",
                "memory": memory,
                "ready_for_crew": True,
                "crew_payload": {"budget": 120.0},
            },
        )()


class FakeCrewRunner:
    def run(self, memory, user):
        del memory
        del user
        return {
            "phase": "finalized",
            "assistant_message": "完成",
            "meal_plan": None,
            "events": [
                {"agent": "需求审查专员", "status": "completed", "message": "已确认用户需求"}
            ],
        }


def test_orchestrator_stops_at_planning_ready_before_running_crew():
    class GuardCrewRunner:
        def run(self, memory, user):
            del memory
            del user
            raise AssertionError("crew runner should not execute during intake advance")

    orchestrator = MealChatOrchestrator(
        intake_runtime=FakeIntake(),
        crew_runner=GuardCrewRunner(),
    )
    session = type(
        "Session",
        (),
        {"status": "discovering", "collected_slots": {}, "final_plan": None},
    )()

    response = orchestrator.advance(user=None, session=session, user_message="预算120元，增肌")

    assert response["status"] == "planning_ready"
    assert response["meal_plan"] is None
    assert response["trace"]["phase"] == "planning_ready"
    assert session.status == "planning_ready"
    assert session.collected_slots["phase"] == "planning_ready"


def test_orchestrator_generate_runs_crew_once_session_is_ready():
    orchestrator = MealChatOrchestrator(
        intake_runtime=FakeIntake(),
        crew_runner=FakeCrewRunner(),
    )
    session = type(
        "Session",
        (),
        {"status": "discovering", "collected_slots": {}, "final_plan": None},
    )()
    user = type("User", (), {"id": 1})()

    advance_response = orchestrator.advance(user, session, "预算120元，增肌，高蛋白")
    response = orchestrator.generate(user, session)

    assert advance_response["status"] == "planning_ready"
    assert response["status"] == "finalized"
    assert response["trace"]["phase"] == "finalized"
    assert response["trace"]["crew_trace"][0]["agent"] == "需求审查专员"
    assert session.collected_slots["crew_events"][0]["agent"] == "需求审查专员"
