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
  "acknowledged_restrictions": false
}
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

    def _apply_slot_fallback(self, payload: dict, user_message: str, expected_slot: str | None) -> tuple[dict, bool]:
        text = re.sub(r"\s+", "", user_message)
        fallback_applied = False

        if expected_slot == "restrictions" and any(token in text for token in EMPTY_RESTRICTION_ANSWERS):
            payload.setdefault("preference_updates", {})
            payload["preference_updates"].setdefault("disliked_foods", [])
            payload["acknowledged_restrictions"] = True
            fallback_applied = True

        return payload, fallback_applied

    def parse(self, user_message: str, expected_slot: str | None = None) -> ParsedTurn:
        response = self.client.invoke(_build_messages(user_message, expected_slot))
        raw = response.content.strip()
        json_match = re.search(r"\{.*\}", raw, re.S)
        payload = json.loads(json_match.group(0) if json_match else raw)
        payload, fallback_applied = self._apply_slot_fallback(payload, user_message, expected_slot)
        payload["debug"] = {
            "expected_slot": expected_slot,
            "raw_response": raw,
            "payload": dict(payload),
            "fallback_applied": fallback_applied,
        }
        return ParsedTurn.model_validate(payload)
