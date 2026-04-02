# CrewAI Meal Chat Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the rigid slot-by-slot meal chat with a single-persona nutritionist chat powered by internal CrewAI multi-agent coordination, range-based nutrition targets, and budget negotiation that ends in RL-generated meal plans.

**Architecture:** Keep the frontend talking to one assistant while the backend runs a CrewAI pipeline per turn: intent routing, profile consolidation, target-range derivation, budget/feasibility reasoning, and RL planning. Replace the current absorbing `budget_rejected` flow with recoverable conversation phases so users can ask questions, revise budgets, and receive two negotiable candidate plans instead of getting stuck in a loop.

**Tech Stack:** Python, FastAPI, SQLAlchemy, Pydantic, CrewAI, pytest, Vue 3, TypeScript

---

### File Map

**Create**
- `src/intelligent_meal_planner/meal_chat/session_schema.py` — typed session memory, conversation phases, pending questions, negotiation state, structured agent outputs
- `src/intelligent_meal_planner/meal_chat/target_ranges.py` — map user profile and goal into nutrition ranges instead of exact macro points
- `src/intelligent_meal_planner/meal_chat/feasibility_negotiator.py` — explain budget pressure, compute recommended budget bands, and assemble two negotiation strategies
- `src/intelligent_meal_planner/meal_chat/crew_runtime.py` — CrewAI agents, tasks, output parsing, and single-turn orchestration
- `tests/meal_chat/test_target_ranges.py` — regression tests for range targets
- `tests/meal_chat/test_feasibility_negotiator.py` — regression tests for budget recommendation and fallback dual-plan decisions
- `tests/meal_chat/test_crew_runtime.py` — regression tests for intent routing, negotiation, and assistant reply synthesis

**Modify**
- `src/intelligent_meal_planner/meal_chat/orchestrator.py` — replace rigid `next_question_key` logic with crew-driven session advancement
- `src/intelligent_meal_planner/api/services.py` — persist typed session memory, wire in crew runtime, serialize richer session states, and support dual-plan results
- `src/intelligent_meal_planner/db/models.py` — widen `MealChatSession` JSON usage to store memory and negotiation artifacts while preserving current table
- `src/intelligent_meal_planner/api/schemas.py` — update response models for new statuses and optional plan alternatives
- `frontend/src/api/index.ts` — relax hard-coded status union and surface dual-plan payload shape
- `frontend/src/views/MealPlanView.vue` — handle new conversation phases and dual-plan assistant messages without assuming `budget_rejected`
- `tests/api/test_meal_chat_router.py` — route-level coverage for recoverable negotiation states
- `tests/meal_chat/test_orchestrator.py` — replace old slot-order assumptions with crew-driven behavior tests
- `README.md` — document new chat behavior and status meanings

---

### Task 1: Add typed conversation memory and range targets

**Files:**
- Create: `src/intelligent_meal_planner/meal_chat/session_schema.py`
- Create: `src/intelligent_meal_planner/meal_chat/target_ranges.py`
- Modify: `src/intelligent_meal_planner/db/models.py`
- Test: `tests/meal_chat/test_target_ranges.py`

- [ ] **Step 1: Write the failing target-range tests**

```python
from intelligent_meal_planner.meal_chat.target_ranges import build_target_ranges


def test_build_target_ranges_for_weight_loss_returns_ranges_not_point_values():
    ranges = build_target_ranges(
        profile={
            "gender": "male",
            "age": 30,
            "height": 175,
            "weight": 82,
            "activity_level": "moderate",
        },
        goal="lose_weight",
    )

    assert ranges.calories_min < ranges.calories_max
    assert ranges.protein_min < ranges.protein_max
    assert ranges.strategy == "fat_loss"
    assert 1600 <= ranges.calories_min <= 2400


def test_build_target_ranges_uses_safe_defaults_when_profile_missing():
    ranges = build_target_ranges(
        profile={
            "gender": None,
            "age": None,
            "height": None,
            "weight": None,
            "activity_level": None,
        },
        goal="healthy",
    )

    assert ranges.calories_min >= 1200
    assert ranges.calories_max <= 2600
    assert ranges.protein_min >= 60
```

- [ ] **Step 2: Run the target-range tests to verify they fail**

