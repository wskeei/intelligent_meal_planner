# Immersive Meal Chat Result Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current "fixed intake then instant right-column result" flow into an immersive same-route experience with an explicit generation phase, a full-screen thinking overlay, and a full-screen meal result that can return to the original chat.

**Architecture:** Keep `/meal-plan` as a single route, but split runtime behavior into three user-visible phases: guided intake, explicit generation, and immersive result. Move CrewAI kickoff out of the final intake turn and behind a dedicated generation action so the frontend can show a full-screen transition before the meal plan is revealed. Build the result experience as an overlay layer above the existing chat page so chat context stays alive and can be restored without route churn.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic v2, CrewAI, Vue 3, TypeScript, Element Plus, vue-i18n, pytest, Vite

---

## File Structure

- Modify: `src/intelligent_meal_planner/meal_chat/orchestrator.py`
- Modify: `src/intelligent_meal_planner/meal_chat/intake_runtime.py`
- Modify: `src/intelligent_meal_planner/meal_chat/session_schema.py`
- Modify: `src/intelligent_meal_planner/api/services.py`
- Modify: `src/intelligent_meal_planner/api/routers/meal_chat.py`
- Modify: `src/intelligent_meal_planner/api/schemas.py`
- Modify: `tests/meal_chat/test_orchestrator.py`
- Modify: `tests/api/test_meal_chat_router.py`
- Modify: `frontend/src/api/index.ts`
- Modify: `frontend/src/views/MealPlanView.vue`
- Modify: `frontend/src/assets/main.css`
- Modify: `frontend/src/locales/zh.json`
- Modify: `frontend/src/locales/en.json`
- Create: `frontend/src/components/meal-chat/MealChatGenerationOverlay.vue`
- Create: `frontend/src/components/meal-chat/MealChatResultOverlay.vue`
- Create: `docs/2026-04-04-immersive-meal-chat-result-flow-review.md`

## Design Constraints To Preserve

- Same route only. Do not navigate away from `/meal-plan`.
- Returning from result to chat must preserve the full conversation and current session id.
- Motion language must feel calm and professional, not sci-fi or theatrical.
- Result first: the first screen after generation should prioritize the meal plan itself, with explanation as secondary content.
- Respect `prefers-reduced-motion`; the UX still has to work with minimal or disabled animation.
- The current "system trace" stays secondary and must not compete with the primary reveal.

## Task 1: Split Intake Completion From Crew Generation

**Files:**
- Modify: `src/intelligent_meal_planner/meal_chat/orchestrator.py`
- Modify: `src/intelligent_meal_planner/meal_chat/intake_runtime.py`
- Modify: `src/intelligent_meal_planner/meal_chat/session_schema.py`
- Modify: `src/intelligent_meal_planner/api/services.py`
- Modify: `src/intelligent_meal_planner/api/schemas.py`
- Modify: `tests/meal_chat/test_orchestrator.py`

- [ ] **Step 1: Write failing tests for the new phase split**

```python
def test_orchestrator_stops_at_planning_ready_before_running_crew():
    class FakeIntake:
        def run_turn(self, user_message, memory):
            memory.phase = "planning_ready"
            return type(
                "Result",
                (),
                {
                    "phase": "planning_ready",
                    "assistant_message": "信息已齐，准备正式生成。",
                    "memory": memory,
                    "ready_for_crew": True,
                },
            )()

    class FakeCrewRunner:
        def run(self, memory, user):
            raise AssertionError("crew runner should not execute during intake advance")

    orchestrator = MealChatOrchestrator(
        intake_runtime=FakeIntake(),
        crew_runner=FakeCrewRunner(),
    )
    session = type(
        "Session",
        (),
        {"status": "discovering", "collected_slots": {}, "final_plan": None},
    )()

    response = orchestrator.advance(user=None, session=session, user_message="预算 120 元，不吃辣")

    assert response["status"] == "planning_ready"
    assert response["meal_plan"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/meal_chat/test_orchestrator.py -v`
Expected: FAIL because `advance()` still calls `crew_runner.run()` immediately after intake becomes ready.

- [ ] **Step 3: Refactor the orchestrator into two explicit transitions**

