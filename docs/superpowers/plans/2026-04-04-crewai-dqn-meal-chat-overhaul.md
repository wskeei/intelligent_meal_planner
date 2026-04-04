# CrewAI DQN Meal Chat Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove all PPO paths and make the system run on DQN only, then replace the current local pseudo-agent runtime with a standard CrewAI multi-agent planning flow whose collaboration trace is visible to users.

**Architecture:** Keep the product in two stages. Stage 1 is a conversational intake loop that gathers profile, budget, goal, restrictions, and preferences over multiple turns. Stage 2 starts a real CrewAI `Crew` after the intake is complete; the crew runs visible specialist agents, calls the DQN planner tool, and returns both the final meal plan and the agent collaboration transcript to the frontend.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic v2, CrewAI, custom Dueling Double DQN, Vue 3, Element Plus, pytest

---

## File Structure

- Delete: `src/intelligent_meal_planner/rl/train_dqn.py`
- Delete: `scripts/train_optimized.py`
- Delete: `src/intelligent_meal_planner/agents/crew.py`
- Delete: `src/intelligent_meal_planner/agents/user_profiler.py`
- Delete: `src/intelligent_meal_planner/agents/rl_chef.py`
- Modify: `src/intelligent_meal_planner/tools/rl_model_tool.py`
- Modify: `src/intelligent_meal_planner/api/services.py`
- Modify: `src/intelligent_meal_planner/api/schemas.py`
- Modify: `src/intelligent_meal_planner/api/routers/meal_chat.py`
- Modify: `src/intelligent_meal_planner/meal_chat/orchestrator.py`
- Modify: `src/intelligent_meal_planner/meal_chat/types.py`
- Modify: `src/intelligent_meal_planner/meal_chat/session_schema.py`
- Modify: `frontend/src/views/MealPlanView.vue`
- Modify: `frontend/src/api/index.ts`
- Modify: `frontend/src/locales/zh.json`
- Modify: `frontend/src/locales/en.json`
- Modify: `README.md`
- Modify: `pyproject.toml`
- Create: `src/intelligent_meal_planner/meal_chat/intake_runtime.py`
- Create: `src/intelligent_meal_planner/meal_chat/crew_models.py`
- Create: `src/intelligent_meal_planner/meal_chat/crew_tools.py`
- Create: `src/intelligent_meal_planner/meal_chat/crew_factory.py`
- Create: `src/intelligent_meal_planner/meal_chat/crew_runner.py`
- Create: `tests/meal_chat/test_intake_runtime.py`
- Create: `tests/meal_chat/test_crew_factory.py`
- Create: `tests/meal_chat/test_crew_runner.py`
- Modify: `tests/api/test_meal_chat_router.py`
- Modify: `tests/meal_chat/test_orchestrator.py`
- Modify: `tests/tools/test_rl_model_tool.py`

### Task 1: Make RL Strictly DQN-Only

**Files:**
- Modify: `src/intelligent_meal_planner/tools/rl_model_tool.py`
- Modify: `main.py`
- Modify: `README.md`
- Modify: `pyproject.toml`
- Delete: `src/intelligent_meal_planner/rl/train_dqn.py`
- Delete: `scripts/train_optimized.py`
- Modify: `tests/tools/test_rl_model_tool.py`

- [ ] **Step 1: Write the failing DQN-only tests**

```python
from pathlib import Path

from intelligent_meal_planner.tools.rl_model_tool import resolve_model_path


def test_resolve_model_path_only_accepts_dqn_artifacts(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    dqn_path = models_dir / "dqn_meal_best.pt"
    dqn_path.write_text("stub", encoding="utf-8")

    assert resolve_model_path(tmp_path) == dqn_path


def test_resolve_model_path_raises_when_no_dqn_model_exists(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()

    try:
        resolve_model_path(tmp_path)
    except FileNotFoundError as exc:
        assert "DQN" in str(exc)
    else:
        raise AssertionError("expected FileNotFoundError")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/tools/test_rl_model_tool.py -v`
