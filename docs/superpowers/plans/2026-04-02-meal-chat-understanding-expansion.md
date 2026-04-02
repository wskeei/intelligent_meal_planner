# Meal Chat Understanding Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade meal chat into an AI-first understanding pipeline that can absorb broad freeform user language, normalize it into canonical nutrition facts, judge confidence and missing information, ask nutritionist-style clarifying questions, and only enter negotiation/planning when the conversation is actually ready.

**Architecture:** Keep the frontend talking to one nutritionist assistant and preserve the current session API shape, but refactor backend turn handling into five explicit understanding stages: extraction, normalization, analysis, follow-up strategy, and planning readiness. Use DeepSeek for broad semantic extraction, deterministic normalizers for canonical schema and safety, an analyzer for confidence/missing/contradiction detection, and a question strategy layer that turns analysis output into focused follow-up prompts instead of generic fallback replies.

**Tech Stack:** Python, FastAPI, Pydantic, LangChain OpenAI-compatible chat client, pytest, Vue 3, TypeScript

---

### File Map

**Create**
- `src/intelligent_meal_planner/meal_chat/understanding_schema.py` — typed models for extraction output, canonical facts, analysis result, and follow-up plans
- `src/intelligent_meal_planner/meal_chat/semantic_normalizer.py` — canonical normalization of goals, budgets, foods, preferred tags, contradictions, and freeform lists
- `src/intelligent_meal_planner/meal_chat/understanding_analyzer.py` — compute readiness, confidence band, missing fields, contradiction flags, and clarification targets
- `src/intelligent_meal_planner/meal_chat/question_strategy.py` — map analysis result into nutritionist-style clarifying prompts and assistant-side summaries
- `tests/meal_chat/test_semantic_normalizer.py` — regression coverage for natural-language normalization
- `tests/meal_chat/test_understanding_analyzer.py` — regression coverage for readiness, confidence, and missing-field logic
- `tests/meal_chat/test_question_strategy.py` — regression coverage for follow-up prompt generation

**Modify**
- `src/intelligent_meal_planner/meal_chat/types.py` — expand parsed turn / debug types
- `src/intelligent_meal_planner/meal_chat/session_schema.py` — store richer understanding state, confidence history, and clarification queue
- `src/intelligent_meal_planner/meal_chat/deepseek_extractor.py` — request richer AI extraction payload and normalize model output shape
- `src/intelligent_meal_planner/meal_chat/crew_runtime.py` — orchestrate extraction → normalization → analysis → follow-up → negotiation/planning
- `src/intelligent_meal_planner/meal_chat/orchestrator.py` — persist richer trace payload and clarification metadata
- `src/intelligent_meal_planner/api/services.py` — inject the upgraded runtime dependencies and serialize richer session memory
- `src/intelligent_meal_planner/api/schemas.py` — optionally allow richer trace metadata if needed by future clients
- `tests/meal_chat/test_crew_runtime.py` — end-to-end runtime coverage for broad language, ambiguity, and follow-ups
- `tests/meal_chat/test_deepseek_extractor.py` — extractor coverage for confidence / missing fields / malformed payloads
- `tests/meal_chat/test_orchestrator.py` — persistence and session trace coverage for clarification states
- `tests/api/test_meal_chat_router.py` — route-level coverage that clarifying turns remain recoverable
- `README.md` — document the new understanding pipeline and clarification behavior

---

### Task 1: Add typed understanding models and richer session memory

**Files:**
- Create: `src/intelligent_meal_planner/meal_chat/understanding_schema.py`
- Modify: `src/intelligent_meal_planner/meal_chat/session_schema.py`
- Modify: `src/intelligent_meal_planner/meal_chat/types.py`
- Test: `tests/meal_chat/test_crew_runtime.py`

- [ ] **Step 1: Write the failing schema-oriented regression test**

```python
from intelligent_meal_planner.meal_chat.session_schema import ConversationMemory


def test_conversation_memory_can_store_analysis_and_follow_up_state():
    memory = ConversationMemory(
        phase="discovering",
        known_facts={
            "preference_confidence": 0.42,
            "missing_fields": ["budget"],
            "clarification_reason": "low_confidence",
        },
        open_questions=["budget", "health_goal"],
    )

    payload = memory.model_dump(mode="json")

    assert payload["known_facts"]["preference_confidence"] == 0.42
    assert payload["known_facts"]["missing_fields"] == ["budget"]
    assert payload["open_questions"] == ["budget", "health_goal"]
```