```python
class MealChatOrchestrator:
    def advance(self, user, session, user_message: str):
        intake_result = self.intake_runtime.run_turn(user_message=user_message, memory=memory)

        session.collected_slots = intake_result.memory.model_dump(mode="json")
        session.status = intake_result.phase

        if intake_result.ready_for_crew:
            return {
                "status": "planning_ready",
                "assistant_message": intake_result.assistant_message,
                "meal_plan": None,
                "trace": {...},
            }

        return {...}

    def generate(self, user, session):
        memory = ConversationMemory.model_validate(session.collected_slots or {})
        final_result = self.crew_runner.run(memory=memory, user=user)
        ...
        return {...}
```

- [ ] **Step 4: Persist the new session-visible phases**

```python
class ConversationMemory(BaseModel):
    phase: str = "discovering"
    overlay_state: str | None = None
```

```python
return {
    "status": session.status,
    "meal_plan": session.final_plan,
    "presentation": {
        "phase": memory.phase,
        "overlay_state": memory.overlay_state,
    },
    ...
}
```

- [ ] **Step 5: Keep intake copy aligned with the new behavior**

```python
def planning_ready(locale: str) -> str:
    if locale == "en":
        return "The key information is complete. I am preparing the formal meal-generation step now."
    return "信息已经齐了，我现在开始正式生成配餐。"
```

- [ ] **Step 6: Run backend tests to verify phase split behavior**

Run: `uv run pytest tests/meal_chat/test_orchestrator.py tests/meal_chat/test_intake_runtime.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/intelligent_meal_planner/meal_chat/orchestrator.py src/intelligent_meal_planner/meal_chat/intake_runtime.py src/intelligent_meal_planner/meal_chat/session_schema.py src/intelligent_meal_planner/api/services.py src/intelligent_meal_planner/api/schemas.py tests/meal_chat/test_orchestrator.py
git commit -m "refactor: split meal chat intake from generation"
```

## Task 2: Add A Dedicated Generate Endpoint For The Overlay Flow

**Files:**
- Modify: `src/intelligent_meal_planner/api/routers/meal_chat.py`
- Modify: `src/intelligent_meal_planner/api/services.py`
- Modify: `src/intelligent_meal_planner/api/schemas.py`
- Modify: `tests/api/test_meal_chat_router.py`

- [ ] **Step 1: Write failing API tests for explicit generation**

```python
def test_generate_session_returns_finalized_payload(client, auth_header, monkeypatch):
    fake_response = {
        "session_id": "session001",
        "status": "finalized",
        "messages": [{"role": "assistant", "content": "多智能体协作已完成。"}],
        "meal_plan": {"id": "plan001", "meals": [], "nutrition": {}, "target": {}, "score": 0},
    }
    monkeypatch.setattr(
        "intelligent_meal_planner.api.routers.meal_chat.meal_chat_app.generate_session",
        lambda db, user, session_id: fake_response,
    )

    response = client.post("/api/meal-chat/sessions/session001/generate", headers=auth_header)

    assert response.status_code == 200
    assert response.json()["status"] == "finalized"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/api/test_meal_chat_router.py -v`
Expected: FAIL because the `/generate` route does not exist.

- [ ] **Step 3: Add the new API route and service method**

```python
@router.post("/sessions/{session_id}/generate", response_model=MealChatSessionResponse)
async def generate_session(...):
    return meal_chat_app.generate_session(db, current_user, session_id)
```

```python
def generate_session(self, db: Session, user: User, session_id: str) -> Dict[str, Any]:
    session = self._load_session(...)
    result = self.orchestrator.generate(user, session)
    ...
    return self._serialize_session(db, session)
```

- [ ] **Step 4: Guard invalid phase transitions**

```python
if session.status != "planning_ready":
    raise ValueError("generation_not_ready")
```

```python
if session.status == "finalized":
    return self._serialize_session(db, session)
```

- [ ] **Step 5: Serialize enough metadata for the overlay timing logic**

```python
return {
    ...
    "presentation": {
        "phase": session.status,
        "can_generate": session.status == "planning_ready",
        "has_result_overlay": session.status == "finalized",
    },
}
```

- [ ] **Step 6: Run backend API tests**

Run: `uv run pytest tests/api/test_meal_chat_router.py tests/api/test_meal_chat_schemas.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/intelligent_meal_planner/api/routers/meal_chat.py src/intelligent_meal_planner/api/services.py src/intelligent_meal_planner/api/schemas.py tests/api/test_meal_chat_router.py
git commit -m "feat: add explicit meal chat generation endpoint"
```

## Task 3: Build The Full-Screen Generation Overlay