Run: `uv run pytest tests/meal_chat/test_target_ranges.py -v`
Expected: FAIL because `build_target_ranges` does not exist.

- [ ] **Step 3: Create typed session memory and range models**

```python
from pydantic import BaseModel, Field


class TargetRanges(BaseModel):
    calories_min: int
    calories_max: int
    protein_min: int
    protein_max: int
    carbs_min: int
    carbs_max: int
    fat_min: int
    fat_max: int
    strategy: str


class NegotiationOption(BaseModel):
    key: str
    title: str
    rationale: str
    budget: float
    preferred_tags: list[str] = Field(default_factory=list)


class ConversationMemory(BaseModel):
    phase: str = "discovering"
    profile: dict = Field(default_factory=dict)
    preferences: dict = Field(default_factory=dict)
    known_facts: dict = Field(default_factory=dict)
    open_questions: list[str] = Field(default_factory=list)
    target_ranges: TargetRanges | None = None
    negotiation_options: list[NegotiationOption] = Field(default_factory=list)
```

- [ ] **Step 4: Implement the range builder**

```python
from pydantic import BaseModel


class TargetRanges(BaseModel):
    calories_min: int
    calories_max: int
    protein_min: int
    protein_max: int
    carbs_min: int
    carbs_max: int
    fat_min: int
    fat_max: int
    strategy: str


def build_target_ranges(profile: dict, goal: str) -> TargetRanges:
    weight = float(profile.get("weight") or 70)
    height = float(profile.get("height") or 170)
    age = int(profile.get("age") or 30)
    gender = profile.get("gender") or "female"
    activity_level = profile.get("activity_level") or "light"

    base = (10 * weight) + (6.25 * height) - (5 * age)
    bmr = base + 5 if gender == "male" else base - 161
    activity_map = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }
    tdee = bmr * activity_map.get(activity_level, 1.375)

    if goal == "lose_weight":
        center = tdee - 450
        strategy = "fat_loss"
        protein_per_kg = (1.6, 2.0)
        fat_ratio = (0.20, 0.30)
    elif goal == "gain_muscle":
        center = tdee + 250
        strategy = "muscle_gain"
        protein_per_kg = (1.8, 2.2)
        fat_ratio = (0.20, 0.30)
    else:
        center = tdee
        strategy = "balanced"
        protein_per_kg = (1.2, 1.8)
        fat_ratio = (0.25, 0.35)

    calories_min = max(1200, int(round(center - 150)))
    calories_max = min(3000, int(round(center + 150)))
    protein_min = max(60, int(round(weight * protein_per_kg[0])))
    protein_max = min(220, int(round(weight * protein_per_kg[1])))
    fat_min = max(30, int(round(calories_min * fat_ratio[0] / 9)))
    fat_max = min(120, int(round(calories_max * fat_ratio[1] / 9)))
    carbs_min = max(50, int(round((calories_min - protein_max * 4 - fat_max * 9) / 4)))
    carbs_max = min(400, int(round((calories_max - protein_min * 4 - fat_min * 9) / 4)))

    return TargetRanges(
        calories_min=calories_min,
        calories_max=calories_max,
        protein_min=protein_min,
        protein_max=protein_max,
        carbs_min=carbs_min,
        carbs_max=carbs_max,
        fat_min=fat_min,
        fat_max=fat_max,
        strategy=strategy,
    )
```

- [ ] **Step 5: Run the target-range tests to verify they pass**

Run: `uv run pytest tests/meal_chat/test_target_ranges.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/intelligent_meal_planner/meal_chat/session_schema.py \
    src/intelligent_meal_planner/meal_chat/target_ranges.py \
    src/intelligent_meal_planner/db/models.py \
    tests/meal_chat/test_target_ranges.py
git commit -m "feat: add meal chat range targets and memory schema"
```

### Task 2: Add budget negotiation logic that returns recoverable options

**Files:**
- Create: `src/intelligent_meal_planner/meal_chat/feasibility_negotiator.py`
- Modify: `src/intelligent_meal_planner/api/feasibility.py`
- Test: `tests/meal_chat/test_feasibility_negotiator.py`

- [ ] **Step 1: Write the failing negotiation tests**

