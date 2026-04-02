# Meal Chat Stuck Debug And Local Trace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复对话式配餐里“用户已回答但系统重复追问同一问题”的卡住问题，并把每轮对话与关键调试上下文落盘到本地 JSONL 文件，便于后续溯源。

**Architecture:** 根因修复放在后端对话编排链路：`MealChatOrchestrator` 先根据当前会话状态计算 `expected_slot`，再把它传给 `DeepSeekSlotExtractor`；抽取器增加确定性兜底规则，避免“没有，都能吃”这类短句因为缺少上下文而解析失败。排障留痕单独实现为 `meal_chat` 下的本地 trace writer，由 `MealChatApplication` 在会话开始、消息处理成功、消息处理失败三个时机写入 JSONL，不改现有业务表结构。

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, python `pathlib` / `json`

---

### Task 1: Reproduce The Stuck Conversation With Regression Tests

**Files:**
- Create: `tests/meal_chat/test_deepseek_extractor.py`
- Modify: `tests/meal_chat/test_orchestrator.py`
- Test: `tests/meal_chat/test_orchestrator.py`
- Test: `tests/meal_chat/test_deepseek_extractor.py`

- [ ] **Step 1: Add the failing orchestrator regression test**

```python
# tests/meal_chat/test_orchestrator.py
class RecordingExtractor:
    def __init__(self, parsed_turn):
        self.parsed_turn = parsed_turn
        self.calls = []

    def parse(self, user_message, expected_slot=None):
        self.calls.append(
            {
                "user_message": user_message,
                "expected_slot": expected_slot,
            }
        )
        return self.parsed_turn


def test_orchestrator_passes_expected_slot_before_parsing_reply():
    extractor = RecordingExtractor(
        ParsedTurn(
            profile_updates={},
            preference_updates={},
            acknowledged_restrictions=False,
        )
    )
    orchestrator = MealChatOrchestrator(
        extractor=extractor,
        budget_guard=FakeBudgetGuard(True),
        planner=FakePlanner(),
    )
    user = _user(
        gender="male",
        age=24,
        height=175,
        weight=68,
        activity_level="moderate",
        health_goal="lose_weight",
    )
    session = _session(
        status="collecting_preferences",
        collected_slots={"health_goal": "lose_weight", "budget": 100},
    )

    orchestrator.advance(user, session, "没有，都能吃")

    assert extractor.calls == [
        {
            "user_message": "没有，都能吃",
            "expected_slot": "restrictions",
        }
    ]
```

- [ ] **Step 2: Add the failing extractor fallback regression test**

```python
# tests/meal_chat/test_deepseek_extractor.py
from types import SimpleNamespace

from intelligent_meal_planner.meal_chat.deepseek_extractor import DeepSeekSlotExtractor


def test_parse_marks_empty_restrictions_reply_as_answered(monkeypatch):
    extractor = DeepSeekSlotExtractor()

    class FakeClient:
        def invoke(self, _messages):
            return SimpleNamespace(
                content='{"profile_updates": {}, "preference_updates": {}, "acknowledged_restrictions": false}'
            )

    extractor.client = FakeClient()

    parsed = extractor.parse("没有，都能吃", expected_slot="restrictions")

    assert parsed.acknowledged_restrictions is True
    assert parsed.preference_updates["disliked_foods"] == []
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/meal_chat/test_orchestrator.py tests/meal_chat/test_deepseek_extractor.py -v`

Expected:
- `test_orchestrator_passes_expected_slot_before_parsing_reply` FAIL because `MealChatOrchestrator.advance()` does not pass `expected_slot`
- `test_parse_marks_empty_restrictions_reply_as_answered` FAIL because `DeepSeekSlotExtractor.parse()` has no deterministic fallback for `restrictions`

- [ ] **Step 4: Commit the failing regression tests**

```bash
git add tests/meal_chat/test_orchestrator.py tests/meal_chat/test_deepseek_extractor.py
git commit -m "test: reproduce meal chat stuck conversation bug"
```

### Task 2: Make Slot Extraction Context-Aware And Deterministic

**Files:**
- Modify: `src/intelligent_meal_planner/meal_chat/types.py`
- Modify: `src/intelligent_meal_planner/meal_chat/deepseek_extractor.py`
- Modify: `src/intelligent_meal_planner/meal_chat/orchestrator.py`
- Test: `tests/meal_chat/test_orchestrator.py`
- Test: `tests/meal_chat/test_deepseek_extractor.py`

- [ ] **Step 1: Extend the parsed turn type to carry debug metadata**