**Files:**
- Create: `frontend/src/components/meal-chat/MealChatGenerationOverlay.vue`
- Modify: `frontend/src/views/MealPlanView.vue`
- Modify: `frontend/src/api/index.ts`
- Modify: `frontend/src/assets/main.css`
- Modify: `frontend/src/locales/zh.json`
- Modify: `frontend/src/locales/en.json`

- [ ] **Step 1: Add the frontend API contract**

```ts
export interface MealChatPresentation {
  phase: string
  can_generate?: boolean
  has_result_overlay?: boolean
}

generateSession: (sessionId: string) =>
  api.post<MealChatSession>(`/meal-chat/sessions/${sessionId}/generate`)
```

- [ ] **Step 2: Add overlay state to `MealPlanView.vue`**

```ts
const overlayMode = ref<'hidden' | 'generating' | 'result'>('hidden')
const overlayVisible = computed(() => overlayMode.value !== 'hidden')
const generationStartedAt = ref<number | null>(null)
```

- [ ] **Step 3: Create a calm, professional generation overlay component**

```vue
<template>
  <transition name="generation-overlay">
    <section v-if="visible" class="generation-overlay" aria-live="polite">
      <div class="generation-stage">
        <p class="eyebrow">{{ eyebrow }}</p>
        <h2>{{ title }}</h2>
        <p>{{ summary }}</p>
        <ul class="generation-steps">
          <li v-for="item in steps" :key="item.key" :class="{ active: item.active, complete: item.complete }">
            <span class="step-dot" />
            <span>{{ item.label }}</span>
          </li>
        </ul>
      </div>
    </section>
  </transition>
</template>
```

- [ ] **Step 4: Auto-enter generation overlay when the session becomes `planning_ready`**

```ts
async function startGenerationSequence() {
  if (!sessionId.value || overlayMode.value === 'generating') return

  overlayMode.value = 'generating'
  generationStartedAt.value = performance.now()

  const { data } = await mealChatApi.generateSession(sessionId.value)
  await waitForMinimumGenerationDuration(generationStartedAt.value, 1400)
  currentSession.value = data
  overlayMode.value = 'result'
}
```

- [ ] **Step 5: Add reduced-motion-safe animation tokens**

```css
:root {
  --overlay-enter-duration: 420ms;
  --overlay-exit-duration: 260ms;
  --overlay-ease: cubic-bezier(0.22, 1, 0.36, 1);
}

@media (prefers-reduced-motion: reduce) {
  :root {
    --overlay-enter-duration: 1ms;
    --overlay-exit-duration: 1ms;
  }
}
```

- [ ] **Step 6: Run build verification**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/meal-chat/MealChatGenerationOverlay.vue frontend/src/views/MealPlanView.vue frontend/src/api/index.ts frontend/src/assets/main.css frontend/src/locales/zh.json frontend/src/locales/en.json
git commit -m "feat: add immersive meal generation overlay"
```

## Task 4: Replace The Right-Column Result With A Full-Screen Result Overlay

**Files:**
- Create: `frontend/src/components/meal-chat/MealChatResultOverlay.vue`
- Modify: `frontend/src/views/MealPlanView.vue`
- Modify: `frontend/src/assets/main.css`
- Modify: `frontend/src/locales/zh.json`
- Modify: `frontend/src/locales/en.json`

- [ ] **Step 1: Move result rendering into a dedicated full-screen component**

```vue
<template>
  <transition name="result-overlay">
    <section v-if="visible" class="result-overlay">
      <header class="result-overlay-head">
        <button class="back-link" type="button" @click="$emit('return-to-chat')">
          {{ returnLabel }}
        </button>
        <div class="price-pill">¥{{ totalPrice }}</div>
      </header>

      <main class="result-hero">
        <h1>{{ title }}</h1>
        <div class="meal-groups">
          ...
        </div>
      </main>
    </section>
  </transition>
</template>
```

- [ ] **Step 2: Remove the old `v-if="finalPlan"` right-column card from the default layout**

```vue
<aside class="result-stack" :class="{ muted: overlayVisible }">
  <el-card class="status-card" shadow="hover">
    ...
  </el-card>
</aside>

<MealChatResultOverlay
  :visible="overlayMode === 'result'"
  :meal-plan="finalPlan"
  @return-to-chat="handleReturnToChat"