```python
from intelligent_meal_planner.meal_chat.feasibility_negotiator import build_negotiation_result
from intelligent_meal_planner.meal_chat.session_schema import TargetRanges


def test_build_negotiation_result_returns_two_options_when_budget_is_tight():
    ranges = TargetRanges(
        calories_min=1700,
        calories_max=1900,
        protein_min=110,
        protein_max=140,
        carbs_min=130,
        carbs_max=210,
        fat_min=40,
        fat_max=65,
        strategy="fat_loss",
    )

    result = build_negotiation_result(budget=100, target_ranges=ranges)

    assert result.phase == "negotiating"
    assert len(result.options) == 2
    assert {option.key for option in result.options} == {"budget_cut", "protein_priority"}
    assert "最低建议预算" in result.explanation


def test_build_negotiation_result_accepts_budget_when_ranges_are_feasible():
    ranges = TargetRanges(
        calories_min=1500,
        calories_max=1800,
        protein_min=60,
        protein_max=80,
        carbs_min=120,
        carbs_max=220,
        fat_min=35,
        fat_max=60,
        strategy="balanced",
    )

    result = build_negotiation_result(budget=150, target_ranges=ranges)

    assert result.phase == "planning"
    assert result.options == []
```

- [ ] **Step 2: Run the negotiation tests to verify they fail**

Run: `uv run pytest tests/meal_chat/test_feasibility_negotiator.py -v`
Expected: FAIL because `build_negotiation_result` does not exist.

- [ ] **Step 3: Add a recoverable negotiation result model**

```python
from pydantic import BaseModel, Field

from .session_schema import NegotiationOption, TargetRanges


class NegotiationResult(BaseModel):
    phase: str
    explanation: str
    recommended_budget_min: float
    recommended_budget_comfort: float
    options: list[NegotiationOption] = Field(default_factory=list)
```

- [ ] **Step 4: Implement the negotiation builder**

```python
def build_negotiation_result(budget: float, target_ranges: TargetRanges) -> NegotiationResult:
    protein_pressure = max(0, target_ranges.protein_min - 70)
    recommended_budget_min = max(float(budget), 80.0 + protein_pressure * 1.2)
    recommended_budget_comfort = recommended_budget_min + 30.0

    if budget >= recommended_budget_min:
        return NegotiationResult(
            phase="planning",
            explanation="当前预算可以进入正式配餐。",
            recommended_budget_min=recommended_budget_min,
            recommended_budget_comfort=recommended_budget_comfort,
            options=[],
        )

    return NegotiationResult(
        phase="negotiating",
        explanation=(
            f"按你当前目标，{budget:.0f} 元更适合做折中方案。"
            f" 最低建议预算约 {recommended_budget_min:.0f} 元，"
            f" 更从容的预算约 {recommended_budget_comfort:.0f} 元。"
        ),
        recommended_budget_min=recommended_budget_min,
        recommended_budget_comfort=recommended_budget_comfort,
        options=[
            NegotiationOption(
                key="budget_cut",
                title="保守减脂",
                rationale="优先控热量和预算，蛋白尽量高但允许略低。",
                budget=budget,
                preferred_tags=["light"],
            ),
            NegotiationOption(
                key="protein_priority",
                title="高蛋白优先",
                rationale="优先保蛋白，价格更贴近预算上限。",
                budget=max(budget, min(recommended_budget_min, recommended_budget_comfort)),
                preferred_tags=["high_protein"],
            ),
        ],
    )
```

- [ ] **Step 5: Run the negotiation tests to verify they pass**

Run: `uv run pytest tests/meal_chat/test_feasibility_negotiator.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/intelligent_meal_planner/meal_chat/feasibility_negotiator.py \
    src/intelligent_meal_planner/api/feasibility.py \
    tests/meal_chat/test_feasibility_negotiator.py
git commit -m "feat: add recoverable meal chat budget negotiation"
```

### Task 3: Add CrewAI runtime with internal agents and typed turn results

**Files:**
- Create: `src/intelligent_meal_planner/meal_chat/crew_runtime.py`
- Modify: `src/intelligent_meal_planner/meal_chat/types.py`
- Test: `tests/meal_chat/test_crew_runtime.py`

- [ ] **Step 1: Write the failing crew runtime tests**