Expected: FAIL because `resolve_model_path()` still accepts PPO candidates.

- [ ] **Step 3: Remove PPO fallback and make the tool load DQN only**

```python
def resolve_model_path(project_root: Path) -> Path:
    models_dir = project_root / "models"
    candidates = (
        models_dir / "dqn_meal_best.pt",
        models_dir / "dqn_meal_final.pt",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"未找到 DQN 模型文件，已检查: {', '.join(str(path) for path in candidates)}"
    )


class RLModelTool:
    """Load the trained DQN model and produce a meal plan JSON payload."""

    def __init__(self, model_path: Optional[str] = None):
        self.description = (
            "使用训练好的 MaskableDQN 模型生成一日三餐方案，"
            "输入营养目标、预算和饮食限制，返回结构化结果。"
        )
        ...
        self.backend = "dqn"
        self.model: Optional[MaskableDQNAgent] = None

    def _load_model(self) -> None:
        if self.model is None:
            self.model = MaskableDQNAgent.from_pretrained(str(self.model_path))
```

- [ ] **Step 4: Remove obsolete PPO entry points and references**

```python
def train_model():
    """训练 DQN 模型。"""
    print("开始训练 DQN 模型...")
    from scripts.train_dqn_maskable import train

    train(total_timesteps=50000)
```

```toml
[project]
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "streamlit>=1.40.0",
    "crewai>=0.95.0",
    "crewai-tools>=0.18.0",
    "gymnasium>=0.29.1",
    "numpy>=1.26.0",
    "torch>=2.5.0",
    "pydantic>=2.10.0",
    "tensorboard>=2.15.0",
    "sqlalchemy>=2.0.45",
    "passlib[bcrypt]>=1.7.4",
    "python-jose>=3.5.0",
    "email-validator>=2.3.0",
    "bcrypt==4.0.1",
    "langchain-openai>=0.3.23",
    "python-dotenv>=1.1.1",
]
```

- [ ] **Step 5: Run tests to verify the DQN-only path passes**

Run: `uv run pytest tests/tools/test_rl_model_tool.py tests/test_main_cli.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add main.py pyproject.toml README.md tests/tools/test_rl_model_tool.py src/intelligent_meal_planner/tools/rl_model_tool.py
git rm src/intelligent_meal_planner/rl/train_dqn.py scripts/train_optimized.py
git commit -m "refactor: remove PPO runtime paths and keep DQN only"
```

### Task 2: Split Intake Stage from Planning Stage

**Files:**
- Create: `src/intelligent_meal_planner/meal_chat/intake_runtime.py`
- Modify: `src/intelligent_meal_planner/meal_chat/orchestrator.py`
- Modify: `src/intelligent_meal_planner/meal_chat/types.py`
- Modify: `src/intelligent_meal_planner/meal_chat/session_schema.py`
- Create: `tests/meal_chat/test_intake_runtime.py`
- Modify: `tests/meal_chat/test_orchestrator.py`

- [ ] **Step 1: Write failing tests for the two-stage conversation flow**

```python
from intelligent_meal_planner.meal_chat.intake_runtime import IntakeRuntime
from intelligent_meal_planner.meal_chat.session_schema import ConversationMemory


def test_intake_runtime_keeps_asking_until_required_fields_are_complete():
    runtime = IntakeRuntime(extractor=None)
    memory = ConversationMemory(phase="discovering")

    result = runtime.run_turn("我最近想减脂", memory)

    assert result.phase == "discovering"
    assert result.ready_for_crew is False
    assert "预算" in result.assistant_message


def test_orchestrator_switches_to_crew_stage_once_intake_is_complete():
    class FakeIntake:
        def run_turn(self, user_message, memory):
            memory.phase = "planning_ready"
            memory.preferences["budget"] = 120.0
            return type(
                "Result",
                (),
                {
                    "phase": "planning_ready",
                    "assistant_message": "信息已齐，可以开始协作配餐。",
                    "memory": memory,
                    "ready_for_crew": True,
                    "crew_payload": {"budget": 120.0},
                },
            )()

    class FakeCrewRunner:
        def run(self, memory):
            return {"phase": "finalized", "assistant_message": "完成", "meal_plan": None, "events": []}

    orchestrator = MealChatOrchestrator(intake_runtime=FakeIntake(), crew_runner=FakeCrewRunner())
    session = type("Session", (), {"status": "discovering", "collected_slots": {}, "final_plan": None})()
    user = type("User", (), {"id": 1})()

    response = orchestrator.advance(user, session, "预算120元，增肌，高蛋白")

    assert response["status"] == "finalized"
    assert response["trace"]["phase"] == "finalized"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/meal_chat/test_intake_runtime.py tests/meal_chat/test_orchestrator.py -v`
