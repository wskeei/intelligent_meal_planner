# Weekly Plan And Shopping Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the current single-day conversational meal planner into a persistent closure loop where users can manually add finalized day plans into a weekly plan and generate a backend-saved shopping list with ingredient and dish-source views.

**Architecture:** Keep `meal_chat` as the single source of truth for generating a finalized daily meal plan, then add two new persistent domain objects after generation: `weekly plan` and `shopping list`. Weekly plans store immutable day snapshots derived from a finalized meal plan, and shopping lists are generated from weekly-plan day snapshots so the current meal-chat runtime and RL stack stay isolated from post-generation management features.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic v2, Vue 3, TypeScript, Pinia, Element Plus, vue-i18n, pytest, Vite

---

## File Structure

- Modify: `src/intelligent_meal_planner/db/models.py`
- Modify: `src/intelligent_meal_planner/api/main.py`
- Modify: `src/intelligent_meal_planner/api/schemas.py`
- Modify: `src/intelligent_meal_planner/api/services.py`
- Modify: `src/intelligent_meal_planner/api/routers/__init__.py`
- Create: `src/intelligent_meal_planner/api/routers/weekly_plans.py`
- Create: `src/intelligent_meal_planner/api/routers/shopping_lists.py`
- Create: `tests/api/test_weekly_plans_router.py`
- Create: `tests/api/test_shopping_lists_router.py`
- Modify: `frontend/src/api/index.ts`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/views/MealPlanView.vue`
- Modify: `frontend/src/views/HistoryView.vue`
- Modify: `frontend/src/views/ShoppingListView.vue`
- Create: `frontend/src/views/WeeklyPlanView.vue`
- Create: `frontend/src/stores/weeklyPlan.ts`
- Modify: `frontend/src/stores/shopping.ts`
- Modify: `frontend/src/views/HomeView.vue`
- Modify: `frontend/src/locales/zh.json`
- Modify: `frontend/src/locales/en.json`

## Product Scope To Preserve

- Do not change the existing `meal_chat -> finalized meal_plan` generation flow.
- Weekly plans are manual accumulation only in V1. No auto-fill 3-day or 7-day plan generation.
- Weekly plans and shopping lists are persisted on the backend, but there is no sharing, collaboration, or cross-account sync feature.
- Shopping lists must support two read modes:
  - ingredient aggregate view
  - dish-source trace view
- The existing shopping list route stays the user-facing entry, but its data source moves from local-only Pinia state to backend-persisted records.

## Domain Decisions

- A weekly plan belongs to one user and contains multiple day slots.
- Each day slot stores a snapshot of the finalized meal plan at the time it was added.
- A shopping list belongs to one user and is generated from exactly one weekly plan.
- Shopping-list rows store both:
  - aggregated ingredient-facing data for buying
  - source references back to day slot, meal type, and recipe name for explainability
- Manual ad hoc shopping items remain allowed, but they attach to a persisted shopping list instead of browser local storage.

## Task 1: Add Persistent Weekly Plan And Shopping List Data Models

**Files:**
- Modify: `src/intelligent_meal_planner/db/models.py`
- Modify: `src/intelligent_meal_planner/api/schemas.py`
- Create: `tests/api/test_weekly_plans_router.py`
- Create: `tests/api/test_shopping_lists_router.py`

- [ ] **Step 1: Write failing schema and serialization tests for the new resources**

```python
def test_weekly_plan_response_serializes_day_snapshots():
    payload = WeeklyPlanResponse(
        id=1,
        name="本周控卡计划",
        days=[
            WeeklyPlanDayResponse(
                id=11,
                plan_date=date(2026, 4, 6),
                source_session_id="session-1",
                meal_plan_snapshot={"id": "plan-1", "meals": [], "nutrition": {}, "target": {}, "score": 0},
            )
        ],
    )
    assert payload.days[0].source_session_id == "session-1"