```python
from intelligent_meal_planner.meal_chat.crew_runtime import CrewMealChatRuntime
from intelligent_meal_planner.meal_chat.session_schema import ConversationMemory


def test_runtime_routes_budget_question_to_negotiation_answer():
    runtime = CrewMealChatRuntime.__new__(CrewMealChatRuntime)
    runtime.intent_agent = lambda *_args, **_kwargs: {
        "intent": "budget_question",
        "needs_plan": False,
    }
    runtime.profile_agent = lambda *_args, **_kwargs: {
        "profile_updates": {},
        "preference_updates": {},
    }
    runtime.strategy_agent = lambda *_args, **_kwargs: {
        "target_ranges": None,
    }
    runtime.negotiator_agent = lambda *_args, **_kwargs: {
        "assistant_message": "按你现在的目标，最低建议预算大约 160 元。",
        "phase": "negotiating",
        "options": [],
    }

    result = runtime.run_turn(
        user_message="最低需要多少预算？",
        memory=ConversationMemory(phase="negotiating"),
    )

    assert result.phase == "negotiating"
    assert "最低建议预算" in result.assistant_message


def test_runtime_requests_plan_when_information_is_sufficient():
    runtime = CrewMealChatRuntime.__new__(CrewMealChatRuntime)
    runtime.intent_agent = lambda *_args, **_kwargs: {
        "intent": "plan_request",
        "needs_plan": True,
    }
    runtime.profile_agent = lambda *_args, **_kwargs: {
        "profile_updates": {},
        "preference_updates": {"budget": 200.0},
    }
    runtime.strategy_agent = lambda *_args, **_kwargs: {
        "target_ranges": {
            "calories_min": 1700,
            "calories_max": 1900,
            "protein_min": 100,
            "protein_max": 130,
            "carbs_min": 140,
            "carbs_max": 220,
            "fat_min": 40,
            "fat_max": 65,
            "strategy": "fat_loss",
        },
    }
    runtime.negotiator_agent = lambda *_args, **_kwargs: {
        "phase": "planning",
        "assistant_message": "可以正式配餐。",
        "options": [],
    }
    runtime.planning_agent = lambda *_args, **_kwargs: {
        "phase": "finalized",
        "assistant_message": "我给你整理了两套方案。",
        "meal_plan": {"primary": {}, "alternatives": [{}, {}]},
    }

    result = runtime.run_turn(
        user_message="那直接给我方案吧",
        memory=ConversationMemory(phase="discovering"),
    )

    assert result.phase == "finalized"
    assert result.meal_plan is not None
```

- [ ] **Step 2: Run the crew runtime tests to verify they fail**

Run: `uv run pytest tests/meal_chat/test_crew_runtime.py -v`
Expected: FAIL because `CrewMealChatRuntime` does not exist.

- [ ] **Step 3: Add a typed turn result model**

```python
from pydantic import BaseModel, Field

from .session_schema import ConversationMemory, NegotiationOption


class CrewTurnResult(BaseModel):
    phase: str
    assistant_message: str
    memory: ConversationMemory
    negotiation_options: list[NegotiationOption] = Field(default_factory=list)
    meal_plan: dict | None = None
```

- [ ] **Step 4: Implement the CrewAI runtime**

```python
class CrewMealChatRuntime:
    def __init__(self, planning_tool):
        self.planning_tool = planning_tool

    def run_turn(self, user_message: str, memory: ConversationMemory) -> CrewTurnResult:
        intent = self.intent_agent(user_message=user_message, memory=memory)
        profile_delta = self.profile_agent(user_message=user_message, memory=memory, intent=intent)
        merged_memory = self._merge_memory(memory, profile_delta)

        strategy = self.strategy_agent(memory=merged_memory)
        if strategy.get("target_ranges"):
            merged_memory.target_ranges = strategy["target_ranges"]

        negotiation = self.negotiator_agent(user_message=user_message, memory=merged_memory, intent=intent)
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
```

- [ ] **Step 5: Run the crew runtime tests to verify they pass**

Run: `uv run pytest tests/meal_chat/test_crew_runtime.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/intelligent_meal_planner/meal_chat/crew_runtime.py \
    src/intelligent_meal_planner/meal_chat/types.py \
    tests/meal_chat/test_crew_runtime.py
git commit -m "feat: add crew-based meal chat runtime"
```

### Task 4: Replace rigid orchestrator flow with recoverable crew-driven conversation

