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


class DeepSeekSlotExtractor:
    def __init__(self):
        self.client = ChatOpenAI(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1"),
            temperature=0,
        )

    def parse(self, user_message: str, expected_slot: str | None = None) -> ParsedTurn:
        response = self.client.invoke(
            [
                ("system", SYSTEM_PROMPT),
                ("human", f"expected_slot={expected_slot}\nmessage={user_message}"),
            ]
        )
        raw = response.content.strip()
        json_match = re.search(r"\{.*\}", raw, re.S)
        payload = json.loads(json_match.group(0) if json_match else raw)
        return ParsedTurn.model_validate(payload)
