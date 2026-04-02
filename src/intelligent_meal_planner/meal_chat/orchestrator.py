import re

from .target_mapper import build_hidden_targets


PROFILE_FIELDS = ["gender", "age", "height", "weight", "activity_level"]
PREFERENCE_FIELDS = {
    "health_goal",
    "budget",
    "disliked_foods",
    "preferred_tags",
    "restrictions_answered",
}
BUDGET_VALUE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)")

QUESTION_TEXT = {
    "gender": "为了更准确地了解你的身体情况，我先确认一下你的性别。",
    "age": "告诉我一下你的年龄。",
    "height": "告诉我一下你的身高，单位厘米。",
    "weight": "告诉我一下你的体重，单位公斤。",
    "activity_level": "你平时的活动强度更接近久坐、轻度活动、中等活动，还是高活动量？",
    "health_goal": "你这段时间更偏向减脂、增肌、维持状态，还是日常健康饮食？",
    "budget": "这次你希望我把一天三餐预算控制在多少元以内？",
    "restrictions": "你有没有忌口、过敏或者明确不吃的食物？如果没有也可以直接告诉我。",
    "taste": "口味上你更偏向清淡、家常、重口一点，还是有什么特别想吃的方向？",
}

BUDGET_REJECTED_MESSAGE = (
    "按你当前的需求，这个预算过低，需要适当提高预算后我再为你正式配餐。"
)
PLAN_READY_MESSAGE = "我已经根据你的情况整理出一份预算内的一日三餐方案。"


class MealChatOrchestrator:
    def __init__(self, extractor, budget_guard, planner):
        self.extractor = extractor
        self.budget_guard = budget_guard
        self.planner = planner

    def _missing_profile_field(self, user):
        for field in PROFILE_FIELDS:
            if getattr(user, field, None) in (None, ""):
                return field
        return None

    def _next_question_key(self, user, slots):
        missing_profile = self._missing_profile_field(user)
        if missing_profile:
            return missing_profile
        if not slots.get("health_goal") and not getattr(user, "health_goal", None):
            return "health_goal"
        if not slots.get("budget"):
            return "budget"
        if not slots.get("restrictions_answered"):
            return "restrictions"
        if "preferred_tags" not in slots:
            return "taste"
        return None

    def _normalize_slot_value(self, field, value):
        if field != "budget":
            return value
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            match = BUDGET_VALUE_PATTERN.search(value.replace(",", ""))
            if match:
                return float(match.group(1))
        return value

    def _normalize_slots(self, slots):
        normalized = dict(slots or {})
        for field, value in tuple(normalized.items()):
            normalized[field] = self._normalize_slot_value(field, value)
        return normalized

    def advance(self, user, session, user_message: str):
        current_slots = self._normalize_slots(session.collected_slots or {})
        expected_slot = self._next_question_key(user, current_slots)
        parsed = self.extractor.parse(user_message, expected_slot=expected_slot)

        slots = dict(current_slots)
        for field, value in parsed.profile_updates.items():
            value = self._normalize_slot_value(field, value)
            if value in (None, ""):
                continue
            if field in PROFILE_FIELDS:
                setattr(user, field, value)
            elif field in PREFERENCE_FIELDS:
                slots[field] = value

        for field, value in parsed.preference_updates.items():
            value = self._normalize_slot_value(field, value)
            if value in (None, ""):
                continue
            if field in PROFILE_FIELDS:
                setattr(user, field, value)
            else:
                slots[field] = value

        if parsed.acknowledged_restrictions:
            slots["restrictions_answered"] = True
        session.collected_slots = slots

        question_key = self._next_question_key(user, slots)
        trace = {
            "expected_slot": expected_slot,
            "next_question_key": question_key,
            "parsed_turn": parsed.model_dump(mode="json"),
        }
        if question_key:
            session.status = (
                "collecting_profile"
                if question_key in PROFILE_FIELDS
                else "collecting_preferences"
            )
            return {
                "status": session.status,
                "assistant_message": QUESTION_TEXT[question_key],
                "hidden_targets": None,
                "meal_plan": None,
                "trace": trace,
            }

        goal = slots.get("health_goal") or getattr(user, "health_goal", "healthy")
        targets = build_hidden_targets(
            {
                "gender": user.gender,
                "age": user.age,
                "height": user.height,
                "weight": user.weight,
                "activity_level": user.activity_level,
            },
            goal,
        )
        session.hidden_targets = targets

        feasible = self.budget_guard.check(
            budget=slots["budget"],
            target_calories=targets["target_calories"],
            target_protein=targets["target_protein"],
            target_carbs=targets["target_carbs"],
            target_fat=targets["target_fat"],
        )
        if not feasible:
            session.status = "budget_rejected"
            return {
                "status": "budget_rejected",
                "assistant_message": BUDGET_REJECTED_MESSAGE,
                "hidden_targets": None,
                "meal_plan": None,
                "trace": trace,
            }

        try:
            meal_plan = self.planner.generate(
                goal=goal,
                budget=slots["budget"],
                disliked_foods=slots.get("disliked_foods", []),
                preferred_tags=slots.get("preferred_tags", []),
                hidden_targets=targets,
            )
        except ValueError:
            session.status = "budget_rejected"
            return {
                "status": "budget_rejected",
                "assistant_message": BUDGET_REJECTED_MESSAGE,
                "hidden_targets": None,
                "meal_plan": None,
                "trace": trace,
            }
        session.status = "completed"
        session.final_plan = meal_plan
        return {
            "status": "completed",
            "assistant_message": PLAN_READY_MESSAGE,
            "hidden_targets": targets,
            "meal_plan": meal_plan,
            "trace": trace,
        }