**Files:**
- Modify: `src/intelligent_meal_planner/meal_chat/orchestrator.py`
- Modify: `src/intelligent_meal_planner/api/services.py`
- Modify: `tests/meal_chat/test_orchestrator.py`
- Modify: `tests/api/test_meal_chat_router.py`

- [ ] **Step 1: Write the failing orchestration tests**

```python
def test_orchestrator_allows_budget_revision_after_negotiation():
    runtime = FakeCrewRuntime(
        result=CrewTurnResult(
            phase="planning",
            assistant_message="预算调到 200 元后，我可以继续给你两套方案。",
            memory=ConversationMemory(
                phase="planning",
                preferences={"budget": 200.0},
            ),
            meal_plan=None,
        )
    )
    orchestrator = MealChatOrchestrator(runtime=runtime, planner=FakePlanner())
    session = _session(
        status="negotiating",
        collected_slots={"budget": 100.0},
    )

    response = orchestrator.advance(_user(), session, "预算设置 200 元")

    assert response["status"] == "planning"
    assert "200 元" in response["assistant_message"]
    assert session.collected_slots["budget"] == 200.0


def test_router_returns_negotiating_status_without_error():
    fake_response = {
        "session_id": "session001",
        "status": "negotiating",
        "messages": [
            {"role": "assistant", "content": "当前预算偏紧，我先给你两个方向。"}
        ],
        "meal_plan": None,
    }
    monkeypatch.setattr(
        "intelligent_meal_planner.api.routers.meal_chat.meal_chat_app.handle_message",
        lambda db, user, session_id, content: fake_response,
    )
```

- [ ] **Step 2: Run the orchestrator and router tests to verify they fail**

Run: `uv run pytest tests/meal_chat/test_orchestrator.py tests/api/test_meal_chat_router.py -v`
Expected: FAIL because the current orchestrator still assumes rigid status values and fixed question order.

- [ ] **Step 3: Refactor the orchestrator constructor and session update path**

```python
class MealChatOrchestrator:
    def __init__(self, runtime, planner):
        self.runtime = runtime
        self.planner = planner

    def advance(self, user, session, user_message: str):
        memory = ConversationMemory.model_validate(session.collected_slots or {})
        result = self.runtime.run_turn(user_message=user_message, memory=memory)

        session.collected_slots = result.memory.model_dump(mode="json")
        session.status = result.phase

        return {
            "status": result.phase,
            "assistant_message": result.assistant_message,
            "hidden_targets": None,
            "meal_plan": result.meal_plan,
            "trace": {
                "phase": result.phase,
                "memory": result.memory.model_dump(mode="json"),
                "negotiation_options": [o.model_dump(mode="json") for o in result.negotiation_options],
            },
        }
```

- [ ] **Step 4: Update session bootstrap and serialization in the API service**

```python
def start_session(self, db: Session, user: User) -> Dict[str, Any]:
    memory = ConversationMemory(
        phase="discovering",
        profile={
            "gender": user.gender,
            "age": user.age,
            "height": user.height,
            "weight": user.weight,
            "activity_level": user.activity_level,
        },
        preferences={"health_goal": user.health_goal},
    )
    session = MealChatSession(
        id=str(uuid.uuid4())[:8],
        user_id=user.id,
        status="discovering",
        collected_slots=memory.model_dump(mode="json"),
    )
```

- [ ] **Step 5: Run the orchestrator and router tests to verify they pass**

Run: `uv run pytest tests/meal_chat/test_orchestrator.py tests/api/test_meal_chat_router.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/intelligent_meal_planner/meal_chat/orchestrator.py \
    src/intelligent_meal_planner/api/services.py \
    tests/meal_chat/test_orchestrator.py \
    tests/api/test_meal_chat_router.py
git commit -m "feat: replace rigid meal chat flow with crew orchestration"
```

### Task 5: Wire the RL planner to produce dual candidate plans

**Files:**
- Modify: `src/intelligent_meal_planner/api/services.py`
- Modify: `src/intelligent_meal_planner/tools/rl_model_tool.py`
- Test: `tests/meal_chat/test_crew_runtime.py`

- [ ] **Step 1: Write the failing dual-plan planning test**

