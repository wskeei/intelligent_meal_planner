from intelligent_meal_planner.meal_chat.crew_factory import build_meal_planning_crew
from intelligent_meal_planner.meal_chat.crew_models import CrewPlanningResult


def test_build_meal_planning_crew_returns_named_crewai_agents():
    crew_bundle = build_meal_planning_crew(planning_tool=None)

    roles = [agent.role for agent in crew_bundle.agents]
    assert "需求审查专员" in roles
    assert "营养规划师" in roles
    assert "预算协调员" in roles
    assert "DQN 配餐师" in roles
    assert "结果解读员" in roles
    assert crew_bundle.tasks[-1].output_pydantic is CrewPlanningResult