- [ ] **Step 2: Run the targeted test to verify current behavior is missing required structure**

Run: `uv run pytest tests/meal_chat/test_crew_runtime.py::test_conversation_memory_can_store_analysis_and_follow_up_state -v`

Expected: FAIL because the test does not exist yet and the current understanding state is too loosely modeled.

- [ ] **Step 3: Create explicit understanding schema models**

```python
from __future__ import annotations

from pydantic import BaseModel, Field


class CanonicalPreferences(BaseModel):
    health_goal: str | None = None
    budget: float | None = None
    disliked_foods: list[str] = Field(default_factory=list)
    preferred_tags: list[str] = Field(default_factory=list)


class UnderstandingAnalysis(BaseModel):
    confidence: float
    missing_fields: list[str] = Field(default_factory=list)
    contradiction_fields: list[str] = Field(default_factory=list)
    clarification_reason: str | None = None
    ready_for_negotiation: bool = False


class FollowUpPlan(BaseModel):
    questions: list[str] = Field(default_factory=list)
    assistant_message: str
```

- [ ] **Step 4: Extend `ConversationMemory` and `ParsedTurn` to hold richer understanding state**

```python
class ConversationMemory(BaseModel):
    phase: str = "discovering"
    profile: dict = Field(default_factory=dict)
    preferences: dict = Field(default_factory=dict)
    known_facts: dict = Field(default_factory=dict)
    open_questions: list[str] = Field(default_factory=list)
    target_ranges: TargetRanges | None = None
    negotiation_options: list[NegotiationOption] = Field(default_factory=list)
    clarification_history: list[dict] = Field(default_factory=list)


class ParsedTurn(BaseModel):
    profile_updates: dict = Field(default_factory=dict)
    preference_updates: dict = Field(default_factory=dict)
    acknowledged_restrictions: bool = False
    confidence: float | None = None
    missing_fields: list[str] = Field(default_factory=list)
    contradiction_fields: list[str] = Field(default_factory=list)
    debug: ExtractionDebug = Field(default_factory=ExtractionDebug)
```

- [ ] **Step 5: Run the regression test to verify the richer state now serializes cleanly**

Run: `uv run pytest tests/meal_chat/test_crew_runtime.py::test_conversation_memory_can_store_analysis_and_follow_up_state -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/intelligent_meal_planner/meal_chat/understanding_schema.py \
    src/intelligent_meal_planner/meal_chat/session_schema.py \
    src/intelligent_meal_planner/meal_chat/types.py \
    tests/meal_chat/test_crew_runtime.py
git commit -m "feat: add typed meal chat understanding state"
```

---

### Task 2: Build a semantic normalizer for broad freeform language

**Files:**
- Create: `src/intelligent_meal_planner/meal_chat/semantic_normalizer.py`
- Test: `tests/meal_chat/test_semantic_normalizer.py`

- [ ] **Step 1: Write the failing normalization tests**

```python
from intelligent_meal_planner.meal_chat.semantic_normalizer import (
    normalize_budget,
    normalize_goal,
    normalize_preference_lists,
)


def test_normalize_budget_understands_freeform_chinese_budget_phrases():
    assert normalize_budget("控制在两百以内") == 200.0
    assert normalize_budget("预算别太贵，150左右") == 150.0
    assert normalize_budget("一百五上下都可以") == 150.0


def test_normalize_goal_understands_colloquial_goal_phrases():
    assert normalize_goal("最近想把体脂往下压一点") == "lose_weight"
    assert normalize_goal("练壮一点，蛋白得跟上") == "gain_muscle"
    assert normalize_goal("先稳住别掉秤") == "maintain"


def test_normalize_preference_lists_deduplicates_and_canonicalizes():
    normalized = normalize_preference_lists(
        disliked_foods="香菜, 芹菜, 香菜",
        preferred_tags=["清爽", "清淡", "高蛋白"],
    )

    assert normalized["disliked_foods"] == ["香菜", "芹菜"]
    assert normalized["preferred_tags"] == ["清淡", "高蛋白"]
```

- [ ] **Step 2: Run the new normalizer tests to verify they fail**

Run: `uv run pytest tests/meal_chat/test_semantic_normalizer.py -v`

Expected: FAIL because `semantic_normalizer.py` does not exist.