```python
def test_runtime_requests_two_rl_plan_variants_when_negotiation_prefers_dual_options():
    runtime = CrewMealChatRuntime(planning_tool=FakePlanningTool())
    memory = ConversationMemory(
        phase="planning",
        target_ranges=TargetRanges(
            calories_min=1700,
            calories_max=1900,
            protein_min=100,
            protein_max=130,
            carbs_min=140,
            carbs_max=220,
            fat_min=40,
            fat_max=65,
            strategy="fat_loss",
        ),
        preferences={"budget": 120.0},
        negotiation_options=[
            NegotiationOption(key="budget_cut", title="保守减脂", rationale="...", budget=120.0),
            NegotiationOption(key="protein_priority", title="高蛋白优先", rationale="...", budget=150.0),
        ],
    )

    result = runtime._build_dual_plan(memory)

    assert len(result["alternatives"]) == 2
    assert result["alternatives"][0]["option_key"] == "budget_cut"
    assert result["alternatives"][1]["option_key"] == "protein_priority"
```

- [ ] **Step 2: Run the dual-plan test to verify it fails**

Run: `uv run pytest tests/meal_chat/test_crew_runtime.py::test_runtime_requests_two_rl_plan_variants_when_negotiation_prefers_dual_options -v`
Expected: FAIL because `_build_dual_plan` does not exist.

- [ ] **Step 3: Add dual-plan assembly logic around the existing RL tool**

```python
def _build_dual_plan(self, memory: ConversationMemory) -> dict:
    alternatives = []
    for option in memory.negotiation_options:
        plan = self.planning_tool.generate(
            goal=memory.preferences.get("health_goal", "healthy"),
            budget=option.budget,
            disliked_foods=memory.preferences.get("disliked_foods", []),
            preferred_tags=option.preferred_tags or memory.preferences.get("preferred_tags", []),
            hidden_targets=self._ranges_to_hidden_targets(memory.target_ranges, option.key),
        )
        alternatives.append(
            {
                "option_key": option.key,
                "title": option.title,
                "rationale": option.rationale,
                "meal_plan": plan,
            }
        )
    return {"primary": alternatives[0]["meal_plan"], "alternatives": alternatives}
```

- [ ] **Step 4: Run the dual-plan test to verify it passes**

Run: `uv run pytest tests/meal_chat/test_crew_runtime.py::test_runtime_requests_two_rl_plan_variants_when_negotiation_prefers_dual_options -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/intelligent_meal_planner/api/services.py \
    src/intelligent_meal_planner/tools/rl_model_tool.py \
    tests/meal_chat/test_crew_runtime.py
git commit -m "feat: generate dual RL meal plans for negotiated chats"
```

### Task 6: Update API and frontend contracts for flexible chat phases

**Files:**
- Modify: `src/intelligent_meal_planner/api/schemas.py`
- Modify: `frontend/src/api/index.ts`
- Modify: `frontend/src/views/MealPlanView.vue`
- Test: `tests/api/test_meal_chat_router.py`

- [ ] **Step 1: Write the failing API/frontend contract tests**

```python
def test_send_message_accepts_negotiating_status(client, auth_header, monkeypatch):
    fake_response = {
        "session_id": "session001",
        "status": "negotiating",
        "messages": [
            {"role": "assistant", "content": "当前预算偏紧，我先给你两个方向。"}
        ],
        "meal_plan": None,
    }
    monkeypatch.setattr(
        "intelligent_meal_planner.api.routers.meal_chat.meal_chat_app.handle_message",
        lambda db, user, session_id, content: fake_response,
    )

    response = client.post(
        "/api/meal-chat/sessions/session001/messages",
        headers=auth_header,
        json={"content": "预算 100 元"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "negotiating"
```

```ts
export interface MealChatSession {
  session_id: string
  status: 'discovering' | 'negotiating' | 'planning' | 'finalized'
  messages: ChatMessage[]
  meal_plan: MealPlan | { primary: MealPlan; alternatives: unknown[] } | null
}
```

- [ ] **Step 2: Run the router tests to verify they fail**

Run: `uv run pytest tests/api/test_meal_chat_router.py -v`
Expected: FAIL until the response schema no longer hard-codes the old statuses.

- [ ] **Step 3: Update the backend and frontend session contracts**