def test_shopping_list_item_response_keeps_source_recipes():
    item = ShoppingListItemResponse(
        id=21,
        ingredient_name="鸡胸肉",
        display_amount="400g",
        sources=[{"plan_date": "2026-04-06", "meal_type": "lunch", "recipe_name": "香煎鸡胸"}],
    )
    assert item.sources[0]["recipe_name"] == "香煎鸡胸"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/api/test_weekly_plans_router.py tests/api/test_shopping_lists_router.py -v`
Expected: FAIL because the response models and resource tests do not exist yet.

- [ ] **Step 3: Extend SQLAlchemy models with explicit ownership and snapshot boundaries**

```python
class WeeklyPlan(Base):
    __tablename__ = "weekly_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WeeklyPlanDay(Base):
    __tablename__ = "weekly_plan_days"

    id = Column(Integer, primary_key=True, index=True)
    weekly_plan_id = Column(Integer, ForeignKey("weekly_plans.id"), nullable=False, index=True)
    plan_date = Column(Date, nullable=False, index=True)
    source_session_id = Column(String, nullable=True)
    meal_plan_snapshot = Column(JSON, nullable=False)
    nutrition_snapshot = Column(JSON, nullable=False, default=dict)
```

```python
class ShoppingList(Base):
    __tablename__ = "shopping_lists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    weekly_plan_id = Column(Integer, ForeignKey("weekly_plans.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)


class ShoppingListItem(Base):
    __tablename__ = "shopping_list_items"

    id = Column(Integer, primary_key=True, index=True)
    shopping_list_id = Column(Integer, ForeignKey("shopping_lists.id"), nullable=False, index=True)
    ingredient_name = Column(String, nullable=False, index=True)
    display_amount = Column(String, nullable=True)
    checked = Column(Integer, nullable=False, default=0)
    category = Column(String, nullable=True)
    source_kind = Column(String, nullable=False, default="weekly-plan")
    source_refs = Column(JSON, nullable=False, default=list)
```

- [ ] **Step 4: Add Pydantic request and response contracts**

```python
class WeeklyPlanCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    notes: str | None = None


class WeeklyPlanAttachDayRequest(BaseModel):
    plan_date: date
    meal_plan_id: str
    source_session_id: str | None = None


class ShoppingListGenerateRequest(BaseModel):
    weekly_plan_id: int
    name: str | None = None