Expected: FAIL because `IntakeRuntime` does not exist and `MealChatOrchestrator` still expects the old runtime.

- [ ] **Step 3: Introduce a dedicated intake runtime and a new orchestrator contract**

```python
class IntakeTurnResult(BaseModel):
    phase: str
    assistant_message: str
    memory: ConversationMemory
    ready_for_crew: bool = False
    crew_payload: dict | None = None
```

```python
class IntakeRuntime:
    def __init__(self, extractor=None):
        self.extractor = extractor

    def run_turn(self, user_message: str, memory: ConversationMemory) -> IntakeTurnResult:
        updated = memory.model_copy(deep=True)
        ...
        if not analysis.ready_for_negotiation:
            return IntakeTurnResult(
                phase="discovering",
                assistant_message=follow_up.assistant_message,
                memory=updated,
                ready_for_crew=False,
            )
        updated.phase = "planning_ready"
        return IntakeTurnResult(
            phase="planning_ready",
            assistant_message="信息已经齐了，我现在组织多智能体为你生成方案。",
            memory=updated,
            ready_for_crew=True,
            crew_payload=updated.model_dump(mode="json"),
        )
```

```python
class MealChatOrchestrator:
    def __init__(self, intake_runtime, crew_runner):
        self.intake_runtime = intake_runtime
        self.crew_runner = crew_runner

    def advance(self, user, session, user_message: str):
        memory = ConversationMemory.model_validate(session.collected_slots or {})
        intake_result = self.intake_runtime.run_turn(user_message=user_message, memory=memory)
        if not intake_result.ready_for_crew:
            ...
        crew_result = self.crew_runner.run(memory=intake_result.memory, user=user)
        ...
```

- [ ] **Step 4: Persist the new stage markers and trace containers**

```python
class ConversationMemory(BaseModel):
    phase: str = "discovering"
    profile: dict = Field(default_factory=dict)
    preferences: dict = Field(default_factory=dict)
    known_facts: dict = Field(default_factory=dict)
    open_questions: list[str] = Field(default_factory=list)
    crew_events: list[dict] = Field(default_factory=list)
    crew_summary: dict | None = None
```

- [ ] **Step 5: Run tests to verify the stage split passes**

Run: `uv run pytest tests/meal_chat/test_intake_runtime.py tests/meal_chat/test_orchestrator.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/intelligent_meal_planner/meal_chat/intake_runtime.py src/intelligent_meal_planner/meal_chat/orchestrator.py src/intelligent_meal_planner/meal_chat/types.py src/intelligent_meal_planner/meal_chat/session_schema.py tests/meal_chat/test_intake_runtime.py tests/meal_chat/test_orchestrator.py
git commit -m "refactor: split meal chat intake from planning stage"
```

### Task 3: Introduce Standard CrewAI Agents, Tasks, and Typed Outputs

**Files:**
- Create: `src/intelligent_meal_planner/meal_chat/crew_models.py`
- Create: `src/intelligent_meal_planner/meal_chat/crew_tools.py`
- Create: `src/intelligent_meal_planner/meal_chat/crew_factory.py`
- Create: `src/intelligent_meal_planner/meal_chat/crew_runner.py`
- Create: `tests/meal_chat/test_crew_factory.py`
- Create: `tests/meal_chat/test_crew_runner.py`

