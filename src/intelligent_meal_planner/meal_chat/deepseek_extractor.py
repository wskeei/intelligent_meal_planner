import json
import os
import re

from langchain_openai import ChatOpenAI

from .types import ParsedTurn

SYSTEM_PROMPT = """
你是配餐对话信息提取器。
只提取结构化事实，不生成建议。
返回 JSON:
{
  "profile_updates": {},
  "preference_updates": {},
  "acknowledged_restrictions": false,
  "confidence": 0.0,
  "missing_fields": []
}

字段约束:
- profile_updates 只允许: gender, age, height, weight, activity_level
- preference_updates 只允许: health_goal, budget, disliked_foods, preferred_tags, restrictions_answered
- confidence 为 0 到 1 的浮点数，表示你对本轮提取结果的把握
- missing_fields 只允许填写当前仍缺失、且用户这轮没有明确提供的关键字段
"""

EMPTY_RESTRICTION_ANSWERS = {
    "没有",
    "没",
    "没有忌口",
    "没有过敏",
    "都能吃",
    "都可以",
    "不忌口",
}
EMPTY_TASTE_ANSWERS = {
    "都行",
    "都可以",
    "随便",
    "都能接受",
    "没所谓",
}
BUDGET_VALUE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)")

PROFILE_FIELDS = {"gender", "age", "height", "weight", "activity_level"}
PREFERENCE_FIELDS = {
    "health_goal",
    "budget",
    "disliked_foods",
    "preferred_tags",
    "restrictions_answered",
}
ALLOWED_MISSING_FIELDS = PROFILE_FIELDS | {
    "health_goal",
    "budget",
    "disliked_foods",
    "preferred_tags",
}


def _coerce_budget_value(value):
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = BUDGET_VALUE_PATTERN.search(value.replace(",", ""))
        if match:
            return float(match.group(1))
    return value


def _build_messages(user_message: str, expected_slot: str | None):
    return [
        ("system", SYSTEM_PROMPT),
        (
            "human",
            (
                f"expected_slot={expected_slot or 'unknown'}\n"
                "如果用户是在回答上一轮问题，请优先按 expected_slot 提取。\n"
                f"message={user_message}"
            ),
        ),
    ]


class DeepSeekSlotExtractor:
    def __init__(self):
        self.client = ChatOpenAI(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1"),
            temperature=0,
        )

    def _apply_slot_fallback(
        self, payload: dict, user_message: str, expected_slot: str | None
    ) -> tuple[dict, bool]:
        text = re.sub(r"\s+", "", user_message)
        fallback_applied = False

        if expected_slot == "restrictions" and any(
            token in text for token in EMPTY_RESTRICTION_ANSWERS
        ):
            payload.setdefault("preference_updates", {})
            payload["preference_updates"].setdefault("disliked_foods", [])
            payload["acknowledged_restrictions"] = True
            fallback_applied = True
        if expected_slot == "taste" and any(
            token in text for token in EMPTY_TASTE_ANSWERS
        ):
            payload.setdefault("preference_updates", {})
            payload["preference_updates"].setdefault("preferred_tags", [])
            fallback_applied = True

        return payload, fallback_applied

    def _normalize_payload(self, payload: dict, expected_slot: str | None) -> dict:
        profile_updates = dict(payload.get("profile_updates") or {})
        preference_updates = dict(payload.get("preference_updates") or {})

        for field in tuple(profile_updates):
            if field in PREFERENCE_FIELDS:
                preference_updates.setdefault(field, profile_updates.pop(field))

        for field in tuple(preference_updates):
            if field in PROFILE_FIELDS:
                profile_updates.setdefault(field, preference_updates.pop(field))

        if expected_slot in PREFERENCE_FIELDS and expected_slot in profile_updates:
            preference_updates.setdefault(
                expected_slot, profile_updates.pop(expected_slot)
            )
        if expected_slot in PROFILE_FIELDS and expected_slot in preference_updates:
            profile_updates.setdefault(
                expected_slot, preference_updates.pop(expected_slot)
            )

        if "budget" in preference_updates:
            preference_updates["budget"] = _coerce_budget_value(
                preference_updates["budget"]
            )
        if "budget" in profile_updates:
            profile_updates["budget"] = _coerce_budget_value(profile_updates["budget"])

        confidence = payload.get("confidence")
        if isinstance(confidence, (int, float)):
            payload["confidence"] = max(0.0, min(1.0, float(confidence)))
        else:
            payload["confidence"] = None

        missing_fields = payload.get("missing_fields") or []
        payload["missing_fields"] = [
            field for field in missing_fields if field in ALLOWED_MISSING_FIELDS
        ]
        payload["profile_updates"] = profile_updates
        payload["preference_updates"] = preference_updates
        return payload

    def parse(self, user_message: str, expected_slot: str | None = None) -> ParsedTurn:
        response = self.client.invoke(_build_messages(user_message, expected_slot))
        raw = response.content.strip()
        json_match = re.search(r"\{.*\}", raw, re.S)
        payload = json.loads(json_match.group(0) if json_match else raw)
        payload = self._normalize_payload(payload, expected_slot)
        payload, fallback_applied = self._apply_slot_fallback(
            payload, user_message, expected_slot
        )
        payload["debug"] = {
            "expected_slot": expected_slot,
            "raw_response": raw,
            "payload": dict(payload),
            "fallback_applied": fallback_applied,
        }
        return ParsedTurn.model_validate(payload)