/>
```

- [ ] **Step 3: Preserve chat underlay when the result is visible**

```ts
function handleReturnToChat() {
  overlayMode.value = 'hidden'
}
```

```css
.meal-chat-page.overlay-active .chat-layout {
  filter: blur(8px);
  transform: scale(0.985);
  pointer-events: none;
}
```

- [ ] **Step 4: Make the result reveal feel like a continuation of generation, not a new page load**

```css
.result-overlay-enter-active {
  transition:
    opacity 360ms var(--overlay-ease),
    transform 420ms var(--overlay-ease);
}

.result-overlay-enter-from {
  opacity: 0;
  transform: translateY(24px) scale(0.985);
}
```

- [ ] **Step 5: Keep explanation and crew trace secondary**

```vue
<section class="result-secondary">
  <article class="explanation-card">...</article>
  <article class="trace-card collapsed">...</article>
</section>
```

- [ ] **Step 6: Run build verification**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/meal-chat/MealChatResultOverlay.vue frontend/src/views/MealPlanView.vue frontend/src/assets/main.css frontend/src/locales/zh.json frontend/src/locales/en.json
git commit -m "feat: reveal meal plan in immersive result overlay"
```

## Task 5: Motion Polish, Copy, And Acceptance Verification

**Files:**
- Modify: `frontend/src/views/MealPlanView.vue`
- Modify: `frontend/src/assets/main.css`
- Modify: `frontend/src/locales/zh.json`
- Modify: `frontend/src/locales/en.json`
- Create: `docs/2026-04-04-immersive-meal-chat-result-flow-review.md`

- [ ] **Step 1: Tune copy for the three key moments**

```json
{
  "generation": {
    "eyebrow": "正式生成中",
    "title": "正在整理今天的配餐",
    "summary": "系统正在核对预算、营养目标和饮食限制，再生成正式结果。",
    "return_to_chat": "返回聊天"
  }
}
```

- [ ] **Step 2: Apply `@animate` polish without adding noise**

```css
.generation-step.active .step-dot {
  transform: scale(1.12);
  opacity: 1;
}

.generation-step.complete .step-dot {
  transform: scale(1);
  opacity: 0.72;
}
```

- [ ] **Step 3: Apply `@arrange` hierarchy fixes to the overlay composition**

```css
.generation-stage {
  width: min(720px, calc(100vw - 48px));
  padding: clamp(32px, 5vw, 56px);
}

.result-hero {
  display: grid;
  gap: clamp(20px, 3vw, 36px);
}
```

- [ ] **Step 4: Run the final verification commands**

Run: `uv run pytest tests/meal_chat/test_orchestrator.py tests/api/test_meal_chat_router.py -v`
Expected: PASS

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 5: Execute the manual acceptance checklist and write it down**

```md
# Immersive Meal Chat Result Flow Review

- Fresh session enters chat normally.
- Final intake answer returns `planning_ready`, not `finalized`.
- Generation overlay appears immediately and lasts long enough to feel intentional.
- Result overlay replaces the old right-column presentation.
- "Return to chat" restores the original chat view and same session state.
- Reduced-motion mode disables large transitions but preserves usability.
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/views/MealPlanView.vue frontend/src/assets/main.css frontend/src/locales/zh.json frontend/src/locales/en.json docs/2026-04-04-immersive-meal-chat-result-flow-review.md
git commit -m "polish: finalize immersive meal chat result flow"
```

## Risks To Watch During Execution

- The current backend response model may assume every finalized session already has `meal_plan`; keep schema changes backward-safe while introducing `planning_ready`.
- `MealPlanView.vue` is already large. If overlay logic starts tangling existing chat logic, split timeline, overlay state, and result rendering into focused components instead of expanding the view further.
- Avoid fake latency. The overlay should have a minimum duration for pacing, but it must still be tied to actual generation completion.
- Keep accessibility intact. Focus traps, escape/return behavior, keyboard navigation, and reduced motion are all part of the acceptance bar.

## Execution Notes

- Use `@brainstorming` decisions as fixed constraints: same-route overlay, calm/professional motion, result-first reveal, return-to-chat preserved.
- Use `@animate` for purposeful motion only. Do not add decorative particles, scanning grids, or sci-fi HUD visuals.
- Use `@arrange` to make the result overlay feel like a deliberate composition, not a stretched card.
- Before claiming completion, invoke `verification-before-completion` and attach both command output and manual acceptance notes.
