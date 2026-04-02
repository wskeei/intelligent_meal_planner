from intelligent_meal_planner.tools import rl_model_tool


def test_resolve_model_path_prefers_dqn_when_ppo_is_missing(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    dqn_path = models_dir / "dqn_meal_best.pt"
    dqn_path.write_text("stub", encoding="utf-8")

    resolved = rl_model_tool.resolve_model_path(tmp_path)

    assert resolved == dqn_path


def test_rl_model_tool_runs_inference_with_dqn_backend(tmp_path, monkeypatch):
    model_path = tmp_path / "dqn_meal_best.pt"
    model_path.write_text("stub", encoding="utf-8")

    captured = {}

    class FakeAgent:
        action_dim = 150

        def select_action(self, state, action_mask, step, deterministic=False):
            captured["state"] = state
            captured["mask_len"] = len(action_mask)
            captured["step"] = step
            captured["deterministic"] = deterministic
            return 1

    class FakeEnv:
        def __init__(self, **kwargs):
            captured["env_kwargs"] = kwargs
            self.items_per_meal = 2
            self.total_calories = 1800
            self.total_protein = 120
            self.total_carbs = 200
            self.total_fat = 50
            self.total_cost = 88
            self.target_calories = kwargs["target_calories"]
            self.target_protein = kwargs["target_protein"]
            self.target_carbs = kwargs["target_carbs"]
            self.target_fat = kwargs["target_fat"]
            self.budget_limit = kwargs["budget_limit"]
            self._step = 0

        def reset(self):
            return [0.1] * 13, {}

        def action_masks(self):
            return [True] * 150 + [False] * 150

        def step(self, action):
            self._step += 1
            terminated = self._step >= 6
            return [0.1] * 13, 1.5, terminated, False, {"valid_action": True}

    monkeypatch.setattr(
        rl_model_tool,
        "MealPlanningEnv",
        FakeEnv,
    )
    monkeypatch.setattr(
        rl_model_tool.MaskableDQNAgent,
        "from_pretrained",
        classmethod(lambda cls, path, device=None: FakeAgent()),
    )

    tool = rl_model_tool.RLModelTool(model_path=str(model_path))
    result = tool._run(
        target_calories=1800,
        target_protein=120,
        target_carbs=200,
        target_fat=50,
        max_budget=100.0,
    )

    assert tool.backend == "dqn"
    assert '"status": "ok"' in result
    assert '"breakfast_0": 1' in result
    assert captured["mask_len"] == 150
    assert captured["deterministic"] is True
    assert captured["env_kwargs"]["training_mode"] is False