- [ ] **Step 1: Write failing tests that require real CrewAI objects to be assembled**

```python
from intelligent_meal_planner.meal_chat.crew_factory import build_meal_planning_crew
from intelligent_meal_planner.meal_chat.session_schema import ConversationMemory


def test_build_meal_planning_crew_returns_named_crewai_agents():
    crew_bundle = build_meal_planning_crew(planning_tool=None)

    roles = [agent.role for agent in crew_bundle.agents]
    assert "需求审查专员" in roles
    assert "营养规划师" in roles
    assert "预算协调员" in roles
    assert "DQN 配餐师" in roles
    assert "结果解读员" in roles


def test_crew_runner_returns_visible_agent_events():
    class FakeCrew:
        def kickoff(self, inputs):
            return {
                "final_message": "方案完成",
                "meal_plan": {"id": "plan001"},
                "events": [
                    {"agent": "需求审查专员", "status": "completed", "message": "已确认用户需求"},
                    {"agent": "DQN 配餐师", "status": "completed", "message": "已调用 DQN 生成方案"},
                ],
            }

    runner = CrewMealPlannerRunner(lambda planning_tool: FakeCrew(), planning_tool=None)
    memory = ConversationMemory(
        phase="planning_ready",
        preferences={"budget": 120.0, "health_goal": "gain_muscle"},
    )

    result = runner.run(memory=memory, user=None)

    assert result["phase"] == "finalized"
    assert len(result["events"]) == 2
    assert result["events"][1]["agent"] == "DQN 配餐师"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/meal_chat/test_crew_factory.py tests/meal_chat/test_crew_runner.py -v`
Expected: FAIL because the CrewAI factory and runner do not exist.

- [ ] **Step 3: Define typed CrewAI result models and visible event records**

```python
class CrewEvent(BaseModel):
    agent: str
    status: str
    message: str
    payload: dict | None = None


class CrewPlanningResult(BaseModel):
    final_message: str
    meal_plan: dict
    events: list[CrewEvent]
    negotiation_summary: dict | None = None
```

- [ ] **Step 4: Build real CrewAI agents and tasks around the DQN planning tool**

```python
def build_meal_planning_crew(planning_tool) -> CrewBundle:
    requirements_agent = Agent(
        role="需求审查专员",
        goal="核对用户资料是否完整，输出可执行约束",
        backstory="擅长把自然语言偏好整理成结构化需求",
        verbose=True,
    )
    nutrition_agent = Agent(
        role="营养规划师",
        goal="把用户目标映射到营养范围和执行策略",
        backstory="专注于增肌、减脂和均衡饮食方案",
        verbose=True,
    )
    budget_agent = Agent(
        role="预算协调员",
        goal="判断预算可行性并提出折中方向",
        backstory="负责成本与营养目标的冲突协调",
        verbose=True,
    )
    dqn_agent = Agent(
        role="DQN 配餐师",
        goal="调用 DQN 工具生成结构化配餐结果",
        backstory="负责把营养约束映射为最终菜谱方案",
        tools=[planning_tool],
        verbose=True,
    )
    explanation_agent = Agent(
        role="结果解读员",
        goal="向用户解释方案形成原因和执行建议",
        backstory="负责把多智能体决策过程转成可信解释",
        verbose=True,
    )
    ...
```

```python
class CrewMealPlannerRunner:
    def __init__(self, crew_factory, planning_tool):
        self.crew_factory = crew_factory
        self.planning_tool = planning_tool

    def run(self, memory: ConversationMemory, user) -> dict:
        crew = self.crew_factory(self.planning_tool)
        kickoff_result = crew.kickoff(inputs=self._build_inputs(memory, user))
        parsed = self._parse_result(kickoff_result)
        return {
            "phase": "finalized",
            "assistant_message": parsed.final_message,
            "meal_plan": parsed.meal_plan,
            "events": [event.model_dump(mode="json") for event in parsed.events],
        }
```

