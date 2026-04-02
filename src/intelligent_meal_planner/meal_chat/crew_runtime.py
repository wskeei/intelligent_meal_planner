from __future__ import annotations

import re

from .feasibility_negotiator import build_negotiation_result
from .session_schema import ConversationMemory, TargetRanges
from .target_ranges import build_target_ranges
from .types import CrewTurnResult

BUDGET_VALUE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*元?")
CHINESE_BUDGET_PATTERN = re.compile(
    r"(?:预算|控制在|控制到|别超过|不超过|不高于|低于|最多|上限)[^零一二两三四五六七八九十百千万]*([零一二两三四五六七八九十百千万]+)"
)
CHINESE_BUDGET_SUFFIX_PATTERN = re.compile(r"([零一二两三四五六七八九十百千万]+)(?:元|块|以内|以下|左右)")
GOAL_KEYWORDS = {
    "lose_weight": ("减肥", "减脂", "瘦身", "瘦一点", "瘦点", "控制体重"),
    "gain_muscle": ("增肌", "长肌肉", "练壮一点", "练壮点", "壮一点"),
    "maintain": ("维持", "保持", "不增不减", "正常吃"),
    "healthy": ("健康饮食", "健康一点", "均衡", "吃健康点", "吃干净点"),
}
PREFERRED_TAG_KEYWORDS = ("清淡", "家常", "重口", "高蛋白")
DISLIKED_FOODS_PATTERN = re.compile(r"(?:不吃|不要|别要)([^，。,.；;\s]+)")


