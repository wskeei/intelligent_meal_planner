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
REQUIRED_PROFILE_FIELDS = ("gender", "age", "height", "weight", "activity_level")
REQUIRED_PREFERENCE_FIELDS = ("health_goal", "budget")
QUESTION_PROMPTS = {
    "gender": "先确认一下你的性别，这样我好把基础代谢估得更准。",
    "age": "你今年大概多少岁？我会据此调整热量范围。",
    "height": "你的身高大概多少厘米？",
    "weight": "你现在体重大概多少公斤？",
    "activity_level": "你平时活动量怎么样，久坐、轻度活动，还是经常训练？",
    "health_goal": "这次你更偏向减脂、增肌，还是先维持状态？",
    "budget": "你一天的预算大概想控制在多少？",
}
LOW_CONFIDENCE_THRESHOLD = 0.55


class CrewMealChatRuntime:
    def __init__(self, planning_tool, extractor=None):
        self.planning_tool = planning_tool
        self.extractor = extractor

    def run_turn(self, user_message: str, memory: ConversationMemory) -> CrewTurnResult:
        intent = self.intent_agent(user_message=user_message, memory=memory)
        profile_delta = self.profile_agent(
            user_message=user_message,
            memory=memory,
            intent=intent,
        )
        merged_memory = self._merge_memory(memory, profile_delta)
        assessment = self._assess_memory(merged_memory, profile_delta)
        merged_memory.open_questions = assessment["open_questions"]
        merged_memory.known_facts["preference_confidence"] = assessment["confidence"]
        merged_memory.known_facts["missing_fields"] = assessment["missing_fields"]

        if assessment["needs_follow_up"]:
            merged_memory.phase = "discovering"
            merged_memory.negotiation_options = []
            return CrewTurnResult(
                phase="discovering",
                assistant_message=assessment["assistant_message"],
                memory=merged_memory,
            )

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
        profile_updates = {}
        preference_updates = {}

        extracted = self._extract_with_ai(user_message)
        if extracted is not None:
            profile_updates.update(extracted.profile_updates)
            preference_updates.update(extracted.preference_updates)
            if (
                extracted.acknowledged_restrictions
                and "disliked_foods" not in preference_updates
            ):
                preference_updates["disliked_foods"] = []
            profile_updates = self._normalize_profile_updates(profile_updates)
            preference_updates = self._normalize_preference_updates(
                preference_updates
            )

        budget = self._extract_budget(user_message)
        health_goal = self._extract_health_goal(user_message)
        disliked_foods = self._extract_disliked_foods(user_message)
        preferred_tags = self._extract_preferred_tags(user_message)

        if budget is not None and "budget" not in preference_updates:
            preference_updates["budget"] = budget
        if health_goal is not None and "health_goal" not in preference_updates:
            preference_updates["health_goal"] = health_goal
        if disliked_foods and "disliked_foods" not in preference_updates:
            preference_updates["disliked_foods"] = disliked_foods
        if preferred_tags and "preferred_tags" not in preference_updates:
            preference_updates["preferred_tags"] = preferred_tags

        return {
            "profile_updates": profile_updates,
            "preference_updates": preference_updates,
            "confidence": self._determine_confidence(
                extracted,
                profile_updates=profile_updates,
                preference_updates=preference_updates,
            ),
            "missing_fields": list(getattr(extracted, "missing_fields", []) or []),
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

    def _extract_with_ai(self, user_message: str):
        if self.extractor is None:
            return None

        try:
            return self.extractor.parse(user_message, expected_slot=None)
        except Exception:
            return None

    def _determine_confidence(
        self,
        extracted,
        profile_updates: dict,
        preference_updates: dict,
    ) -> float:
        if extracted is not None and extracted.confidence is not None:
            return float(extracted.confidence)
        total_updates = len(profile_updates) + len(preference_updates)
        if total_updates >= 2:
            return 0.82
        if total_updates == 1:
            return 0.68
        return 0.3

    def _assess_memory(self, memory: ConversationMemory, profile_delta: dict) -> dict:
        missing_fields = list(dict.fromkeys(
            profile_delta.get("missing_fields", []) + self._find_missing_fields(memory)
        ))
        confidence = float(profile_delta.get("confidence", 0.3))
        confirmation_fields = []
        if confidence < LOW_CONFIDENCE_THRESHOLD:
            confirmation_fields = self._build_confirmation_fields(memory)

        open_questions = missing_fields or confirmation_fields
        needs_follow_up = bool(missing_fields or confidence < LOW_CONFIDENCE_THRESHOLD)

        return {
            "confidence": round(confidence, 2),
            "missing_fields": missing_fields,
            "open_questions": open_questions,
            "needs_follow_up": needs_follow_up,
            "assistant_message": self._build_follow_up_message(
                memory,
                missing_fields=missing_fields,
                confidence=confidence,
                confirmation_fields=confirmation_fields,
            ),
        }

    def _find_missing_fields(self, memory: ConversationMemory) -> list[str]:
        missing_fields = [
            field
            for field in REQUIRED_PROFILE_FIELDS
            if memory.profile.get(field) in (None, "")
        ]
        missing_fields.extend(
            field
            for field in REQUIRED_PREFERENCE_FIELDS
            if memory.preferences.get(field) in (None, "")
        )
        return missing_fields

    def _build_confirmation_fields(self, memory: ConversationMemory) -> list[str]:
        fields = []
        if memory.preferences.get("health_goal") not in (None, ""):
            fields.append("health_goal")
        if memory.preferences.get("budget") not in (None, ""):
            fields.append("budget")
        return fields or ["health_goal", "budget"]

    def _build_follow_up_message(
        self,
        memory: ConversationMemory,
        missing_fields: list[str],
        confidence: float,
        confirmation_fields: list[str],
    ) -> str:
        if missing_fields:
            prompts = [QUESTION_PROMPTS[field] for field in missing_fields[:2]]
            return "我先补齐两个关键点，这样给你的方案才会更准。 " + " ".join(prompts)

        if confidence < LOW_CONFIDENCE_THRESHOLD:
            details = []
            if "health_goal" in confirmation_fields and memory.preferences.get(
                "health_goal"
            ):
                details.append(f"目标先按“{self._render_goal(memory.preferences['health_goal'])}”理解")
            if "budget" in confirmation_fields and memory.preferences.get("budget"):
                details.append(f"预算先按 {float(memory.preferences['budget']):.0f} 元理解")
            if details:
                return "我先确认一下，" + "，".join(details) + "，对吗？"
            return "我先确认一下你的目标和预算，这样我后面的分析会更稳。"

        return "我还需要再确认一点关键信息，才能继续往下分析。"

    def _render_goal(self, goal: str) -> str:
        return {
            "lose_weight": "减脂",
            "gain_muscle": "增肌",
            "maintain": "维持",
            "healthy": "健康饮食",
        }.get(goal, goal)

    def _normalize_profile_updates(self, profile_updates: dict) -> dict:
        normalized = dict(profile_updates)
        if "height" in normalized:
            normalized["height"] = self._coerce_float(normalized["height"])
        if "weight" in normalized:
            normalized["weight"] = self._coerce_float(normalized["weight"])
        if "age" in normalized:
            normalized["age"] = self._coerce_int(normalized["age"])
        return normalized

    def _normalize_preference_updates(self, preference_updates: dict) -> dict:
        normalized = dict(preference_updates)

        if "health_goal" in normalized:
            goal = self._extract_health_goal(str(normalized["health_goal"]))
            if goal is not None:
                normalized["health_goal"] = goal

        if "budget" in normalized:
            budget = self._coerce_budget(normalized["budget"])
            if budget is not None:
                normalized["budget"] = budget

        if "disliked_foods" in normalized:
            normalized["disliked_foods"] = self._coerce_string_list(
                normalized["disliked_foods"]
            )

        if "preferred_tags" in normalized:
            preferred_tags = self._coerce_string_list(normalized["preferred_tags"])
            normalized["preferred_tags"] = [
                tag for tag in preferred_tags if tag in PREFERRED_TAG_KEYWORDS
            ]

        return normalized

    def _coerce_budget(self, value) -> float | None:
        if isinstance(value, (int, float)):
            return float(value)
        return self._extract_budget(str(value))

    def _coerce_float(self, value):
        if isinstance(value, (int, float)):
            return float(value)
        match = re.search(r"\d+(?:\.\d+)?", str(value))
        return float(match.group(0)) if match else value

    def _coerce_int(self, value):
        if isinstance(value, int):
            return value
        match = re.search(r"\d+", str(value))
        return int(match.group(0)) if match else value

    def _coerce_string_list(self, value) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [
                item.strip()
                for item in re.split(r"[，,、/；;\s]+", value)
                if item.strip()
            ]
        return []

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
