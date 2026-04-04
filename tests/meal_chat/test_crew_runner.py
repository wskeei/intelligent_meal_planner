from intelligent_meal_planner.meal_chat.crew_factory import build_meal_planning_crew
from intelligent_meal_planner.meal_chat.crew_runner import CrewMealPlannerRunner
from intelligent_meal_planner.meal_chat.session_schema import ConversationMemory, TargetRanges


def test_crew_runner_returns_visible_agent_events():
    class FakeCrew:
        def kickoff(self, inputs):
            del inputs
            return {
                "final_message": "方案完成",
                "meal_plan": {"id": "plan001"},
                "events": [
                    {"agent": "需求审查专员", "status": "completed", "message": "已确认用户需求"},
                    {"agent": "DQN 配餐师", "status": "completed", "message": "已调用 DQN 生成方案"},
                ],
            }

    runner = CrewMealPlannerRunner(lambda planning_tool: FakeCrew(), planning_tool=None)
    memory = ConversationMemory(
        phase="planning_ready",
        preferences={"budget": 120.0, "health_goal": "gain_muscle"},
    )

    result = runner.run(memory=memory, user=None)

    assert result["phase"] == "finalized"
    assert len(result["events"]) == 2
    assert result["events"][1]["agent"] == "DQN 配餐师"


def test_crew_runner_uses_real_task_transcript_and_tool_output():
    class FakePlanningTool:
        def __init__(self):
            self.calls = []

        def generate(self, **kwargs):
            self.calls.append(kwargs)
            return {
                "id": "plan001",
                "created_at": "2026-04-04T10:00:00",
                "meals": [],
                "nutrition": {
                    "total_calories": 1800,
                    "total_protein": 120,
                    "total_carbs": 180,
                    "total_fat": 55,
                    "total_price": kwargs["budget"],
                    "calories_achievement": 100,
                    "protein_achievement": 100,
                    "budget_usage": 100,
                },
                "target": {
                    "health_goal": kwargs["goal"],
                    "target_calories": kwargs["hidden_targets"]["target_calories"],
                    "target_protein": kwargs["hidden_targets"]["target_protein"],
                    "target_carbs": kwargs["hidden_targets"]["target_carbs"],
                    "target_fat": kwargs["hidden_targets"]["target_fat"],
                    "max_budget": kwargs["budget"],
                    "disliked_foods": kwargs["disliked_foods"],
                    "preferred_tags": kwargs["preferred_tags"],
                },
                "score": 9.5,
            }

    planner = FakePlanningTool()
    runner = CrewMealPlannerRunner(build_meal_planning_crew, planning_tool=planner)
    memory = ConversationMemory(
        phase="planning_ready",
        profile={
            "gender": "male",
            "age": 26,
            "height": 176,
            "weight": 72,
            "activity_level": "moderate",
        },
        preferences={"budget": 120.0, "health_goal": "gain_muscle", "preferred_tags": ["高蛋白"]},
        target_ranges=TargetRanges(
            calories_min=1900,
            calories_max=2100,
            protein_min=130,
            protein_max=150,
            carbs_min=180,
            carbs_max=240,
            fat_min=50,
            fat_max=70,
            strategy="muscle_gain",
        ),
    )

    result = runner.run(memory=memory, user=type("User", (), {"id": 7})())

    assert planner.calls
    assert result["meal_plan"]["id"] == "plan001"
    assert len(result["events"]) == 5
    dqn_event = next(event for event in result["events"] if event["agent"] == "DQN 配餐师")
    assert dqn_event["payload"]["meal_plan_id"] == "plan001"
    assert dqn_event["payload"]["tool_name"] == "dqn_meal_planning_tool"


def test_crew_runner_rejects_untyped_crew_outputs_instead_of_synthesizing_plan():
    class FakeCrew:
        def kickoff(self, inputs):
            del inputs
            return type("CrewOutput", (), {"raw": "not-json"})()

    runner = CrewMealPlannerRunner(lambda planning_tool: FakeCrew(), planning_tool=None)
    memory = ConversationMemory(
        phase="planning_ready",
        preferences={"budget": 120.0, "health_goal": "gain_muscle"},
    )

    try:
        runner.run(memory=memory, user=None)
    except RuntimeError as exc:
        assert "typed" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")