- [ ] **Step 5: Run tests to verify the CrewAI layer passes**

Run: `uv run pytest tests/meal_chat/test_crew_factory.py tests/meal_chat/test_crew_runner.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/intelligent_meal_planner/meal_chat/crew_models.py src/intelligent_meal_planner/meal_chat/crew_tools.py src/intelligent_meal_planner/meal_chat/crew_factory.py src/intelligent_meal_planner/meal_chat/crew_runner.py tests/meal_chat/test_crew_factory.py tests/meal_chat/test_crew_runner.py
git commit -m "feat: add standard CrewAI meal planning crew"
```

### Task 4: Connect FastAPI Session Flow to the CrewAI Planning Stage

**Files:**
- Modify: `src/intelligent_meal_planner/api/services.py`
- Modify: `src/intelligent_meal_planner/api/schemas.py`
- Modify: `src/intelligent_meal_planner/api/routers/meal_chat.py`
- Modify: `src/intelligent_meal_planner/meal_chat/orchestrator.py`
- Modify: `tests/api/test_meal_chat_router.py`
- Modify: `tests/meal_chat/test_orchestrator.py`

- [ ] **Step 1: Write failing API tests for visible agent collaboration payloads**

```python
def test_send_message_returns_visible_crew_events(client, auth_header, monkeypatch):
    fake_response = {
        "session_id": "session001",
        "status": "finalized",
        "messages": [
            {"role": "assistant", "content": "多智能体协作已完成，我给你整理好了方案。"}
        ],
        "meal_plan": {"id": "plan001", "meals": [], "nutrition": {}, "target": {}, "score": 10},
        "crew_trace": [
            {"agent": "需求审查专员", "status": "completed", "message": "需求已确认"},
            {"agent": "DQN 配餐师", "status": "completed", "message": "DQN 配餐完成"},
        ],
    }
    monkeypatch.setattr(
        "intelligent_meal_planner.api.routers.meal_chat.meal_chat_app.handle_message",
        lambda db, user, session_id, content: fake_response,
    )

    response = client.post(
        "/api/meal-chat/sessions/session001/messages",
        headers=auth_header,
        json={"content": "给我方案"},
    )

    assert response.status_code == 200
    assert len(response.json()["crew_trace"]) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/api/test_meal_chat_router.py tests/meal_chat/test_orchestrator.py -v`
Expected: FAIL because the session response schema does not expose CrewAI trace events.

- [ ] **Step 3: Return `crew_trace` and persist crew output in the session state**

```python
class MealChatSessionResponse(BaseModel):
    session_id: str
    status: str
    messages: list[ChatMessage]
    meal_plan: MealPlan | NegotiatedMealPlan | None = None
    crew_trace: list[dict] = Field(default_factory=list)
```

```python
class MealChatApplication:
    @property
    def orchestrator(self) -> MealChatOrchestrator:
        if self._orchestrator is None:
            planner = StrictBudgetPlanner()
            intake_runtime = IntakeRuntime(extractor=DeepSeekSlotExtractor())
            crew_runner = CrewMealPlannerRunner(build_meal_planning_crew, planner)
            self._orchestrator = MealChatOrchestrator(
                intake_runtime=intake_runtime,
                crew_runner=crew_runner,
            )
        return self._orchestrator
```

```python
return {
    "status": final_result["phase"],
    "assistant_message": final_result["assistant_message"],
    "hidden_targets": None,
    "meal_plan": final_result["meal_plan"],
    "trace": {
        "phase": final_result["phase"],
        "memory": memory_dump,
        "crew_trace": final_result["events"],
        "open_questions": memory_dump.get("open_questions", []),
        "known_facts": memory_dump.get("known_facts", {}),
    },
}
```

- [ ] **Step 4: Serialize the new trace into the HTTP response**