```python
class MealChatSessionResponse(BaseModel):
    session_id: str
    status: str
    messages: List[ChatMessage]
    meal_plan: Optional[dict] = None
```

```ts
export interface NegotiatedMealPlan {
  primary: MealPlan
  alternatives: Array<{
    option_key: string
    title: string
    rationale: string
    meal_plan: MealPlan
  }>
}

export interface MealChatSession {
  session_id: string
  status: 'discovering' | 'negotiating' | 'planning' | 'finalized'
  messages: ChatMessage[]
  meal_plan: MealPlan | NegotiatedMealPlan | null
}
```

- [ ] **Step 4: Update the meal chat view to stop branching on `budget_rejected`**

```ts
const isConversationActive = computed(() =>
  currentSession.value &&
  currentSession.value.status !== 'finalized'
)

const planAlternatives = computed(() => {
  const mealPlan = currentSession.value?.meal_plan
  return mealPlan && 'alternatives' in mealPlan ? mealPlan.alternatives : []
})
```

- [ ] **Step 5: Run the router tests to verify they pass**

Run: `uv run pytest tests/api/test_meal_chat_router.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/intelligent_meal_planner/api/schemas.py \
    frontend/src/api/index.ts \
    frontend/src/views/MealPlanView.vue \
    tests/api/test_meal_chat_router.py
git commit -m "feat: support flexible meal chat session phases"
```

### Task 7: Verify the whole migration and update docs

**Files:**
- Modify: `README.md`
- Review: `src/intelligent_meal_planner/meal_chat/session_schema.py`
- Review: `src/intelligent_meal_planner/meal_chat/target_ranges.py`
- Review: `src/intelligent_meal_planner/meal_chat/feasibility_negotiator.py`
- Review: `src/intelligent_meal_planner/meal_chat/crew_runtime.py`
- Review: `src/intelligent_meal_planner/meal_chat/orchestrator.py`
- Review: `src/intelligent_meal_planner/api/services.py`
- Review: `frontend/src/api/index.ts`
- Review: `frontend/src/views/MealPlanView.vue`

- [ ] **Step 1: Update README runtime docs**

```md
## 对话式配餐

当前聊天流程采用“前台单一营养师人格 + 后台 CrewAI 多 agent 协作”：

1. 通过自然对话理解目标、预算、忌口和口味
2. 将目标映射为营养范围而非单点值
3. 预算不足时进入协商阶段，默认给出两种折中方案
4. 条件足够时调用强化学习算法生成正式配餐
```

- [ ] **Step 2: Run the full backend test slice**

Run: `uv run pytest tests/meal_chat/test_target_ranges.py tests/meal_chat/test_feasibility_negotiator.py tests/meal_chat/test_crew_runtime.py tests/meal_chat/test_orchestrator.py tests/api/test_meal_chat_router.py -v`
Expected: PASS.

- [ ] **Step 3: Run formatting and lint checks**

Run: `uv run ruff check src/intelligent_meal_planner/meal_chat src/intelligent_meal_planner/api tests/meal_chat tests/api/test_meal_chat_router.py`
Expected: `All checks passed!`

Run: `uv run black --check src/intelligent_meal_planner/meal_chat src/intelligent_meal_planner/api tests/meal_chat tests/api/test_meal_chat_router.py`
Expected: `would be left unchanged`

- [ ] **Step 4: Inspect the final diff**

Run: `git diff -- README.md src/intelligent_meal_planner/meal_chat src/intelligent_meal_planner/api/services.py src/intelligent_meal_planner/api/schemas.py src/intelligent_meal_planner/db/models.py frontend/src/api/index.ts frontend/src/views/MealPlanView.vue tests/meal_chat tests/api/test_meal_chat_router.py`
Expected: Only the CrewAI chat migration, range-target logic, negotiation flow, API contract updates, and tests are present.

- [ ] **Step 5: Commit**

```bash
git add README.md \
    src/intelligent_meal_planner/meal_chat \
    src/intelligent_meal_planner/api/services.py \
    src/intelligent_meal_planner/api/schemas.py \
    src/intelligent_meal_planner/db/models.py \
    frontend/src/api/index.ts \
    frontend/src/views/MealPlanView.vue \
    tests/meal_chat \
    tests/api/test_meal_chat_router.py
git commit -m "feat: overhaul meal chat with crew-based negotiation"
```