- [ ] **Step 3: Implement canonical normalization helpers**

```python
GOAL_ALIASES = {
    "lose_weight": ("减肥", "减脂", "瘦一点", "控脂", "把体脂压下去"),
    "gain_muscle": ("增肌", "练壮一点", "练厚一点", "长肌肉"),
    "maintain": ("维持", "保持", "先稳住", "不想明显增减"),
    "healthy": ("健康饮食", "吃干净点", "均衡一点"),
}

TAG_ALIASES = {
    "清爽": "清淡",
    "清淡": "清淡",
    "高蛋白": "高蛋白",
    "蛋白高一点": "高蛋白",
    "家常": "家常",
}


def normalize_goal(text: str | None) -> str | None:
    ...


def normalize_budget(value) -> float | None:
    ...


def normalize_preference_lists(disliked_foods, preferred_tags) -> dict:
    ...
```

- [ ] **Step 4: Cover Chinese numerals and approximate budget phrases**

```python
def parse_chinese_amount(text: str) -> int:
    digits = {"零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    units = {"十": 10, "百": 100, "千": 1000, "万": 10000}
    ...


def normalize_budget(value) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if not value:
        return None
    text = str(value)
    ...
```

- [ ] **Step 5: Run the normalizer tests to verify they pass**

Run: `uv run pytest tests/meal_chat/test_semantic_normalizer.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/intelligent_meal_planner/meal_chat/semantic_normalizer.py \
    tests/meal_chat/test_semantic_normalizer.py
git commit -m "feat: add meal chat semantic normalizer"
```

---

### Task 3: Upgrade AI extraction to return confidence, missing fields, and contradictions

**Files:**
- Modify: `src/intelligent_meal_planner/meal_chat/deepseek_extractor.py`
- Modify: `src/intelligent_meal_planner/meal_chat/types.py`
- Test: `tests/meal_chat/test_deepseek_extractor.py`

- [ ] **Step 1: Write the failing extractor regression test for richer AI output**

```python
from types import SimpleNamespace

from intelligent_meal_planner.meal_chat.deepseek_extractor import DeepSeekSlotExtractor


def test_parse_normalizes_confidence_missing_and_contradictions():
    extractor = DeepSeekSlotExtractor.__new__(DeepSeekSlotExtractor)

    class FakeClient:
        def invoke(self, _messages):
            return SimpleNamespace(
                content=(
                    '{"profile_updates": {}, "preference_updates": {"health_goal": "减脂"}, '
                    '"acknowledged_restrictions": false, "confidence": 0.66, '
                    '"missing_fields": ["budget"], "contradiction_fields": ["health_goal"]}'
                )
            )

    extractor.client = FakeClient()

    parsed = extractor.parse("最近想减脂，但预算还没想好", expected_slot=None)

    assert parsed.confidence == 0.66
    assert parsed.missing_fields == ["budget"]
    assert parsed.contradiction_fields == ["health_goal"]
```

- [ ] **Step 2: Run the extractor tests to verify they fail**

Run: `uv run pytest tests/meal_chat/test_deepseek_extractor.py -v`

Expected: FAIL because `contradiction_fields` is not normalized yet.

- [ ] **Step 3: Expand the system prompt and payload normalization**

```python
SYSTEM_PROMPT = """
你是配餐对话信息提取器。
只提取结构化事实，不生成建议。
返回 JSON:
{
  "profile_updates": {},
  "preference_updates": {},
  "acknowledged_restrictions": false,
  "confidence": 0.0,
  "missing_fields": [],
  "contradiction_fields": []
}
...
"""
```

- [ ] **Step 4: Normalize richer metadata**

```python
ALLOWED_MISSING_FIELDS = PROFILE_FIELDS | {"health_goal", "budget", "disliked_foods", "preferred_tags"}
ALLOWED_CONTRADICTION_FIELDS = {"health_goal", "budget", "disliked_foods", "preferred_tags", "activity_level"}


def _normalize_payload(self, payload: dict, expected_slot: str | None) -> dict:
    ...
    payload["confidence"] = max(0.0, min(1.0, float(confidence))) if isinstance(confidence, (int, float)) else None
    payload["missing_fields"] = [field for field in missing_fields if field in ALLOWED_MISSING_FIELDS]
    payload["contradiction_fields"] = [field for field in contradiction_fields if field in ALLOWED_CONTRADICTION_FIELDS]
    ...
```

