# Meal Chat Slot Normalization Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent the meal chat from repeating questions after the user already answered a slot, even when the extractor returns that slot in the wrong update bucket.

**Architecture:** Keep the fix inside the meal chat parsing/orchestration boundary. Normalize extracted slot fields before `ParsedTurn` is consumed, then guard profile writes so non-profile fields cannot be silently attached to the `User` object and mask future parsing mistakes.

**Tech Stack:** Python, Pydantic, LangChain OpenAI-compatible client, pytest

---

### Task 1: Lock the regression with failing tests

**Files:**
- Modify: `tests/meal_chat/test_deepseek_extractor.py`
- Modify: `tests/meal_chat/test_orchestrator.py`

- [ ] **Step 1: Write the failing extractor regression test**

```python
def test_parse_moves_budget_answer_into_preference_updates_when_expected_slot_is_budget():
    extractor = DeepSeekSlotExtractor.__new__(DeepSeekSlotExtractor)

    class FakeClient:
        def invoke(self, _messages):
            return SimpleNamespace(
                content='{"profile_updates": {"budget": "100元"}, "preference_updates": {}, "acknowledged_restrictions": false}'
            )

    extractor.client = FakeClient()

    parsed = extractor.parse("100元吧", expected_slot="budget")

    assert "budget" not in parsed.profile_updates
    assert parsed.preference_updates["budget"] == "100元"
```

- [ ] **Step 2: Run the extractor test and verify it fails**

Run: `uv run pytest tests/meal_chat/test_deepseek_extractor.py::test_parse_moves_budget_answer_into_preference_updates_when_expected_slot_is_budget -v`
Expected: FAIL because the current extractor preserves `budget` inside `profile_updates`.

- [ ] **Step 3: Write the failing orchestrator regression test**

```python
def test_orchestrator_advances_after_budget_answer_even_if_extractor_misclassifies_budget():
    parsed = ParsedTurn(
        profile_updates={"budget": "100元"},
        preference_updates={},
        acknowledged_restrictions=False,
    )
    orchestrator = MealChatOrchestrator(
        extractor=FakeExtractor(parsed),
        budget_guard=FakeBudgetGuard(True),
        planner=FakePlanner(),
    )
    user = _user(
        gender="male",
        age=24,
        height=175,
        weight=68,
        activity_level="moderate",
        health_goal=None,
    )
    session = _session(status="collecting_preferences")

    response = orchestrator.advance(user, session, "100元吧")

    assert response["assistant_message"] != "这次你希望我把一天三餐预算控制在多少元以内？"
    assert session.collected_slots["budget"] == "100元"
```

- [ ] **Step 4: Run the orchestrator test and verify it fails**

Run: `uv run pytest tests/meal_chat/test_orchestrator.py::test_orchestrator_advances_after_budget_answer_even_if_extractor_misclassifies_budget -v`
Expected: FAIL because the current orchestrator only merges `preference_updates` into `session.collected_slots`.

### Task 2: Implement the minimal normalization fix

**Files:**
- Modify: `src/intelligent_meal_planner/meal_chat/deepseek_extractor.py`
- Modify: `src/intelligent_meal_planner/meal_chat/orchestrator.py`

- [ ] **Step 1: Normalize misclassified slot fields in the extractor**

```python
PROFILE_FIELD_NAMES = {"gender", "age", "height", "weight", "activity_level"}
PREFERENCE_FIELD_NAMES = {"health_goal", "budget", "disliked_foods", "preferred_tags", "restrictions_answered"}


def _normalize_payload(self, payload: dict, expected_slot: str | None) -> dict:
    profile_updates = dict(payload.get("profile_updates") or {})
    preference_updates = dict(payload.get("preference_updates") or {})

    for field in tuple(profile_updates):
        if field in PREFERENCE_FIELD_NAMES:
            preference_updates.setdefault(field, profile_updates.pop(field))

    if expected_slot in PREFERENCE_FIELD_NAMES and expected_slot in profile_updates:
        preference_updates.setdefault(expected_slot, profile_updates.pop(expected_slot))

    payload["profile_updates"] = profile_updates
    payload["preference_updates"] = preference_updates
    return payload
```

- [ ] **Step 2: Call normalization before building `ParsedTurn`**

```python
payload = json.loads(json_match.group(0) if json_match else raw)
payload = self._normalize_payload(payload, expected_slot)
payload, fallback_applied = self._apply_slot_fallback(payload, user_message, expected_slot)
```

- [ ] **Step 3: Guard profile writes in the orchestrator**

```python
for field, value in parsed.profile_updates.items():
    if field not in PROFILE_FIELDS:
        continue
    if value not in (None, ""):
        setattr(user, field, value)
```

- [ ] **Step 4: Keep the change minimal and scoped**

Do not refactor unrelated meal chat flow. Leave planner, budget guard, and router behavior unchanged.

### Task 3: Verify and commit

**Files:**
- Review: `src/intelligent_meal_planner/meal_chat/deepseek_extractor.py`
- Review: `src/intelligent_meal_planner/meal_chat/orchestrator.py`
- Review: `tests/meal_chat/test_deepseek_extractor.py`
- Review: `tests/meal_chat/test_orchestrator.py`

- [ ] **Step 1: Run focused meal chat tests**

Run: `uv run pytest tests/meal_chat/test_deepseek_extractor.py tests/meal_chat/test_orchestrator.py -v`
Expected: PASS with the new regression tests included.

- [ ] **Step 2: Run the API meal chat router tests**

Run: `uv run pytest tests/api/test_meal_chat_router.py -v`
Expected: PASS to confirm the public meal chat endpoint still behaves correctly.

- [ ] **Step 3: Inspect the diff**

Run: `git diff -- src/intelligent_meal_planner/meal_chat/deepseek_extractor.py src/intelligent_meal_planner/meal_chat/orchestrator.py tests/meal_chat/test_deepseek_extractor.py tests/meal_chat/test_orchestrator.py docs/superpowers/plans/2026-04-02-fix-meal-chat-slot-normalization.md`
Expected: Only the intended slot normalization, profile guard, tests, and plan doc changes appear.

- [ ] **Step 4: Commit the verified fix**

```bash
git add docs/superpowers/plans/2026-04-02-fix-meal-chat-slot-normalization.md \
    src/intelligent_meal_planner/meal_chat/deepseek_extractor.py \
    src/intelligent_meal_planner/meal_chat/orchestrator.py \
    tests/meal_chat/test_deepseek_extractor.py \
    tests/meal_chat/test_orchestrator.py
git commit -m "fix: normalize meal chat slot extraction"
```