```python
# src/intelligent_meal_planner/meal_chat/types.py
from typing import Optional

from pydantic import BaseModel, Field


class ExtractionDebug(BaseModel):
    expected_slot: Optional[str] = None
    raw_response: str = ""
    payload: dict = Field(default_factory=dict)
    fallback_applied: bool = False


class ParsedTurn(BaseModel):
    profile_updates: dict = Field(default_factory=dict)
    preference_updates: dict = Field(default_factory=dict)
    acknowledged_restrictions: bool = False
    debug: ExtractionDebug = Field(default_factory=ExtractionDebug)
```

- [ ] **Step 2: Implement expected-slot-aware fallback logic in the extractor**

```python
# src/intelligent_meal_planner/meal_chat/deepseek_extractor.py
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


def _apply_slot_fallback(self, payload: dict, user_message: str, expected_slot: str | None) -> tuple[dict, bool]:
    text = re.sub(r"\s+", "", user_message)
    fallback_applied = False

    if expected_slot == "restrictions":
        if any(token in text for token in EMPTY_RESTRICTION_ANSWERS):
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
        "payload": payload,
        "fallback_applied": fallback_applied,
    }
    return ParsedTurn.model_validate(payload)
```

- [ ] **Step 3: Pass the current slot into the extractor before merging the turn**

```python
# src/intelligent_meal_planner/meal_chat/orchestrator.py
def advance(self, user, session, user_message: str):
    current_slots = dict(session.collected_slots or {})
    expected_slot = self._next_question_key(user, current_slots)
    parsed = self.extractor.parse(user_message, expected_slot=expected_slot)

    for field, value in parsed.profile_updates.items():
        if value not in (None, ""):
            setattr(user, field, value)

    slots = dict(session.collected_slots or {})
    slots.update(parsed.preference_updates)
    if parsed.acknowledged_restrictions:
        slots["restrictions_answered"] = True
    session.collected_slots = slots

    question_key = self._next_question_key(user, slots)
    if question_key:
        session.status = "collecting_profile" if question_key in PROFILE_FIELDS else "collecting_preferences"
        return {
            "status": session.status,
            "assistant_message": QUESTION_TEXT[question_key],
            "hidden_targets": None,
            "meal_plan": None,
            "trace": {
                "expected_slot": expected_slot,
                "next_question_key": question_key,
                "parsed_turn": parsed.model_dump(mode="json"),
            },
        }
```

- [ ] **Step 4: Preserve the trace payload in all return branches**

```python
# src/intelligent_meal_planner/meal_chat/orchestrator.py
trace = {
    "expected_slot": expected_slot,
    "next_question_key": question_key,
    "parsed_turn": parsed.model_dump(mode="json"),
}

if not feasible:
    return {
        "status": "budget_rejected",
        "assistant_message": BUDGET_REJECTED_MESSAGE,
        "hidden_targets": None,
        "meal_plan": None,
        "trace": trace,
    }

return {
    "status": "completed",
    "assistant_message": PLAN_READY_MESSAGE,
    "hidden_targets": targets,
    "meal_plan": meal_plan,
    "trace": trace,
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/meal_chat/test_orchestrator.py tests/meal_chat/test_deepseek_extractor.py -v`

Expected:
- both new regression tests PASS
- existing orchestrator tests continue to PASS

- [ ] **Step 6: Commit the root-cause fix**

```bash
git add src/intelligent_meal_planner/meal_chat/types.py src/intelligent_meal_planner/meal_chat/deepseek_extractor.py src/intelligent_meal_planner/meal_chat/orchestrator.py tests/meal_chat/test_orchestrator.py tests/meal_chat/test_deepseek_extractor.py
git commit -m "fix: make meal chat slot extraction context aware"
```

### Task 3: Add Local JSONL Trace Logging For Session Replay And Debugging

**Files:**
- Create: `src/intelligent_meal_planner/meal_chat/local_trace.py`
- Create: `tests/meal_chat/test_local_trace.py`
- Modify: `src/intelligent_meal_planner/api/services.py`
- Modify: `.env.example`
- Modify: `README.md`
- Test: `tests/meal_chat/test_local_trace.py`

- [ ] **Step 1: Add the failing trace writer unit test**

```python
# tests/meal_chat/test_local_trace.py
import json
from datetime import date

from intelligent_meal_planner.meal_chat.local_trace import MealChatTraceWriter


def test_trace_writer_appends_jsonl_events(tmp_path):
    writer = MealChatTraceWriter(base_dir=tmp_path)

    writer.write(
        session_id="session001",
        event="turn_processed",
        payload={
            "status": "collecting_preferences",
            "expected_slot": "restrictions",
        },
    )

    log_file = tmp_path / date.today().isoformat() / "session001.jsonl"
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    record = json.loads(lines[0])

    assert record["session_id"] == "session001"
    assert record["event"] == "turn_processed"
    assert record["payload"]["expected_slot"] == "restrictions"
```