- [ ] **Step 5: Run the extractor tests to verify they pass**

Run: `uv run pytest tests/meal_chat/test_deepseek_extractor.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/intelligent_meal_planner/meal_chat/deepseek_extractor.py \
    src/intelligent_meal_planner/meal_chat/types.py \
    tests/meal_chat/test_deepseek_extractor.py
git commit -m "feat: enrich meal chat ai extraction metadata"
```

---

### Task 4: Add an analyzer that decides readiness, ambiguity, and missing information

**Files:**
- Create: `src/intelligent_meal_planner/meal_chat/understanding_analyzer.py`
- Test: `tests/meal_chat/test_understanding_analyzer.py`

- [ ] **Step 1: Write the failing analyzer tests**

```python
from intelligent_meal_planner.meal_chat.session_schema import ConversationMemory
from intelligent_meal_planner.meal_chat.understanding_analyzer import analyze_understanding


def test_analyze_understanding_requests_budget_when_goal_is_known_but_budget_missing():
    memory = ConversationMemory(
        phase="discovering",
        profile={
            "gender": "male",
            "age": 25,
            "height": 170.0,
            "weight": 65.0,
            "activity_level": "moderate",
        },
        preferences={"health_goal": "lose_weight"},
    )

    analysis = analyze_understanding(memory=memory, confidence=0.82, extracted_missing_fields=[])

    assert analysis.missing_fields == ["budget"]
    assert analysis.ready_for_negotiation is False
    assert analysis.clarification_reason == "missing_required_fields"


def test_analyze_understanding_blocks_planning_when_confidence_is_low():
    memory = ConversationMemory(
        phase="discovering",
        profile={
            "gender": "male",
            "age": 25,
            "height": 170.0,
            "weight": 65.0,
            "activity_level": "moderate",
        },
        preferences={"health_goal": "lose_weight", "budget": 180.0},
    )

    analysis = analyze_understanding(memory=memory, confidence=0.32, extracted_missing_fields=[])

    assert analysis.ready_for_negotiation is False
    assert analysis.clarification_reason == "low_confidence"
```

- [ ] **Step 2: Run the analyzer tests to verify they fail**

Run: `uv run pytest tests/meal_chat/test_understanding_analyzer.py -v`

Expected: FAIL because `understanding_analyzer.py` does not exist.

- [ ] **Step 3: Implement readiness and ambiguity analysis**

```python
from .understanding_schema import UnderstandingAnalysis

REQUIRED_PROFILE_FIELDS = ("gender", "age", "height", "weight", "activity_level")
REQUIRED_PREFERENCE_FIELDS = ("health_goal", "budget")
LOW_CONFIDENCE_THRESHOLD = 0.55


def analyze_understanding(memory: ConversationMemory, confidence: float, extracted_missing_fields: list[str], contradiction_fields: list[str] | None = None) -> UnderstandingAnalysis:
    missing_fields = list(dict.fromkeys(extracted_missing_fields + _find_missing_fields(memory)))
    contradiction_fields = contradiction_fields or []
    ready = not missing_fields and not contradiction_fields and confidence >= LOW_CONFIDENCE_THRESHOLD
    if contradiction_fields:
        reason = "contradiction_detected"
    elif missing_fields:
        reason = "missing_required_fields"
    elif confidence < LOW_CONFIDENCE_THRESHOLD:
        reason = "low_confidence"
    else:
        reason = None
    return UnderstandingAnalysis(
        confidence=round(confidence, 2),
        missing_fields=missing_fields,
        contradiction_fields=contradiction_fields,
        clarification_reason=reason,
        ready_for_negotiation=ready,
    )
```

- [ ] **Step 4: Run the analyzer tests to verify they pass**

Run: `uv run pytest tests/meal_chat/test_understanding_analyzer.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/intelligent_meal_planner/meal_chat/understanding_analyzer.py \
    tests/meal_chat/test_understanding_analyzer.py
git commit -m "feat: add meal chat understanding analyzer"
```

---

### Task 5: Add a nutritionist-style follow-up question strategy

**Files:**
- Create: `src/intelligent_meal_planner/meal_chat/question_strategy.py`
- Test: `tests/meal_chat/test_question_strategy.py`

- [ ] **Step 1: Write the failing follow-up strategy tests**

