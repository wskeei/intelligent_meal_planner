"""API service layer."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..db.models import MealChatMessage, MealChatSession, User
from ..meal_chat.crew_runtime import CrewMealChatRuntime
from ..meal_chat.local_trace import MealChatTraceWriter
from ..meal_chat.orchestrator import MealChatOrchestrator
from ..meal_chat.session_schema import ConversationMemory
from .feasibility import feasibility_service
from .schemas import (
    MealItem,
    MealPlanResponse,
    NutritionSummary,
    RecipeBase,
    RecipeFilter,
    UserPreferences,
)


class RecipeService:
    def __init__(self):
        data_path = Path(__file__).parent.parent / "data" / "recipes.json"
        with open(data_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        self.recipes = data.get("recipes", [])

    def get_all(self, filter: RecipeFilter) -> tuple[List[RecipeBase], int]:
        results = []
        for recipe in self.recipes:
            if filter.meal_type and filter.meal_type not in recipe.get("meal_type", []):
                continue
            if filter.min_price is not None and recipe["price"] < filter.min_price:
                continue
            if filter.max_price is not None and recipe["price"] > filter.max_price:
                continue
            if filter.category and recipe["category"] != filter.category:
                continue
            if filter.tags and not all(
                tag in recipe.get("tags", []) for tag in filter.tags
            ):
                continue
            results.append(RecipeBase(**recipe))

        total = len(results)
        return results[filter.offset : filter.offset + filter.limit], total

    def get_by_id(self, recipe_id: int) -> Optional[RecipeBase]:
        for recipe in self.recipes:
            if recipe["id"] == recipe_id:
                return RecipeBase(**recipe)
        return None

    def get_by_ids(self, ids: List[int]) -> List[RecipeBase]:
        return [
            recipe
            for recipe in (self.get_by_id(recipe_id) for recipe_id in ids)
            if recipe
        ]

    def get_categories(self) -> List[str]:
        return list(set(recipe["category"] for recipe in self.recipes))

    def get_tags(self) -> List[str]:
        tags = set()
        for recipe in self.recipes:
            tags.update(recipe.get("tags", []))
        return list(tags)


class MealPlanService:
    def __init__(self):
        self.recipe_service = RecipeService()
        self._history: Dict[str, MealPlanResponse] = {}

    def generate_plan(self, preferences: UserPreferences) -> MealPlanResponse:
        try:
            from ..tools.rl_model_tool import create_rl_model_tool

            tool = create_rl_model_tool()
            data = json.loads(
                tool._run(
                    target_calories=preferences.target_calories,
                    target_protein=preferences.target_protein,
                    target_carbs=preferences.target_carbs,
                    target_fat=preferences.target_fat,
                    max_budget=preferences.max_budget,
                    disliked_ingredients=preferences.disliked_foods,
                    preferred_tags=preferences.preferred_tags,
                    strict_budget=True,
                )
            )
            return self._build_response(data, preferences)
        except FileNotFoundError:
            return self._generate_random_plan(preferences)

    def _build_response(
        self, data: dict, preferences: UserPreferences
    ) -> MealPlanResponse:
        meal_plan = data.get("meal_plan", {})
        metrics = data.get("metrics", {})

        meals = []
        for key, recipe_id in meal_plan.items():
            meal_type = key.split("_")[0] if "_" in key else key
            recipe = self.recipe_service.get_by_id(recipe_id)
            if recipe:
                meals.append(
                    MealItem(
                        meal_type=meal_type,
                        recipe_id=recipe.id,
                        recipe_name=recipe.name,
                        calories=recipe.calories,
                        protein=recipe.protein,
                        carbs=recipe.carbs,
                        fat=recipe.fat,
                        price=recipe.price,
                    )
                )

        nutrition = NutritionSummary(
            total_calories=metrics.get("total_calories", 0),
            total_protein=metrics.get("total_protein", 0),
            total_carbs=metrics.get("total_carbs", 0),
            total_fat=metrics.get("total_fat", 0),
            total_price=metrics.get("total_cost", 0),
            calories_achievement=metrics.get("calories_achievement", 0),
            protein_achievement=metrics.get("protein_achievement", 0),
            budget_usage=metrics.get("budget_usage", 0),
        )

        plan_id = str(uuid.uuid4())[:8]
        response = MealPlanResponse(
            id=plan_id,
            created_at=datetime.now(),
            meals=meals,
            nutrition=nutrition,
            target=preferences,
            score=metrics.get("final_reward", 0),
        )
        self._history[plan_id] = response
        return response

    def _generate_random_plan(self, preferences: UserPreferences) -> MealPlanResponse:
        import random

        meals = []
        total_calories = total_protein = total_carbs = total_fat = total_price = 0.0

        for meal_type in ["breakfast", "lunch", "dinner"]:
            candidates = [
                recipe
                for recipe in self.recipe_service.recipes
                if meal_type in recipe.get("meal_type", [])
            ]
            if not candidates:
                continue
            recipe = random.choice(candidates)
            meals.append(
                MealItem(
                    meal_type=meal_type,
                    recipe_id=recipe["id"],
                    recipe_name=recipe["name"],
                    calories=recipe["calories"],
                    protein=recipe["protein"],
                    carbs=recipe["carbs"],
                    fat=recipe["fat"],
                    price=recipe["price"],
                )
            )
            total_calories += recipe["calories"]
            total_protein += recipe["protein"]
            total_carbs += recipe["carbs"]
            total_fat += recipe["fat"]
            total_price += recipe["price"]

        nutrition = NutritionSummary(
            total_calories=total_calories,
            total_protein=total_protein,
            total_carbs=total_carbs,
            total_fat=total_fat,
            total_price=total_price,
            calories_achievement=(total_calories / preferences.target_calories) * 100,
            protein_achievement=(total_protein / preferences.target_protein) * 100,
            budget_usage=(total_price / preferences.max_budget) * 100,
        )

        return MealPlanResponse(
            id=str(uuid.uuid4())[:8],
            created_at=datetime.now(),
            meals=meals,
            nutrition=nutrition,
            target=preferences,
            score=0,
        )

    def get_history(self, limit: int = 10) -> List[MealPlanResponse]:
        items = list(self._history.values())
        return sorted(items, key=lambda item: item.created_at, reverse=True)[:limit]

    def get_by_id(self, plan_id: str) -> Optional[MealPlanResponse]:
        return self._history.get(plan_id)


class BudgetGuardService:
    def check(self, budget, target_calories, target_protein, target_carbs, target_fat):
        result = feasibility_service.check_feasibility(
            budget=budget,
            target_calories=target_calories,
            target_protein=target_protein,
            target_carbs=target_carbs,
            target_fat=target_fat,
        )
        return (
            result.calories_feasibility >= 100
            and result.protein_feasibility >= 100
            and result.carbs_feasibility >= 100
            and result.fat_feasibility >= 100
        )


class StrictBudgetPlanner:
    def generate(self, goal, budget, disliked_foods, preferred_tags, hidden_targets):
        from ..tools.rl_model_tool import create_rl_model_tool

        tool = create_rl_model_tool()
        payload = json.loads(
            tool._run(
                target_calories=hidden_targets["target_calories"],
                target_protein=hidden_targets["target_protein"],
                target_carbs=hidden_targets["target_carbs"],
                target_fat=hidden_targets["target_fat"],
                max_budget=budget,
                disliked_ingredients=disliked_foods,
                preferred_tags=preferred_tags,
                strict_budget=True,
            )
        )
        if payload["status"] != "ok":
            raise ValueError("budget_infeasible")

        preferences = UserPreferences(
            health_goal=goal,
            target_calories=hidden_targets["target_calories"],
            target_protein=hidden_targets["target_protein"],
            target_carbs=hidden_targets["target_carbs"],
            target_fat=hidden_targets["target_fat"],
            max_budget=budget,
            disliked_foods=disliked_foods,
            preferred_tags=preferred_tags,
        )
        response = meal_plan_service._build_response(payload, preferences)
        if response.nutrition.total_price > budget:
            raise ValueError("budget_infeasible")
        return response.model_dump(mode="json")


class MealChatApplication:
    def __init__(self):
        self._orchestrator: Optional[MealChatOrchestrator] = None
        self.trace_writer = MealChatTraceWriter()

    @property
    def orchestrator(self) -> MealChatOrchestrator:
        if self._orchestrator is None:
            planner = StrictBudgetPlanner()
            runtime = CrewMealChatRuntime(planning_tool=planner)
            self._orchestrator = MealChatOrchestrator(runtime=runtime, planner=planner)
        return self._orchestrator

    def _serialize_session(
        self, db: Session, session: MealChatSession
    ) -> Dict[str, Any]:
        messages = (
            db.query(MealChatMessage)
            .filter(MealChatMessage.session_id == session.id)
            .order_by(MealChatMessage.created_at.asc())
            .all()
        )
        return {
            "session_id": session.id,
            "status": session.status,
            "messages": [
                {
                    "role": message.role,
                    "content": message.content,
                    "created_at": message.created_at,
                }
                for message in messages
            ],
            "meal_plan": session.final_plan,
        }

    def start_session(self, db: Session, user: User) -> Dict[str, Any]:
        memory = ConversationMemory(
            phase="discovering",
            profile={
                "gender": user.gender,
                "age": user.age,
                "height": user.height,
                "weight": user.weight,
                "activity_level": user.activity_level,
            },
            preferences={"health_goal": user.health_goal},
        )
        session = MealChatSession(
            id=str(uuid.uuid4())[:8],
            user_id=user.id,
            status="discovering",
            collected_slots=memory.model_dump(mode="json"),
        )
        db.add(session)
        db.add(
            MealChatMessage(
                session_id=session.id,
                role="assistant",
                content="我会先了解你的目标、预算和口味偏好，再帮你整理一份预算内的一日三餐方案。",
                stage="discovering",
            )
        )
        db.commit()
        self.trace_writer.write(
            session_id=session.id,
            event="session_started",
            payload={
                "user_id": user.id,
                "status": session.status,
            },
        )
        db.refresh(session)
        return self._serialize_session(db, session)

    def get_session(
        self, db: Session, user: User, session_id: str
    ) -> Optional[Dict[str, Any]]:
        session = (
            db.query(MealChatSession)
            .filter(
                MealChatSession.id == session_id, MealChatSession.user_id == user.id
            )
            .first()
        )
        if not session:
            return None
        return self._serialize_session(db, session)

    def handle_message(
        self, db: Session, user: User, session_id: str, content: str
    ) -> Dict[str, Any]:
        session = (
            db.query(MealChatSession)
            .filter(
                MealChatSession.id == session_id, MealChatSession.user_id == user.id
            )
            .first()
        )
        if session is None:
            raise ValueError("session_not_found")

        stage_before = session.status

        try:
            db.add(
                MealChatMessage(
                    session_id=session.id,
                    role="user",
                    content=content,
                    stage=stage_before,
                )
            )
            result = self.orchestrator.advance(user, session, content)
            session.status = result["status"]
            if result["meal_plan"] is not None:
                session.final_plan = result["meal_plan"]

            db.add(user)
            db.add(session)
            db.add(
                MealChatMessage(
                    session_id=session.id,
                    role="assistant",
                    content=result["assistant_message"],
                    stage=session.status,
                )
            )
            db.commit()
            self.trace_writer.write(
                session_id=session.id,
                event="turn_processed",
                payload={
                    "user_id": user.id,
                    "status": result["status"],
                    "stage_before": stage_before,
                    "user_message": content,
                    "assistant_message": result["assistant_message"],
                    "trace": result.get("trace", {}),
                },
            )
            db.refresh(session)
            return self._serialize_session(db, session)
        except Exception as exc:
            db.rollback()
            self.trace_writer.write(
                session_id=session.id,
                event="turn_failed",
                payload={
                    "user_id": user.id,
                    "stage_before": stage_before,
                    "user_message": content,
                    "error": repr(exc),
                },
            )
            raise

    def get_completed_plans(
        self, db: Session, user_id: int, limit: int
    ) -> List[Dict[str, Any]]:
        rows = (
            db.query(MealChatSession)
            .filter(
                MealChatSession.user_id == user_id,
                MealChatSession.status.in_(["completed", "finalized"]),
            )
            .order_by(MealChatSession.updated_at.desc())
            .limit(limit)
            .all()
        )
        return [row.final_plan for row in rows if row.final_plan]


recipe_service = RecipeService()
meal_plan_service = MealPlanService()
meal_chat_app = MealChatApplication()
