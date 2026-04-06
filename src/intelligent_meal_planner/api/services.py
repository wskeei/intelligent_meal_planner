"""API service layer."""

import copy
import json
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload

from ..db import models
from ..db.models import MealChatMessage, MealChatSession, User
from ..meal_chat.crew_factory import build_meal_planning_crew
from ..meal_chat.copy import normalize_locale, session_intro
from ..meal_chat.crew_runner import CrewMealPlannerRunner
from ..meal_chat.deepseek_extractor import DeepSeekSlotExtractor
from ..meal_chat.intake_runtime import IntakeRuntime
from ..meal_chat.local_trace import MealChatTraceWriter
from ..meal_chat.orchestrator import MealChatOrchestrator
from ..meal_chat.semantic_normalizer import normalize_goal
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
            source_session_id=None,
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
            intake_runtime = IntakeRuntime(
                extractor=DeepSeekSlotExtractor(),
            )
            crew_runner = CrewMealPlannerRunner(build_meal_planning_crew, planner)
            self._orchestrator = MealChatOrchestrator(
                intake_runtime=intake_runtime,
                crew_runner=crew_runner,
            )
        return self._orchestrator

    def _serialize_session(
        self, db: Session, session: MealChatSession
    ) -> Dict[str, Any]:
        memory = ConversationMemory.model_validate(session.collected_slots or {})
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
            "crew_trace": memory.crew_events,
            "open_questions": memory.open_questions,
            "known_facts": memory.known_facts,
            "follow_up_plan": (
                memory.follow_up_plan.model_dump(mode="json")
                if memory.follow_up_plan is not None
                else None
            ),
            "presentation": {
                "phase": memory.phase,
                "overlay_state": memory.overlay_state,
                "can_generate": session.status == "planning_ready",
                "has_result_overlay": memory.overlay_state == "result",
            },
            "profile_snapshot": memory.profile,
            "preferences_snapshot": memory.preferences,
            "negotiation_options": [
                option.model_dump(mode="json") for option in memory.negotiation_options
            ],
        }

    def _load_session(
        self, db: Session, user: User, session_id: str
    ) -> MealChatSession | None:
        return (
            db.query(MealChatSession)
            .filter(MealChatSession.id == session_id, MealChatSession.user_id == user.id)
            .first()
        )

    def start_session(self, db: Session, user: User, locale: str = "zh") -> Dict[str, Any]:
        resolved_locale = normalize_locale(locale)
        memory = ConversationMemory(
            phase="discovering",
            profile={
                "gender": user.gender,
                "age": user.age,
                "height": user.height,
                "weight": user.weight,
                "activity_level": user.activity_level,
            },
            preferences={"health_goal": normalize_goal(user.health_goal) or "healthy"},
            known_facts={"locale": resolved_locale},
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
                content=session_intro(resolved_locale),
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
        session = self._load_session(db, user, session_id)
        if not session:
            return None
        return self._serialize_session(db, session)

    def handle_message(
        self,
        db: Session,
        user: User,
        session_id: str,
        content: str,
        locale: str = "zh",
    ) -> Dict[str, Any]:
        session = self._load_session(db, user, session_id)
        if session is None:
            raise ValueError("session_not_found")

        stage_before = session.status
        resolved_locale = normalize_locale(locale)
        current_slots = dict(session.collected_slots or {})
        current_known_facts = dict(current_slots.get("known_facts") or {})
        current_known_facts["locale"] = resolved_locale
        current_slots["known_facts"] = current_known_facts
        session.collected_slots = current_slots

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

    def generate_session(self, db: Session, user: User, session_id: str) -> Dict[str, Any]:
        session = self._load_session(db, user, session_id)
        if session is None:
            raise ValueError("session_not_found")

        if session.status == "finalized":
            return self._serialize_session(db, session)
        if session.status != "planning_ready":
            raise ValueError("generation_not_ready")

        try:
            result = self.orchestrator.generate(user, session)
            updated_memory = ConversationMemory.model_validate(session.collected_slots or {})
            updated_memory.overlay_state = "result"
            session.collected_slots = updated_memory.model_dump(mode="json")
            session.status = result["status"]
            if result["meal_plan"] is not None:
                session.final_plan = result["meal_plan"]

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
                event="generation_completed",
                payload={
                    "user_id": user.id,
                    "status": result["status"],
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
                event="generation_failed",
                payload={
                    "user_id": user.id,
                    "status": session.status,
                    "error": repr(exc),
                },
            )
            raise

    def update_session_presentation(
        self,
        db: Session,
        user: User,
        session_id: str,
        overlay_state: str,
    ) -> Dict[str, Any]:
        session = self._load_session(db, user, session_id)
        if session is None:
            raise ValueError("session_not_found")

        memory = ConversationMemory.model_validate(session.collected_slots or {})
        memory.overlay_state = overlay_state
        session.collected_slots = memory.model_dump(mode="json")

        db.add(session)
        db.commit()
        db.refresh(session)
        return self._serialize_session(db, session)

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
        plans: list[dict[str, Any]] = []
        for row in rows:
            if not row.final_plan:
                continue

            final_plan = row.final_plan
            attachable_plan = (
                final_plan.get("primary")
                if isinstance(final_plan.get("primary"), dict)
                else final_plan
            )
            if not isinstance(attachable_plan, dict):
                continue

            plans.append(
                {
                    **attachable_plan,
                    "source_session_id": row.id,
                }
            )
        return plans


class WeeklyPlanService:
    def _resolve_requested_meal_plan(
        self, final_plan: Dict[str, Any], meal_plan_id: str
    ) -> Dict[str, Any]:
        candidates: list[dict[str, Any]] = []
        if isinstance(final_plan.get("primary"), dict):
            candidates.append(final_plan["primary"])
            for alternative in final_plan.get("alternatives", []):
                meal_plan = alternative.get("meal_plan")
                if isinstance(meal_plan, dict):
                    candidates.append(meal_plan)
        else:
            candidates.append(final_plan)

        for candidate in candidates:
            if candidate.get("id") == meal_plan_id:
                return candidate

        raise HTTPException(status_code=409, detail="Meal plan id does not match session")

    def _freeze_meal_plan_snapshot(self, meal_plan: Dict[str, Any]) -> Dict[str, Any]:
        snapshot = copy.deepcopy(meal_plan)
        frozen_meals = []

        for meal in snapshot.get("meals", []):
            recipe = recipe_service.get_by_id(meal.get("recipe_id"))
            frozen_meal = copy.deepcopy(meal)
            frozen_meal["ingredients"] = copy.deepcopy(
                frozen_meal.get("ingredients") or (recipe.ingredients if recipe else []) or []
            )
            frozen_meals.append(frozen_meal)

        snapshot["meals"] = frozen_meals
        return snapshot

    def _serialize_day(self, day: models.WeeklyPlanDay) -> Dict[str, Any]:
        return {
            "id": day.id,
            "plan_date": day.plan_date,
            "source_session_id": day.source_session_id,
            "meal_plan_snapshot": day.meal_plan_snapshot,
            "nutrition_snapshot": day.nutrition_snapshot or {},
        }

    def _serialize_plan(self, plan: models.WeeklyPlan) -> Dict[str, Any]:
        days = list(plan.days or [])
        return {
            "id": plan.id,
            "name": plan.name,
            "notes": plan.notes,
            "created_at": plan.created_at,
            "updated_at": plan.updated_at,
            "days": [self._serialize_day(day) for day in days],
        }

    def _serialize_summary(self, plan: models.WeeklyPlan) -> Dict[str, Any]:
        return {
            "id": plan.id,
            "name": plan.name,
            "notes": plan.notes,
            "created_at": plan.created_at,
            "updated_at": plan.updated_at,
            "day_count": len(plan.days or []),
        }

    def get_owned_plan(
        self, db: Session, user_id: int, plan_id: int
    ) -> models.WeeklyPlan:
        plan = (
            db.query(models.WeeklyPlan)
            .options(selectinload(models.WeeklyPlan.days))
            .filter(models.WeeklyPlan.id == plan_id, models.WeeklyPlan.user_id == user_id)
            .first()
        )
        if plan is None:
            raise HTTPException(status_code=404, detail="Weekly plan not found")
        return plan

    def list_plans(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        plans = (
            db.query(models.WeeklyPlan)
            .options(selectinload(models.WeeklyPlan.days))
            .filter(models.WeeklyPlan.user_id == user_id)
            .order_by(models.WeeklyPlan.updated_at.desc(), models.WeeklyPlan.id.desc())
            .all()
        )
        return [self._serialize_summary(plan) for plan in plans]

    def create_plan(
        self, db: Session, user_id: int, name: str, notes: str | None
    ) -> Dict[str, Any]:
        plan = models.WeeklyPlan(user_id=user_id, name=name, notes=notes)
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return self.get_plan(db, user_id, plan.id)

    def get_plan(self, db: Session, user_id: int, plan_id: int) -> Dict[str, Any]:
        plan = self.get_owned_plan(db, user_id, plan_id)
        return self._serialize_plan(plan)

    def attach_day_from_session(
        self,
        db: Session,
        user_id: int,
        plan_id: int,
        plan_date: date,
        meal_plan_id: str,
        source_session_id: str | None,
    ) -> Dict[str, Any]:
        plan = self.get_owned_plan(db, user_id, plan_id)
        session = (
            db.query(models.MealChatSession)
            .filter(
                models.MealChatSession.id == source_session_id,
                models.MealChatSession.user_id == user_id,
            )
            .first()
        )
        if session is None:
            raise HTTPException(status_code=404, detail="Meal chat session not found")
        if not session.final_plan:
            raise HTTPException(status_code=409, detail="Meal plan is not finalized")

        existing_day = next((day for day in plan.days if day.plan_date == plan_date), None)
        if existing_day is not None:
            raise HTTPException(status_code=409, detail="Plan date already occupied")

        requested_plan = self._resolve_requested_meal_plan(session.final_plan, meal_plan_id)
        snapshot = self._freeze_meal_plan_snapshot(requested_plan)
        day = models.WeeklyPlanDay(
            weekly_plan_id=plan.id,
            plan_date=plan_date,
            source_session_id=session.id,
            meal_plan_snapshot=snapshot,
            nutrition_snapshot=snapshot.get("nutrition", {}),
        )
        db.add(day)
        db.commit()
        return self.get_plan(db, user_id, plan.id)

    def remove_day(
        self, db: Session, user_id: int, plan_id: int, day_id: int
    ) -> Dict[str, Any]:
        plan = self.get_owned_plan(db, user_id, plan_id)
        day = next((entry for entry in plan.days if entry.id == day_id), None)
        if day is None:
            raise HTTPException(status_code=404, detail="Weekly plan day not found")

        db.delete(day)
        db.commit()
        return self.get_plan(db, user_id, plan.id)


class ShoppingListService:
    def _serialize_item(self, item: models.ShoppingListItem) -> Dict[str, Any]:
        return {
            "id": item.id,
            "ingredient_name": item.ingredient_name,
            "display_amount": item.display_amount or "",
            "checked": bool(item.checked),
            "category": item.category,
            "source_kind": item.source_kind,
            "sources": item.source_refs or [],
        }

    def _serialize_list(self, shopping_list: models.ShoppingList) -> Dict[str, Any]:
        return {
            "id": shopping_list.id,
            "weekly_plan_id": shopping_list.weekly_plan_id,
            "name": shopping_list.name,
            "status": shopping_list.status,
            "created_at": shopping_list.created_at,
            "updated_at": shopping_list.updated_at,
            "items": [self._serialize_item(item) for item in shopping_list.items or []],
        }

    def _serialize_summary(self, shopping_list: models.ShoppingList) -> Dict[str, Any]:
        return {
            "id": shopping_list.id,
            "weekly_plan_id": shopping_list.weekly_plan_id,
            "name": shopping_list.name,
            "status": shopping_list.status,
            "created_at": shopping_list.created_at,
            "updated_at": shopping_list.updated_at,
            "item_count": len(shopping_list.items or []),
        }

    def _normalize_ingredient_entry(
        self, ingredient: Any, meal: Dict[str, Any]
    ) -> Dict[str, Any] | None:
        if isinstance(ingredient, dict):
            name = (
                ingredient.get("name")
                or ingredient.get("ingredient_name")
                or ingredient.get("ingredient")
                or ingredient.get("item")
                or ingredient.get("title")
            )
            amount = (
                ingredient.get("amount")
                or ingredient.get("quantity")
                or ingredient.get("display_amount")
                or ""
            )
            category = ingredient.get("category") or meal.get("meal_type")
        else:
            name = str(ingredient).strip() if ingredient is not None else ""
            amount = ""
            category = meal.get("meal_type")

        if not name:
            return None

        return {
            "ingredient_name": str(name).strip(),
            "display_amount": str(amount).strip(),
            "category": category,
        }

    def _append_aggregated_item(
        self,
        aggregated: Dict[str, Dict[str, Any]],
        ingredient_name: str,
        display_amount: str,
        category: str | None,
        source_ref: Dict[str, Any],
        source_kind: str = "weekly-plan",
    ) -> None:
        key = ingredient_name.strip().lower()
        bucket = aggregated.setdefault(
            key,
            {
                "ingredient_name": ingredient_name.strip(),
                "display_amount": display_amount.strip(),
                "category": category,
                "source_kind": source_kind,
                "source_refs": [],
            },
        )
        if display_amount and not bucket["display_amount"]:
            bucket["display_amount"] = display_amount.strip()
        if category and not bucket["category"]:
            bucket["category"] = category
        bucket["source_refs"].append(source_ref)

    def _build_generated_items(
        self, plan: models.WeeklyPlan
    ) -> List[Dict[str, Any]]:
        aggregated: Dict[str, Dict[str, Any]] = {}
        for day in plan.days:
            meal_plan_snapshot = day.meal_plan_snapshot or {}
            for meal in meal_plan_snapshot.get("meals", []):
                source_ref = {
                    "plan_date": str(day.plan_date),
                    "meal_type": meal.get("meal_type", ""),
                    "recipe_name": meal.get("recipe_name", ""),
                }
                ingredients = meal.get("ingredients") or []
                parsed_entries = [
                    self._normalize_ingredient_entry(entry, meal) for entry in ingredients
                ]
                parsed_entries = [entry for entry in parsed_entries if entry is not None]

                if not parsed_entries:
                    parsed_entries = [
                        {
                            "ingredient_name": meal.get("recipe_name", "Unknown recipe"),
                            "display_amount": "",
                            "category": meal.get("meal_type"),
                        }
                    ]

                for entry in parsed_entries:
                    self._append_aggregated_item(
                        aggregated=aggregated,
                        ingredient_name=entry["ingredient_name"],
                        display_amount=entry["display_amount"],
                        category=entry["category"],
                        source_ref=source_ref,
                    )

        return list(aggregated.values())

    def get_owned_list(
        self, db: Session, user_id: int, shopping_list_id: int
    ) -> models.ShoppingList:
        shopping_list = (
            db.query(models.ShoppingList)
            .options(selectinload(models.ShoppingList.items))
            .filter(
                models.ShoppingList.id == shopping_list_id,
                models.ShoppingList.user_id == user_id,
            )
            .first()
        )
        if shopping_list is None:
            raise HTTPException(status_code=404, detail="Shopping list not found")
        return shopping_list

    def list_lists(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        shopping_lists = (
            db.query(models.ShoppingList)
            .options(selectinload(models.ShoppingList.items))
            .filter(models.ShoppingList.user_id == user_id)
            .order_by(models.ShoppingList.updated_at.desc(), models.ShoppingList.id.desc())
            .all()
        )
        return [self._serialize_summary(entry) for entry in shopping_lists]

    def get_list(
        self, db: Session, user_id: int, shopping_list_id: int
    ) -> Dict[str, Any]:
        shopping_list = self.get_owned_list(db, user_id, shopping_list_id)
        return self._serialize_list(shopping_list)

    def generate_from_weekly_plan(
        self, db: Session, user_id: int, weekly_plan_id: int, name: str | None
    ) -> Dict[str, Any]:
        plan = weekly_plan_service.get_owned_plan(db, user_id, weekly_plan_id)
        generated_items = self._build_generated_items(plan)
        shopping_list = models.ShoppingList(
            user_id=user_id,
            weekly_plan_id=plan.id,
            name=name or f"{plan.name} 采购清单",
            status="active",
        )
        db.add(shopping_list)
        db.flush()

        for item in generated_items:
            db.add(
                models.ShoppingListItem(
                    shopping_list_id=shopping_list.id,
                    ingredient_name=item["ingredient_name"],
                    display_amount=item["display_amount"],
                    checked=False,
                    category=item["category"],
                    source_kind=item["source_kind"],
                    source_refs=item["source_refs"],
                )
            )

        db.commit()
        return self.get_list(db, user_id, shopping_list.id)

    def add_manual_item(
        self,
        db: Session,
        user_id: int,
        shopping_list_id: int,
        ingredient_name: str,
        display_amount: str | None,
        category: str | None,
    ) -> Dict[str, Any]:
        shopping_list = self.get_owned_list(db, user_id, shopping_list_id)
        db.add(
            models.ShoppingListItem(
                shopping_list_id=shopping_list.id,
                ingredient_name=ingredient_name.strip(),
                display_amount=(display_amount or "").strip(),
                checked=False,
                category=category,
                source_kind="manual",
                source_refs=[],
            )
        )
        db.commit()
        return self.get_list(db, user_id, shopping_list.id)

    def update_item(
        self,
        db: Session,
        user_id: int,
        shopping_list_id: int,
        item_id: int,
        updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        shopping_list = self.get_owned_list(db, user_id, shopping_list_id)
        item = next((entry for entry in shopping_list.items if entry.id == item_id), None)
        if item is None:
            raise HTTPException(status_code=404, detail="Shopping list item not found")

        for field in ("checked", "display_amount", "category"):
            if field in updates:
                setattr(item, field, updates[field])

        db.add(item)
        db.commit()
        return self.get_list(db, user_id, shopping_list.id)

    def delete_item(
        self, db: Session, user_id: int, shopping_list_id: int, item_id: int
    ) -> Dict[str, Any]:
        shopping_list = self.get_owned_list(db, user_id, shopping_list_id)
        item = next((entry for entry in shopping_list.items if entry.id == item_id), None)
        if item is None:
            raise HTTPException(status_code=404, detail="Shopping list item not found")

        db.delete(item)
        db.commit()
        return self.get_list(db, user_id, shopping_list.id)


recipe_service = RecipeService()
meal_plan_service = MealPlanService()
meal_chat_app = MealChatApplication()
weekly_plan_service = WeeklyPlanService()
shopping_list_service = ShoppingListService()