```python
from intelligent_meal_planner.meal_chat.question_strategy import build_follow_up_plan
from intelligent_meal_planner.meal_chat.session_schema import ConversationMemory
from intelligent_meal_planner.meal_chat.understanding_schema import UnderstandingAnalysis


def test_build_follow_up_plan_asks_for_budget_with_nutritionist_tone():
    memory = ConversationMemory(
        preferences={"health_goal": "lose_weight"},
    )
    analysis = UnderstandingAnalysis(
        confidence=0.82,
        missing_fields=["budget"],
        contradiction_fields=[],
        clarification_reason="missing_required_fields",
        ready_for_negotiation=False,
    )

    follow_up = build_follow_up_plan(memory=memory, analysis=analysis)

    assert follow_up.questions == ["budget"]
    assert "预算" in follow_up.assistant_message
    assert "方案" in follow_up.assistant_message


def test_build_follow_up_plan_confirms_low_confidence_instead_of_assuming():
    memory = ConversationMemory(
        preferences={"health_goal": "lose_weight", "budget": 180.0},
    )
    analysis = UnderstandingAnalysis(
        confidence=0.35,
        missing_fields=[],
        contradiction_fields=[],
        clarification_reason="low_confidence",
        ready_for_negotiation=False,
    )

    follow_up = build_follow_up_plan(memory=memory, analysis=analysis)

    assert "我先确认一下" in follow_up.assistant_message
    assert "180" in follow_up.assistant_message
```

- [ ] **Step 2: Run the follow-up strategy tests to verify they fail**

Run: `uv run pytest tests/meal_chat/test_question_strategy.py -v`

Expected: FAIL because `question_strategy.py` does not exist.

- [ ] **Step 3: Implement follow-up planning**

```python
from .understanding_schema import FollowUpPlan, UnderstandingAnalysis

QUESTION_PROMPTS = {
    "budget": "你一天的预算大概想控制在多少？这样我才能判断食材密度和蛋白空间。",
    "health_goal": "这次你更想减脂、增肌，还是先维持住？",
    "activity_level": "你平时活动量怎么样，久坐还是会训练？",
}


def build_follow_up_plan(memory: ConversationMemory, analysis: UnderstandingAnalysis) -> FollowUpPlan:
    if analysis.missing_fields:
        questions = analysis.missing_fields[:2]
        prompt = "我先补齐两个关键点，这样后面的分析和配餐会更准。 " + " ".join(
            QUESTION_PROMPTS[field] for field in questions
        )
        return FollowUpPlan(questions=questions, assistant_message=prompt)

    if analysis.clarification_reason == "low_confidence":
        return FollowUpPlan(
            questions=["health_goal", "budget"],
            assistant_message=(
                f"我先确认一下，我现在是按“{memory.preferences.get('health_goal')}”和 "
                f"{memory.preferences.get('budget')} 元预算理解的，对吗？"
            ),
        )

    return FollowUpPlan(questions=[], assistant_message="我们可以继续往下分析。")
```

- [ ] **Step 4: Run the follow-up strategy tests to verify they pass**

Run: `uv run pytest tests/meal_chat/test_question_strategy.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/intelligent_meal_planner/meal_chat/question_strategy.py \
    tests/meal_chat/test_question_strategy.py
git commit -m "feat: add nutritionist follow-up strategy"
```

---

### Task 6: Wire the full understanding pipeline into the runtime and persistence flow

**Files:**
- Modify: `src/intelligent_meal_planner/meal_chat/crew_runtime.py`
- Modify: `src/intelligent_meal_planner/meal_chat/orchestrator.py`
- Modify: `src/intelligent_meal_planner/api/services.py`
- Modify: `tests/meal_chat/test_crew_runtime.py`
- Modify: `tests/meal_chat/test_orchestrator.py`
- Modify: `tests/api/test_meal_chat_router.py`

- [ ] **Step 1: Write the failing runtime/orchestrator regression tests**

```python
def test_runtime_tracks_missing_fields_and_asks_nutritionist_follow_up():
    extractor = FakeExtractor(
        parsed_turn=ParsedTurn(
            preference_updates={"health_goal": "lose_weight"},
            confidence=0.88,
            missing_fields=["budget"],
        )
    )
    runtime = CrewMealChatRuntime(planning_tool=None, extractor=extractor)

    result = runtime.run_turn(
        user_message="最近想把体脂降一点",
        memory=ConversationMemory(
            phase="discovering",
            profile={
                "gender": "male",
                "age": 25,
                "height": 170.0,
                "weight": 65.0,
                "activity_level": "moderate",
            },
            preferences={},
        ),
    )

    assert result.phase == "discovering"
    assert result.memory.open_questions == ["budget"]
    assert result.memory.known_facts["clarification_reason"] == "missing_required_fields"
    assert "预算" in result.assistant_message
```