- [ ] **Step 2: Run the trace test to verify it fails**

Run: `uv run pytest tests/meal_chat/test_local_trace.py -v`

Expected: FAIL because `MealChatTraceWriter` does not exist.

- [ ] **Step 3: Implement the local trace writer**

```python
# src/intelligent_meal_planner/meal_chat/local_trace.py
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
```

- [ ] **Step 4: Wire the trace writer into session start and message handling**

```python
# src/intelligent_meal_planner/api/services.py
from ..meal_chat.local_trace import MealChatTraceWriter


class MealChatApplication:
    def __init__(self):
        self._orchestrator: Optional[MealChatOrchestrator] = None
        self.trace_writer = MealChatTraceWriter()

    def start_session(self, db: Session, user: User) -> Dict[str, Any]:
        session = MealChatSession(
            id=str(uuid.uuid4())[:8],
            user_id=user.id,
            status="collecting_profile",
            collected_slots={},
        )
        ...
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

    def handle_message(self, db: Session, user: User, session_id: str, content: str) -> Dict[str, Any]:
        session = (
            db.query(MealChatSession)
            .filter(MealChatSession.id == session_id, MealChatSession.user_id == user.id)
            .first()
        )
        if session is None:
            raise ValueError("session_not_found")

        try:
            db.add(MealChatMessage(session_id=session.id, role="user", content=content, stage=session.status))
            result = self.orchestrator.advance(user, session, content)
            session.status = result["status"]
            if result["hidden_targets"] is not None:
                session.hidden_targets = result["hidden_targets"]
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
                    "stage_before": session.status,
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
                    "stage_before": session.status,
                    "user_message": content,
                    "error": repr(exc),
                },
            )
            raise
```

- [ ] **Step 5: Document the local trace directory**

```env
# .env.example
DEEPSEEK_API_KEY=
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
MEAL_CHAT_TRACE_DIR=logs/meal_chat
```

```md
# README.md
## Meal chat trace logs

Backend conversational meal planning now writes per-session debug traces to:

`logs/meal_chat/YYYY-MM-DD/<session_id>.jsonl`

Each line is one JSON record and contains:

- session start events
- successful turn processing events
- failed turn processing events with exception text
- extractor debug metadata such as `expected_slot`, raw model response, and whether fallback parsing was applied
```

- [ ] **Step 6: Run tests to verify the trace writer passes**

Run: `uv run pytest tests/meal_chat/test_local_trace.py -v`

Expected: PASS.

- [ ] **Step 7: Commit the local trace logging work**

```bash
git add src/intelligent_meal_planner/meal_chat/local_trace.py src/intelligent_meal_planner/api/services.py tests/meal_chat/test_local_trace.py .env.example README.md
git commit -m "feat: add local meal chat trace logging"
```

### Task 4: Verify The Full Backend Flow Before Hand-off

**Files:**
- Test: `tests/meal_chat/test_orchestrator.py`
- Test: `tests/meal_chat/test_deepseek_extractor.py`
- Test: `tests/meal_chat/test_local_trace.py`
- Test: `tests/api/test_meal_chat_router.py`

- [ ] **Step 1: Run the focused meal-chat backend suite**

Run: `uv run pytest tests/meal_chat/test_orchestrator.py tests/meal_chat/test_deepseek_extractor.py tests/meal_chat/test_local_trace.py tests/api/test_meal_chat_router.py -v`

Expected:
- all meal-chat unit and router tests PASS
- no regression on session create / send message router responses

- [ ] **Step 2: Run one manual API smoke test**

Run: `uv run python main.py api`

Expected:
- API starts successfully
- create a session from `/api/meal-chat/sessions`
- send these turns in order:
  - `我想减脂`
  - `100元`
  - `没有，都能吃`
- after the third turn, assistant should ask the taste-preference question instead of repeating the restriction question
- a trace file should exist under `logs/meal_chat/<today>/<session_id>.jsonl`

- [ ] **Step 3: Inspect the generated trace file**

Run: `Get-Content -Raw "logs\\meal_chat\\$(Get-Date -Format 'yyyy-MM-dd')\\<session_id>.jsonl"`

Expected:
- at least one `session_started` record
- at least one `turn_processed` record
- `payload.trace.expected_slot` equals `"restrictions"` on the “没有，都能吃” turn
- `payload.trace.parsed_turn.debug.fallback_applied` is `true` if the LLM returned an empty restriction parse

- [ ] **Step 4: Commit the verification checkpoint**

```bash
git add .
git commit -m "chore: verify meal chat stuck fix and local tracing"
```
