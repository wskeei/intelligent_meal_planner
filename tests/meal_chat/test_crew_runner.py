from intelligent_meal_planner.meal_chat.crew_runner import CrewMealPlannerRunner
from intelligent_meal_planner.meal_chat.session_schema import ConversationMemory


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