- [ ] **Step 2: Run the focused regression tests to verify they fail if the pipeline is not fully wired**

Run: `uv run pytest tests/meal_chat/test_crew_runtime.py tests/meal_chat/test_orchestrator.py tests/api/test_meal_chat_router.py -v`

Expected: FAIL until the runtime persists analysis and clarification state end-to-end.

- [ ] **Step 3: Refactor runtime into explicit stages**

```python
def run_turn(self, user_message: str, memory: ConversationMemory) -> CrewTurnResult:
    intent = self.intent_agent(user_message=user_message, memory=memory)
    extracted = self.profile_agent(user_message=user_message, memory=memory, intent=intent)
    merged_memory = self._merge_memory(memory, extracted)

    analysis = analyze_understanding(
        memory=merged_memory,
        confidence=float(extracted.get("confidence", 0.3)),
        extracted_missing_fields=extracted.get("missing_fields", []),
        contradiction_fields=extracted.get("contradiction_fields", []),
    )
    merged_memory.known_facts["preference_confidence"] = analysis.confidence
    merged_memory.known_facts["missing_fields"] = analysis.missing_fields
    merged_memory.known_facts["clarification_reason"] = analysis.clarification_reason
    merged_memory.open_questions = analysis.missing_fields

    if not analysis.ready_for_negotiation:
        follow_up = build_follow_up_plan(memory=merged_memory, analysis=analysis)
        merged_memory.phase = "discovering"
        return CrewTurnResult(
            phase="discovering",
            assistant_message=follow_up.assistant_message,
            memory=merged_memory,
        )

    ...
```

- [ ] **Step 4: Persist richer trace data through orchestrator and service**

```python
return {
    "status": result.phase,
    "assistant_message": result.assistant_message,
    "hidden_targets": None,
    "meal_plan": result.meal_plan,
    "trace": {
        "phase": result.phase,
        "memory": result.memory.model_dump(mode="json"),
        "negotiation_options": [...],
        "open_questions": result.memory.open_questions,
        "known_facts": result.memory.known_facts,
    },
}
```

- [ ] **Step 5: Run the runtime/orchestrator/router tests to verify they pass**

Run: `uv run pytest tests/meal_chat/test_crew_runtime.py tests/meal_chat/test_orchestrator.py tests/api/test_meal_chat_router.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/intelligent_meal_planner/meal_chat/crew_runtime.py \
    src/intelligent_meal_planner/meal_chat/orchestrator.py \
    src/intelligent_meal_planner/api/services.py \
    tests/meal_chat/test_crew_runtime.py \
    tests/meal_chat/test_orchestrator.py \
    tests/api/test_meal_chat_router.py
git commit -m "feat: add meal chat understanding pipeline"
```

---

### Task 7: Broaden broad-language support and ambiguity handling end to end

**Files:**
- Modify: `src/intelligent_meal_planner/meal_chat/semantic_normalizer.py`
- Modify: `src/intelligent_meal_planner/meal_chat/understanding_analyzer.py`
- Modify: `src/intelligent_meal_planner/meal_chat/question_strategy.py`
- Modify: `tests/meal_chat/test_semantic_normalizer.py`
- Modify: `tests/meal_chat/test_understanding_analyzer.py`
- Modify: `tests/meal_chat/test_question_strategy.py`

- [ ] **Step 1: Write failing coverage for contradictory and fuzzy inputs**

```python
def test_analyzer_detects_contradiction_when_user_says_gain_muscle_but_eat_less():
    memory = ConversationMemory(
        preferences={"health_goal": "gain_muscle"},
        known_facts={"raw_user_message": "想增肌，但最好吃少一点"},
    )

    analysis = analyze_understanding(
        memory=memory,
        confidence=0.77,
        extracted_missing_fields=[],
        contradiction_fields=["health_goal"],
    )

    assert analysis.clarification_reason == "contradiction_detected"
    assert analysis.ready_for_negotiation is False
```