```python
return {
    "session_id": session.id,
    "status": session.status,
    "messages": [...],
    "meal_plan": session.final_plan,
    "crew_trace": (session.collected_slots or {}).get("crew_events", []),
}
```

- [ ] **Step 5: Run tests to verify the API contract passes**

Run: `uv run pytest tests/api/test_meal_chat_router.py tests/meal_chat/test_orchestrator.py tests/api/test_auth_profile.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/intelligent_meal_planner/api/services.py src/intelligent_meal_planner/api/schemas.py src/intelligent_meal_planner/api/routers/meal_chat.py src/intelligent_meal_planner/meal_chat/orchestrator.py tests/api/test_meal_chat_router.py tests/meal_chat/test_orchestrator.py
git commit -m "feat: expose CrewAI collaboration trace through meal chat api"
```

### Task 5: Show the Multi-Agent Collaboration Process in the Frontend

**Files:**
- Modify: `frontend/src/views/MealPlanView.vue`
- Modify: `frontend/src/api/index.ts`
- Modify: `frontend/src/locales/zh.json`
- Modify: `frontend/src/locales/en.json`

- [ ] **Step 1: Add failing frontend type coverage for the new trace payload**

```ts
export interface CrewTraceEvent {
  agent: string
  status: 'completed' | 'running' | 'blocked'
  message: string
  payload?: Record<string, unknown>
}

export interface MealChatSession {
  session_id: string
  status: string
  messages: ChatMessage[]
  meal_plan: MealPlan | NegotiatedMealPlan | null
  crew_trace: CrewTraceEvent[]
}
```

- [ ] **Step 2: Run frontend type check to verify it fails before the view is updated**

Run: `cd frontend && npm run build`
Expected: FAIL because the view and API types do not yet handle `crew_trace`.

- [ ] **Step 3: Render a visible multi-agent collaboration timeline next to the chat**

```vue
<el-card class="crew-card" shadow="hover">
  <template #header>
    <div class="section-head compact">
      <div>
        <h2>{{ $t('meal_plan.crew_title') }}</h2>
        <p>{{ $t('meal_plan.crew_subtitle') }}</p>
      </div>
    </div>
  </template>

  <div v-if="crewTrace.length" class="crew-timeline">
    <article
      v-for="event in crewTrace"
      :key="`${event.agent}-${event.message}`"
      class="crew-event"
    >
      <div class="crew-event-head">
        <strong>{{ event.agent }}</strong>
        <span class="crew-status">{{ event.status }}</span>
      </div>
      <p>{{ event.message }}</p>
    </article>
  </div>
  <p v-else class="crew-empty">{{ $t('meal_plan.crew_empty') }}</p>
</el-card>
```

```ts
const crewTrace = computed(() => currentSession.value?.crew_trace ?? [])
```

- [ ] **Step 4: Add i18n copy for the new visible collaboration UI**

```json
{
  "meal_plan": {
    "crew_title": "多智能体协作过程",
    "crew_subtitle": "你可以看到系统如何分工、协商并调用 DQN 生成方案",
    "crew_empty": "资料收集中，协作记录会在生成方案时显示。"
  }
}
```

- [ ] **Step 5: Run frontend build to verify the UI compiles**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/views/MealPlanView.vue frontend/src/api/index.ts frontend/src/locales/zh.json frontend/src/locales/en.json
git commit -m "feat: show visible CrewAI collaboration timeline in meal plan ui"
```

### Task 6: Remove Legacy Pseudo-Agent Compatibility Layer and Update Docs

**Files:**
- Delete: `src/intelligent_meal_planner/agents/crew.py`
- Delete: `src/intelligent_meal_planner/agents/user_profiler.py`
- Delete: `src/intelligent_meal_planner/agents/rl_chef.py`
- Modify: `src/intelligent_meal_planner/agents/__init__.py`
- Modify: `README.md`
- Modify: `src/intelligent_meal_planner/__init__.py`

- [ ] **Step 1: Write a failing regression test that ensures the old compatibility layer is gone**

```python
import importlib


