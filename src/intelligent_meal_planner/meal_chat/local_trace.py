import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any


class MealChatTraceWriter:
    def __init__(self, base_dir: str | Path | None = None):
        configured = base_dir or os.getenv("MEAL_CHAT_TRACE_DIR", "logs/meal_chat")
        self.base_dir = Path(configured)

    def _resolve_file(self, session_id: str) -> Path:
        day_dir = self.base_dir / date.today().isoformat()
        day_dir.mkdir(parents=True, exist_ok=True)
        return day_dir / f"{session_id}.jsonl"

    def write(self, session_id: str, event: str, payload: dict[str, Any]) -> None:
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "event": event,
            "payload": payload,
        }
        with self._resolve_file(session_id).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