- [ ] **Step 2: Run the broad-language understanding tests to verify they fail**

Run: `uv run pytest tests/meal_chat/test_semantic_normalizer.py tests/meal_chat/test_understanding_analyzer.py tests/meal_chat/test_question_strategy.py -v`

Expected: FAIL until contradiction and fuzzy-language handling is implemented.

- [ ] **Step 3: Expand canonical alias tables and contradiction heuristics**

```python
GOAL_ALIASES["lose_weight"] += ("吃少一点", "把体脂压下去", "控制热量")
GOAL_ALIASES["gain_muscle"] += ("练厚一点", "涨点围度", "更壮一点")

CONTRADICTION_RULES = {
    "gain_muscle": ("吃少一点", "热量压低", "别吃太多"),
    "lose_weight": ("多长点肉", "增肌期", "吃猛一点"),
}
```

- [ ] **Step 4: Generate better clarification messages for contradictions**

```python
if analysis.clarification_reason == "contradiction_detected":
    return FollowUpPlan(
        questions=["health_goal"],
        assistant_message=(
            "我听起来有一点矛盾：你像是在追求增肌，但又提到想把进食压低。"
            " 你这次更优先的是体脂下降，还是肌肉增长？"
        ),
    )
```

- [ ] **Step 5: Run the broad-language tests to verify they pass**

Run: `uv run pytest tests/meal_chat/test_semantic_normalizer.py tests/meal_chat/test_understanding_analyzer.py tests/meal_chat/test_question_strategy.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/intelligent_meal_planner/meal_chat/semantic_normalizer.py \
    src/intelligent_meal_planner/meal_chat/understanding_analyzer.py \
    src/intelligent_meal_planner/meal_chat/question_strategy.py \
    tests/meal_chat/test_semantic_normalizer.py \
    tests/meal_chat/test_understanding_analyzer.py \
    tests/meal_chat/test_question_strategy.py
git commit -m "feat: expand meal chat ambiguity handling"
```

---

### Task 8: Verify the complete understanding upgrade and document behavior

**Files:**
- Modify: `README.md`
- Review: `src/intelligent_meal_planner/meal_chat/crew_runtime.py`
- Review: `src/intelligent_meal_planner/meal_chat/deepseek_extractor.py`
- Review: `src/intelligent_meal_planner/meal_chat/semantic_normalizer.py`
- Review: `src/intelligent_meal_planner/meal_chat/understanding_analyzer.py`
- Review: `src/intelligent_meal_planner/meal_chat/question_strategy.py`
- Review: `src/intelligent_meal_planner/meal_chat/session_schema.py`
- Review: `tests/meal_chat/test_crew_runtime.py`

- [ ] **Step 1: Update README to document the understanding pipeline**

```md
## 对话理解升级

当前 meal chat 后端每轮会执行：

1. AI 提取用户本轮自由表达中的目标、预算、忌口和口味线索
2. 将提取结果归一化成标准字段与枚举
3. 计算理解置信度、关键缺失项和潜在语义冲突
4. 如果信息不足，则以营养师语气进行追问
5. 信息充分后才进入预算协商与强化学习配餐
```

- [ ] **Step 2: Run the full backend test suite**

Run: `uv run pytest -v`

Expected: PASS.

- [ ] **Step 3: Run lint and formatting checks on touched backend files**

Run: `uv run ruff check src/intelligent_meal_planner/meal_chat src/intelligent_meal_planner/api tests/meal_chat tests/api/test_meal_chat_router.py`

Expected: `All checks passed!`

Run: `uv run black --check src/intelligent_meal_planner/meal_chat src/intelligent_meal_planner/api tests/meal_chat tests/api/test_meal_chat_router.py`

Expected: `would be left unchanged`

- [ ] **Step 4: Inspect the final diff**

Run: `git diff -- README.md src/intelligent_meal_planner/meal_chat src/intelligent_meal_planner/api/services.py tests/meal_chat tests/api/test_meal_chat_router.py`

Expected: Only the understanding pipeline expansion, follow-up strategy, richer AI extraction, and related tests/docs are present.

- [ ] **Step 5: Commit**

```bash
git add README.md \
    src/intelligent_meal_planner/meal_chat \
    src/intelligent_meal_planner/api/services.py \
    tests/meal_chat \
    tests/api/test_meal_chat_router.py
git commit -m "feat: broaden meal chat ai understanding pipeline"
```