class CrewMealChatRuntime:
    def __init__(self, planning_tool):
        self.planning_tool = planning_tool

    def run_turn(self, user_message: str, memory: ConversationMemory) -> CrewTurnResult:
        intent = self.intent_agent(user_message=user_message, memory=memory)
        profile_delta = self.profile_agent(
            user_message=user_message,
            memory=memory,
            intent=intent,
        )
        merged_memory = self._merge_memory(memory, profile_delta)

        strategy = self.strategy_agent(memory=merged_memory)
        if strategy.get("target_ranges"):
            merged_memory.target_ranges = TargetRanges.model_validate(
                strategy["target_ranges"]
            )

        negotiation = self.negotiator_agent(
            user_message=user_message,
            memory=merged_memory,
            intent=intent,
        )
        merged_memory.phase = negotiation["phase"]
        merged_memory.negotiation_options = negotiation.get("options", [])

        if not intent.get("needs_plan"):
            return CrewTurnResult(
                phase=merged_memory.phase,
                assistant_message=negotiation["assistant_message"],
                memory=merged_memory,
                negotiation_options=merged_memory.negotiation_options,
            )

        plan = self.planning_agent(memory=merged_memory, user_message=user_message)
        return CrewTurnResult(
            phase=plan["phase"],
            assistant_message=plan["assistant_message"],
            memory=merged_memory,
            negotiation_options=merged_memory.negotiation_options,
            meal_plan=plan["meal_plan"],
        )

    def intent_agent(self, user_message: str, memory: ConversationMemory) -> dict:
        text = user_message.lower()
        asks_budget = "预算" in user_message and any(
            token in user_message for token in ("多少", "最低", "至少", "?")
        )
        needs_plan = any(
            token in text for token in ("方案", "计划", "meal plan", "plan")
        )
        if asks_budget:
            return {"intent": "budget_question", "needs_plan": False}
        if needs_plan or memory.phase == "planning":
            return {"intent": "plan_request", "needs_plan": True}
        return {"intent": "general_chat", "needs_plan": False}

    def profile_agent(
        self, user_message: str, memory: ConversationMemory, intent: dict
    ) -> dict:
        del memory, intent
        preference_updates = {}
        budget = self._extract_budget(user_message)
        health_goal = self._extract_health_goal(user_message)
        disliked_foods = self._extract_disliked_foods(user_message)
        preferred_tags = self._extract_preferred_tags(user_message)

        if budget is not None:
            preference_updates["budget"] = budget
        if health_goal is not None:
            preference_updates["health_goal"] = health_goal
        if disliked_foods:
            preference_updates["disliked_foods"] = disliked_foods
        if preferred_tags:
            preference_updates["preferred_tags"] = preferred_tags

        return {
            "profile_updates": {},
            "preference_updates": preference_updates,
        }

    def strategy_agent(self, memory: ConversationMemory) -> dict:
        profile = memory.profile
        goal = memory.preferences.get("health_goal", "healthy")
        if not profile:
            return {"target_ranges": memory.target_ranges}
        return {
            "target_ranges": build_target_ranges(profile=profile, goal=goal),
        }

    def negotiator_agent(
        self, user_message: str, memory: ConversationMemory, intent: dict
    ) -> dict:
        budget = memory.preferences.get("budget")
        if budget is None or memory.target_ranges is None:
            return {
                "phase": memory.phase,
                "assistant_message": "我还需要你的预算和目标信息，才能继续判断。",
                "options": [],
            }

        negotiation = build_negotiation_result(
            budget=float(budget),
            target_ranges=memory.target_ranges,
        )
        return {
            "phase": negotiation.phase,
            "assistant_message": negotiation.explanation,
            "options": negotiation.options,
        }

    def planning_agent(self, memory: ConversationMemory, user_message: str) -> dict:
        del user_message
        if self.planning_tool is None:
            return {
                "phase": "planning",
                "assistant_message": "我已经准备好开始配餐。",
                "meal_plan": None,
            }
        if memory.negotiation_options:
            return {
                "phase": "finalized",
                "assistant_message": "我给你整理了两套方案。",
                "meal_plan": self._build_dual_plan(memory),
            }
        return {
            "phase": "finalized",
            "assistant_message": "我给你整理好了一份方案。",
            "meal_plan": self.planning_tool.generate(
                goal=memory.preferences.get("health_goal", "healthy"),
                budget=float(memory.preferences.get("budget", 0)),
                disliked_foods=memory.preferences.get("disliked_foods", []),
                preferred_tags=memory.preferences.get("preferred_tags", []),
                hidden_targets=self._ranges_to_hidden_targets(memory.target_ranges),
            ),
        }

    def _merge_memory(
        self, memory: ConversationMemory, profile_delta: dict
    ) -> ConversationMemory:
        merged = memory.model_copy(deep=True)
        merged.profile.update(profile_delta.get("profile_updates", {}))
        merged.preferences.update(profile_delta.get("preference_updates", {}))
        return merged

    def _build_dual_plan(self, memory: ConversationMemory) -> dict:
        alternatives = []
        for option in memory.negotiation_options:
            plan = self.planning_tool.generate(
                goal=memory.preferences.get("health_goal", "healthy"),
                budget=option.budget,
                disliked_foods=memory.preferences.get("disliked_foods", []),
                preferred_tags=option.preferred_tags
                or memory.preferences.get("preferred_tags", []),
                hidden_targets=self._ranges_to_hidden_targets(
                    memory.target_ranges,
                    option.key,
                ),
            )
            alternatives.append(
                {
                    "option_key": option.key,
                    "title": option.title,
                    "rationale": option.rationale,
                    "meal_plan": plan,
                }
            )
        return {
            "primary": alternatives[0]["meal_plan"] if alternatives else None,
            "alternatives": alternatives,
        }

    def _ranges_to_hidden_targets(
        self,
        target_ranges: TargetRanges | None,
        option_key: str | None = None,
    ) -> dict:
        if target_ranges is None:
            return {
                "target_calories": 1800,
                "target_protein": 100,
                "target_carbs": 180,
                "target_fat": 55,
            }

        if option_key == "budget_cut":
            target_calories = target_ranges.calories_min
            target_protein = target_ranges.protein_min
            target_carbs = target_ranges.carbs_min
            target_fat = target_ranges.fat_min
        elif option_key == "protein_priority":
            target_calories = target_ranges.calories_max
            target_protein = target_ranges.protein_max
            target_carbs = target_ranges.carbs_min
            target_fat = target_ranges.fat_min
        else:
            target_calories = round(
                (target_ranges.calories_min + target_ranges.calories_max) / 2
            )
            target_protein = round(
                (target_ranges.protein_min + target_ranges.protein_max) / 2
            )
            target_carbs = round(
                (target_ranges.carbs_min + target_ranges.carbs_max) / 2
            )
            target_fat = round((target_ranges.fat_min + target_ranges.fat_max) / 2)

        return {
            "target_calories": int(target_calories),
            "target_protein": int(target_protein),
            "target_carbs": int(target_carbs),
            "target_fat": int(target_fat),
        }

    def _extract_budget(self, user_message: str) -> float | None:
        match = BUDGET_VALUE_PATTERN.search(user_message.replace(",", ""))
        if match:
            return float(match.group(1))

        normalized = user_message.replace("俩", "两")
        chinese_match = CHINESE_BUDGET_PATTERN.search(normalized)
        if not chinese_match:
            chinese_match = CHINESE_BUDGET_SUFFIX_PATTERN.search(normalized)
        if not chinese_match:
            return None

        return float(self._parse_chinese_number(chinese_match.group(1)))

    def _extract_health_goal(self, user_message: str) -> str | None:
        for goal, keywords in GOAL_KEYWORDS.items():
            if any(keyword in user_message for keyword in keywords):
                return goal
        return None

    def _extract_disliked_foods(self, user_message: str) -> list[str]:
        foods = []
        for match in DISLIKED_FOODS_PATTERN.finditer(user_message):
            food = match.group(1).strip()
            if food and food not in foods:
                foods.append(food)
        return foods

    def _extract_preferred_tags(self, user_message: str) -> list[str]:
        return [
            keyword for keyword in PREFERRED_TAG_KEYWORDS if keyword in user_message
        ]

    def _parse_chinese_number(self, text: str) -> int:
        digits = {
            "零": 0,
            "一": 1,
            "二": 2,
            "两": 2,
            "三": 3,
            "四": 4,
            "五": 5,
            "六": 6,
            "七": 7,
            "八": 8,
            "九": 9,
        }
        units = {
            "十": 10,
            "百": 100,
            "千": 1000,
            "万": 10000,
        }

        normalized = text
        if (
            "百" in normalized
            and "十" not in normalized
            and normalized[-1] in digits
        ):
            normalized = f"{normalized}十"
        if normalized.startswith("十"):
            normalized = f"一{normalized}"

        total = 0
        section = 0
        number = 0

        for char in normalized:
            if char in digits:
                number = digits[char]
                continue

            unit = units.get(char)
            if unit is None:
                continue

            if unit == 10000:
                section = (section + number) * unit
                total += section
                section = 0
                number = 0
                continue

            if number == 0:
                number = 1
            section += number * unit
            number = 0

        return total + section + number
