"""RL-backed meal planning tool."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sb3_contrib import MaskablePPO

from ..rl.environment import MealPlanningEnv


class RLModelTool:
    """Load the trained PPO model and produce a meal plan JSON payload."""

    def __init__(self, model_path: Optional[str] = None):
        self.name = "强化学习配餐模型"
        self.description = (
            "使用训练好的 MaskablePPO 模型生成一日三餐方案，"
            "输入营养目标、预算和饮食限制，返回结构化结果。"
        )

        if model_path is None:
            project_root = Path(__file__).parent.parent.parent.parent
            model_path = project_root / "models" / "best_model.zip"

        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"模型文件不存在: {self.model_path}")

        self.model: Optional[MaskablePPO] = None
        self.env: Optional[MealPlanningEnv] = None

    def _load_model(self) -> None:
        if self.model is None:
            self.model = MaskablePPO.load(self.model_path)

    def _run(
        self,
        target_calories: int = 2000,
        target_protein: int = 100,
        target_carbs: int = 250,
        target_fat: int = 60,
        max_budget: float = 50.0,
        disliked_ingredients: Optional[List[str]] = None,
        preferred_tags: Optional[List[str]] = None,
        strict_budget: bool = True,
    ) -> str:
        self._load_model()

        self.env = MealPlanningEnv(
            target_calories=target_calories,
            target_protein=target_protein,
            target_carbs=target_carbs,
            target_fat=target_fat,
            budget_limit=max_budget,
            disliked_tags=disliked_ingredients or [],
            training_mode=False,
            strict_budget=strict_budget,
        )

        meal_plan, metrics, status = self._generate_meal_plan()

        result = {
            "status": status,
            "meal_plan": meal_plan,
            "metrics": metrics,
            "target": {
                "calories": target_calories,
                "protein": target_protein,
                "carbs": target_carbs,
                "fat": target_fat,
                "budget": max_budget,
                "preferred_tags": preferred_tags or [],
            },
        }
        return json.dumps(result, ensure_ascii=False, indent=2)

    def _generate_meal_plan(self) -> Tuple[Dict[str, int], Dict[str, Any], str]:
        if self.env is None or self.model is None:
            raise RuntimeError("Model tool is not initialized")

        obs, _info = self.env.reset()
        meal_plan: Dict[str, int] = {}
        meal_names = ["breakfast", "lunch", "dinner"]
        done = False
        reward = 0.0
        current_steps = 0
        max_steps_safety = 20

        while not done and current_steps < max_steps_safety:
            current_steps += 1

            action_masks = self.env.action_masks()
            if not action_masks.any():
                return {}, self._build_metrics(final_reward=reward), "budget_infeasible"

            action, _states = self.model.predict(
                obs,
                action_masks=action_masks,
                deterministic=True,
            )

            obs, reward, terminated, truncated, info = self.env.step(action)
            done = terminated or truncated

            if info.get("valid_action", False):
                step_idx_zero_based = current_steps - 1
                meal_idx = step_idx_zero_based // self.env.items_per_meal
                if meal_idx < len(meal_names):
                    key = f"{meal_names[meal_idx]}_{step_idx_zero_based % self.env.items_per_meal}"
                    meal_plan[key] = int(action)

        return meal_plan, self._build_metrics(final_reward=reward), "ok"

    def _build_metrics(self, final_reward: float) -> Dict[str, Any]:
        if self.env is None:
            raise RuntimeError("Environment is not initialized")

        return {
            "total_calories": self.env.total_calories,
            "total_protein": self.env.total_protein,
            "total_carbs": self.env.total_carbs,
            "total_fat": self.env.total_fat,
            "total_cost": self.env.total_cost,
            "final_reward": final_reward,
            "calories_achievement": (self.env.total_calories / self.env.target_calories) * 100,
            "protein_achievement": (self.env.total_protein / self.env.target_protein) * 100,
            "budget_usage": (self.env.total_cost / self.env.budget_limit) * 100,
        }

    def generate_multiple_plans(self, num_plans: int = 3, **kwargs) -> List[Dict[str, Any]]:
        plans = []
        for _ in range(num_plans):
            result = json.loads(self._run(**kwargs))
            plans.append(result)
        return plans


def create_rl_model_tool(model_path: Optional[str] = None) -> RLModelTool:
    return RLModelTool(model_path=model_path)