def test_legacy_agents_package_no_longer_exports_runtime_stubs():
    module = importlib.import_module("intelligent_meal_planner.agents")
    assert getattr(module, "__all__", []) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_main_cli.py -v`
Expected: FAIL because the compatibility exports still exist.

- [ ] **Step 3: Remove deprecated stubs and rewrite docs around CrewAI + DQN**

```python
"""CrewAI-based meal planning package."""

__all__ = []
```

```md
# 基于 DQN 与 CrewAI 多智能体协作的智能配餐系统

## 核心流程

1. 与用户多轮对话收集资料
2. 信息充分后启动 CrewAI 多智能体团队
3. 团队完成需求审查、营养规划、预算协商、DQN 配餐、结果解释
4. 前端展示最终方案与协作过程
```

- [ ] **Step 4: Run the targeted regression tests**

Run: `uv run pytest tests/test_main_cli.py tests/api/test_meal_chat_router.py tests/meal_chat/test_orchestrator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add README.md src/intelligent_meal_planner/__init__.py src/intelligent_meal_planner/agents/__init__.py tests/test_main_cli.py
git rm src/intelligent_meal_planner/agents/crew.py src/intelligent_meal_planner/agents/user_profiler.py src/intelligent_meal_planner/agents/rl_chef.py
git commit -m "chore: remove legacy pseudo-agent layer and refresh docs"
```

### Task 7: Run End-to-End Verification Before Completion

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/plans/2026-04-04-crewai-dqn-meal-chat-overhaul.md`

- [ ] **Step 1: Run the backend test suite covering RL and meal chat**

Run: `uv run pytest tests/tools/test_rl_model_tool.py tests/meal_chat tests/api -v`
Expected: PASS

- [ ] **Step 2: Run the frontend production build**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 3: Run a manual smoke test of the runtime flow**

Run: `uv run python main.py api`
Expected: FastAPI starts successfully and `/api/meal-chat/sessions` can create a session with DQN-only runtime wiring.

- [ ] **Step 4: Verify the final repository no longer contains PPO runtime references**

Run: `rg -n "MaskablePPO|PPO|ppo_meal|best_model.zip|train_optimized" src scripts README.md tests pyproject.toml`
Expected: no matches for runtime code paths; only historical plan documents may still contain archived references.

- [ ] **Step 5: Commit final verification and doc adjustments**

```bash
git add README.md docs/superpowers/plans/2026-04-04-crewai-dqn-meal-chat-overhaul.md
git commit -m "docs: finalize crewai dqn overhaul verification notes"
```

## Self-Review

- Spec coverage: the plan covers DQN-only cleanup, two-stage runtime decomposition, real CrewAI introduction, API contract updates, frontend visibility, legacy removal, and verification.
- Placeholder scan: no `TODO` or `TBD` markers remain.
- Type consistency: the plan uses `crew_trace`, `crew_events`, `IntakeRuntime`, and `CrewMealPlannerRunner` consistently across tasks.

## Execution Notes

- Executed in git worktree `.worktrees/crewai-dqn-meal-chat-overhaul` on branch `feat/crewai-dqn-meal-chat-overhaul`.
- Verification run on 2026-04-04:
  - `uv run pytest tests/tools/test_rl_model_tool.py tests/meal_chat tests/api -v`
  - `cd frontend && npm run build`
  - `MEAL_PLANNER_API_RELOAD=0 timeout 8s uv run python main.py api`
  - `rg -n "MaskablePPO|PPO|ppo_meal|best_model.zip|train_optimized" src scripts README.md tests pyproject.toml`
- Verification outcome:
  - Backend targeted suite passed (`53 passed`).
  - Frontend production build passed.
  - FastAPI startup smoke test reached `Application startup complete` before timeout shutdown.
  - PPO runtime reference scan returned no matches in `src`, `scripts`, `README.md`, `tests`, or `pyproject.toml`.
