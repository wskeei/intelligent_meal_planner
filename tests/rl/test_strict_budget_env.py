from intelligent_meal_planner.rl.environment import MealPlanningEnv


def test_strict_budget_returns_empty_mask_when_no_affordable_action():
    env = MealPlanningEnv(
        budget_limit=1.0,
        training_mode=False,
        strict_budget=True,
    )

    env.reset()
    mask = env.action_masks()

    assert not mask.any()