```

- [ ] **Step 5: Run the new resource tests again**

Run: `uv run pytest tests/api/test_weekly_plans_router.py tests/api/test_shopping_lists_router.py -v`
Expected: PASS for schema-level expectations, with router-level tests still pending in later tasks.

- [ ] **Step 6: Commit**

```bash
git add src/intelligent_meal_planner/db/models.py src/intelligent_meal_planner/api/schemas.py tests/api/test_weekly_plans_router.py tests/api/test_shopping_lists_router.py
git commit -m "feat: add weekly plan and shopping list data models"
```

## Task 2: Build Weekly Plan Backend CRUD And Day-Attach Flow

**Files:**
- Modify: `src/intelligent_meal_planner/api/services.py`
- Modify: `src/intelligent_meal_planner/api/routers/__init__.py`
- Modify: `src/intelligent_meal_planner/api/main.py`
- Create: `src/intelligent_meal_planner/api/routers/weekly_plans.py`
- Create: `tests/api/test_weekly_plans_router.py`

- [ ] **Step 1: Write failing API tests for weekly-plan lifecycle**

```python
def test_create_weekly_plan_requires_auth_and_returns_empty_days(client, auth_header):
    response = client.post(
        "/api/weekly-plans",
        headers=auth_header,
        json={"name": "本周减脂计划"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "本周减脂计划"
    assert response.json()["days"] == []


def test_attach_finalized_meal_plan_snapshot_to_weekly_plan(client, auth_header, db_session, seeded_meal_chat_session):
    response = client.post(
        "/api/weekly-plans/1/days",
        headers=auth_header,
        json={
            "plan_date": "2026-04-07",
            "meal_plan_id": "plan-001",
            "source_session_id": seeded_meal_chat_session.id,
        },
    )
    assert response.status_code == 200
    assert response.json()["days"][0]["plan_date"] == "2026-04-07"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/api/test_weekly_plans_router.py -v`
Expected: FAIL because `/api/weekly-plans` routes do not exist.

- [ ] **Step 3: Add a focused weekly-plan service in `api/services.py`**

```python
class WeeklyPlanService:
    def create_plan(self, db: Session, user_id: int, name: str, notes: str | None):
        plan = models.WeeklyPlan(user_id=user_id, name=name, notes=notes)
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan

    def attach_day_from_session(self, db: Session, user_id: int, plan_id: int, plan_date: date, source_session_id: str):
        session = self._load_owned_finalized_session(db, user_id, source_session_id)
        day = models.WeeklyPlanDay(
            weekly_plan_id=plan_id,
            plan_date=plan_date,
            source_session_id=session.id,
            meal_plan_snapshot=session.final_plan,
            nutrition_snapshot=session.final_plan.get("nutrition", {}),
        )
        ...
```

- [ ] **Step 4: Expose CRUD and attach-day routes**

```python
router = APIRouter(prefix="/weekly-plans", tags=["周计划"])


@router.post("", response_model=WeeklyPlanResponse)
async def create_weekly_plan(...):
    ...


@router.get("", response_model=list[WeeklyPlanSummaryResponse])
async def list_weekly_plans(...):
    ...


@router.get("/{plan_id}", response_model=WeeklyPlanResponse)
async def get_weekly_plan(...):
    ...


@router.post("/{plan_id}/days", response_model=WeeklyPlanResponse)
async def attach_weekly_plan_day(...):
    ...


@router.delete("/{plan_id}/days/{day_id}", response_model=WeeklyPlanResponse)
async def remove_weekly_plan_day(...):
    ...
```

- [ ] **Step 5: Guard the main failure cases**

```python
if not session.final_plan:
    raise HTTPException(status_code=409, detail="Meal plan is not finalized")

if existing_day and not allow_replace:
    raise HTTPException(status_code=409, detail="Plan date already occupied")

if plan.user_id != user_id:
    raise HTTPException(status_code=404, detail="Weekly plan not found")
```

- [ ] **Step 6: Run weekly-plan API tests**

Run: `uv run pytest tests/api/test_weekly_plans_router.py tests/api/test_meal_chat_router.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/intelligent_meal_planner/api/services.py src/intelligent_meal_planner/api/routers/__init__.py src/intelligent_meal_planner/api/main.py src/intelligent_meal_planner/api/routers/weekly_plans.py tests/api/test_weekly_plans_router.py
git commit -m "feat: add weekly plan api and day attach flow"
```

## Task 3: Generate Backend-Saved Shopping Lists From Weekly Plans

**Files:**
- Modify: `src/intelligent_meal_planner/api/services.py`
- Modify: `src/intelligent_meal_planner/api/main.py`
- Create: `src/intelligent_meal_planner/api/routers/shopping_lists.py`
- Create: `tests/api/test_shopping_lists_router.py`

- [ ] **Step 1: Write failing API tests for shopping-list generation and mutation**

```python
def test_generate_shopping_list_from_weekly_plan(client, auth_header, seeded_weekly_plan):
    response = client.post(
        "/api/shopping-lists/generate",
        headers=auth_header,
        json={"weekly_plan_id": seeded_weekly_plan.id, "name": "第15周采购"},
    )
    assert response.status_code == 200
    assert response.json()["weekly_plan_id"] == seeded_weekly_plan.id
    assert response.json()["items"]


def test_toggle_shopping_list_item_checked_state(client, auth_header, seeded_shopping_list):
    response = client.patch(
        "/api/shopping-lists/1/items/1",
        headers=auth_header,
        json={"checked": True},
    )
    assert response.status_code == 200
    assert response.json()["items"][0]["checked"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/api/test_shopping_lists_router.py -v`
Expected: FAIL because the routes and generation service do not exist.

- [ ] **Step 3: Implement deterministic list generation from weekly-plan snapshots**

```python
class ShoppingListService:
    def generate_from_weekly_plan(self, db: Session, user_id: int, weekly_plan_id: int, name: str | None):
        plan = weekly_plan_service.get_owned_plan(db, user_id, weekly_plan_id)
        aggregated: dict[str, dict] = {}
        for day in plan.days:
            for meal in day.meal_plan_snapshot.get("meals", []):
                recipe = recipe_service.get_by_id(meal["recipe_id"])
                for ingredient in recipe.ingredients or []:
                    key = ingredient.strip().lower()
                    bucket = aggregated.setdefault(
                        key,
                        {"ingredient_name": ingredient, "display_amount": "", "source_refs": []},
                    )
                    bucket["source_refs"].append(
                        {
                            "plan_date": str(day.plan_date),
                            "meal_type": meal["meal_type"],
                            "recipe_name": meal["recipe_name"],
                        }
                    )
```

- [ ] **Step 4: Support both plan-derived items and manual additions**

```python
@router.post("/{shopping_list_id}/items", response_model=ShoppingListResponse)
async def add_manual_item(...):
    ...


@router.patch("/{shopping_list_id}/items/{item_id}", response_model=ShoppingListResponse)
async def update_item(...):
    ...


@router.delete("/{shopping_list_id}/items/{item_id}", response_model=ShoppingListResponse)
async def delete_item(...):
    ...
```

- [ ] **Step 5: Return both ingredient aggregate data and source traces in one payload**

```python
class ShoppingListItemResponse(BaseModel):
    id: int
    ingredient_name: str
    display_amount: str
    checked: bool
    category: str | None = None
    source_kind: str
    sources: list[dict] = Field(default_factory=list)
```

- [ ] **Step 6: Run shopping-list API tests**

Run: `uv run pytest tests/api/test_shopping_lists_router.py tests/api/test_weekly_plans_router.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/intelligent_meal_planner/api/services.py src/intelligent_meal_planner/api/main.py src/intelligent_meal_planner/api/routers/shopping_lists.py tests/api/test_shopping_lists_router.py
git commit -m "feat: add shopping list generation from weekly plans"
```

## Task 4: Add Frontend API Contracts And Weekly Plan State

**Files:**
- Modify: `frontend/src/api/index.ts`
- Create: `frontend/src/stores/weeklyPlan.ts`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/locales/zh.json`
- Modify: `frontend/src/locales/en.json`

- [ ] **Step 1: Add the TypeScript contracts for weekly plans and shopping lists**

```ts
export interface WeeklyPlanDay {
  id: number
  plan_date: string
  source_session_id?: string | null
  meal_plan_snapshot: MealPlan
  nutrition_snapshot: NutritionSummary
}

export interface WeeklyPlan {
  id: number
  name: string
  notes?: string | null
  days: WeeklyPlanDay[]
}

export interface ShoppingListItem {
  id: number
  ingredient_name: string
  display_amount: string
  checked: boolean
  category?: string | null
  source_kind: 'weekly-plan' | 'manual'
  sources: Array<{ plan_date: string; meal_type: string; recipe_name: string }>
}
```

- [ ] **Step 2: Add weekly-plan and shopping-list API clients**

```ts
export const weeklyPlanApi = {
  list: () => api.get<WeeklyPlanSummary[]>('/weekly-plans'),
  create: (payload: { name: string; notes?: string }) => api.post<WeeklyPlan>('/weekly-plans', payload),
  getById: (id: number) => api.get<WeeklyPlan>(`/weekly-plans/${id}`),
  attachDay: (id: number, payload: WeeklyPlanAttachPayload) => api.post<WeeklyPlan>(`/weekly-plans/${id}/days`, payload),
  removeDay: (id: number, dayId: number) => api.delete<WeeklyPlan>(`/weekly-plans/${id}/days/${dayId}`),
}
```

```ts
export const shoppingListApi = {
  list: () => api.get<ShoppingListSummary[]>('/shopping-lists'),
  generate: (payload: { weekly_plan_id: number; name?: string }) => api.post<ShoppingList>('/shopping-lists/generate', payload),
  getById: (id: number) => api.get<ShoppingList>(`/shopping-lists/${id}`),
  addItem: (id: number, payload: { ingredient_name: string; display_amount?: string }) =>
    api.post<ShoppingList>(`/shopping-lists/${id}/items`, payload),
  updateItem: (id: number, itemId: number, payload: { checked?: boolean; display_amount?: string }) =>
    api.patch<ShoppingList>(`/shopping-lists/${id}/items/${itemId}`, payload),
}
```

- [ ] **Step 3: Create a focused weekly-plan store**

```ts
export const useWeeklyPlanStore = defineStore('weekly-plan', () => {
  const plans = ref<WeeklyPlanSummary[]>([])
  const activePlan = ref<WeeklyPlan | null>(null)
  const loading = ref(false)

  async function loadPlans() { ... }
  async function createPlan(name: string, notes = '') { ... }
  async function openPlan(id: number) { ... }
  async function attachDay(planId: number, payload: WeeklyPlanAttachPayload) { ... }

  return { plans, activePlan, loading, loadPlans, createPlan, openPlan, attachDay }
})
```

- [ ] **Step 4: Add a dedicated weekly-plan route**

```ts
{
  path: '/weekly-plan',
  name: 'weekly-plan',
  component: () => import('@/views/WeeklyPlanView.vue')
}
```

- [ ] **Step 5: Add i18n keys for plan creation, attach flow, list generation, and dual-view labels**

```json
"weekly_plan": {
  "title": "周计划",
  "create": "新建周计划",
  "attach_day": "加入周计划",
  "empty_desc": "先把满意的单日方案加入这里，再生成采购清单。"
}
```

- [ ] **Step 6: Run the frontend build**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add frontend/src/api/index.ts frontend/src/stores/weeklyPlan.ts frontend/src/router/index.ts frontend/src/locales/zh.json frontend/src/locales/en.json
git commit -m "feat: add weekly plan frontend contracts and state"
```

## Task 5: Add The Weekly Plan Management Page And Entry Points

**Files:**
- Create: `frontend/src/views/WeeklyPlanView.vue`
- Modify: `frontend/src/views/MealPlanView.vue`
- Modify: `frontend/src/views/HistoryView.vue`
- Modify: `frontend/src/views/HomeView.vue`

- [ ] **Step 1: Add the weekly-plan page shell**

```vue
<template>
  <div class="weekly-plan-page">
    <header class="page-header">
      <h1>{{ $t('weekly_plan.title') }}</h1>
      <p class="subtitle">{{ $t('weekly_plan.subtitle') }}</p>
    </header>

    <section v-if="activePlan" class="week-grid">
      <article v-for="day in activePlan.days" :key="day.id" class="day-card">
        <h3>{{ formatDate(day.plan_date) }}</h3>
        <div v-for="meal in day.meal_plan_snapshot.meals" :key="meal.recipe_id">{{ meal.recipe_name }}</div>
      </article>
    </section>
  </div>
</template>
```

- [ ] **Step 2: Add “加入周计划” from finalized meal-chat results**

```ts
async function attachCurrentPlanToWeeklyPlan(planId: number, planDate: string) {
  if (!currentSession.value?.meal_plan || !finalPlan.value) return
  await weeklyPlanStore.attachDay(planId, {
    plan_date: planDate,
    meal_plan_id: finalPlan.value.id,
    source_session_id: currentSession.value.session_id
  })
}
```

- [ ] **Step 3: Add the same attach entry from history cards**

```vue
<el-button plain @click="openAttachDialog(item)">
  {{ $t('weekly_plan.attach_day') }}
</el-button>
```

- [ ] **Step 4: Keep the first version simple and explicit**

```ts
// V1 only supports explicit day assignment.
const selectableDates = ref<string[]>([])
const selectedPlanId = ref<number | null>(null)
const selectedPlanDate = ref('')
```

- [ ] **Step 5: Add homepage navigation into the new loop**

```vue
<router-link to="/weekly-plan">
  <el-button plain size="large">{{ $t('weekly_plan.title') }}</el-button>
</router-link>
```

- [ ] **Step 6: Run the frontend build**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add frontend/src/views/WeeklyPlanView.vue frontend/src/views/MealPlanView.vue frontend/src/views/HistoryView.vue frontend/src/views/HomeView.vue
git commit -m "feat: add weekly plan page and attach entry points"
```

## Task 6: Replace The Local Shopping Page With A Persisted Dual-View Experience

**Files:**
- Modify: `frontend/src/stores/shopping.ts`
- Modify: `frontend/src/views/ShoppingListView.vue`
- Modify: `frontend/src/api/index.ts`
- Modify: `frontend/src/locales/zh.json`
- Modify: `frontend/src/locales/en.json`

- [ ] **Step 1: Refactor the shopping store to use backend records**

```ts
export const useShoppingStore = defineStore('shopping', () => {
  const lists = ref<ShoppingListSummary[]>([])
  const activeList = ref<ShoppingList | null>(null)
  const viewMode = ref<'ingredients' | 'sources'>('ingredients')

  async function loadLists() { ... }
  async function openList(id: number) { ... }
  async function generateFromWeeklyPlan(weeklyPlanId: number, name = '') { ... }
  async function toggleItem(itemId: number, checked: boolean) { ... }

  return { lists, activeList, viewMode, loadLists, openList, generateFromWeeklyPlan, toggleItem }
})
```

- [ ] **Step 2: Redesign the shopping page around one active persisted list**

```vue
<el-segmented v-model="viewMode" :options="viewModeOptions" />

<template v-if="viewMode === 'ingredients'">
  <article v-for="item in activeList?.items" :key="item.id">
    <span>{{ item.ingredient_name }}</span>
    <span>{{ item.display_amount }}</span>
  </article>
</template>

<template v-else>
  <article v-for="item in activeList?.items" :key="item.id">
    <h3>{{ item.ingredient_name }}</h3>
    <ul>
      <li v-for="source in item.sources" :key="`${item.id}-${source.plan_date}-${source.recipe_name}`">
        {{ source.plan_date }} / {{ source.meal_type }} / {{ source.recipe_name }}
      </li>
    </ul>
  </article>
</template>
```

- [ ] **Step 3: Preserve manual item entry, but write to the backend**

```ts
async function handleAddItem() {
  if (!activeList.value || !newItemName.value.trim()) return
  await shoppingStore.addItem(activeList.value.id, {
    ingredient_name: newItemName.value.trim(),
    display_amount: newItemAmount.value.trim(),
  })
}
```

- [ ] **Step 4: Add the “from weekly plan” generation CTA**

```vue
<el-button type="primary" @click="$router.push('/weekly-plan')">
  {{ $t('shopping.go_weekly_plan') }}
</el-button>
```

- [ ] **Step 5: Remove browser-local persistence assumptions**

```ts
// Delete localStorage bootstrap and watch-based persistence from the store.
// The backend response becomes the only source of truth.
```

- [ ] **Step 6: Run the frontend build**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add frontend/src/stores/shopping.ts frontend/src/views/ShoppingListView.vue frontend/src/api/index.ts frontend/src/locales/zh.json frontend/src/locales/en.json
git commit -m "feat: replace local shopping list with persisted weekly-plan lists"
```

## Task 7: Verify The Full Closure Flow End To End

**Files:**
- Modify: `tests/api/test_weekly_plans_router.py`
- Modify: `tests/api/test_shopping_lists_router.py`
- Modify: `frontend/src/views/MealPlanView.vue`
- Modify: `frontend/src/views/WeeklyPlanView.vue`
- Modify: `frontend/src/views/ShoppingListView.vue`

- [ ] **Step 1: Add one backend happy-path test that covers the closure chain**

```python
def test_user_can_attach_session_to_weekly_plan_then_generate_shopping_list(client, auth_header, finalized_session):
    create_plan = client.post("/api/weekly-plans", headers=auth_header, json={"name": "第15周"})
    plan_id = create_plan.json()["id"]

    attach = client.post(
        f"/api/weekly-plans/{plan_id}/days",
        headers=auth_header,
        json={"plan_date": "2026-04-08", "meal_plan_id": "plan-001", "source_session_id": finalized_session.id},
    )
    assert attach.status_code == 200

    generated = client.post(
        "/api/shopping-lists/generate",
        headers=auth_header,
        json={"weekly_plan_id": plan_id},
    )
    assert generated.status_code == 200
    assert generated.json()["items"]
```

- [ ] **Step 2: Run the targeted backend suite**

Run: `uv run pytest tests/api/test_weekly_plans_router.py tests/api/test_shopping_lists_router.py tests/api/test_meal_chat_router.py -v`
Expected: PASS

- [ ] **Step 3: Run the broader backend regression suite**

Run: `uv run pytest tests/api tests/meal_chat -v`
Expected: PASS

- [ ] **Step 4: Run the frontend production build**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 5: Perform manual smoke verification**

Run:

```bash
uv run python main.py api
cd frontend && npm run dev
```

Expected:
- create or reuse a finalized meal-chat session
- attach it to a weekly plan with an explicit date
- open `/weekly-plan` and confirm the day snapshot renders
- generate a shopping list from that weekly plan
- open `/shopping-list` and confirm ingredient view and source view both render

- [ ] **Step 6: Commit**

```bash
git add tests/api/test_weekly_plans_router.py tests/api/test_shopping_lists_router.py frontend/src/views/MealPlanView.vue frontend/src/views/WeeklyPlanView.vue frontend/src/views/ShoppingListView.vue
git commit -m "test: verify weekly plan and shopping closure flow"
```

## Notes For The Implementer

- Reuse `MealChatSession.final_plan` as the day-snapshot source. Do not recalculate targets when attaching to a weekly plan.
- Do not introduce Alembic in this scope. This project currently relies on `metadata.create_all`; keep the storage change aligned with that reality.
- Ingredient amounts in V1 can be best-effort strings derived from `Recipe.ingredients`. Do not block the feature on structured quantity parsing.
- If a recipe has no ingredient list, still allow shopping-list generation and create a fallback source-only row so the plan stays explainable.
- Keep weekly-plan ownership checks strict. A user must never be able to attach or read another user's plan or list.
- Avoid frontend over-abstraction. One weekly-plan store and one shopping store are enough for V1.
