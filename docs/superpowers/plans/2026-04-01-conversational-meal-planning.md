# Conversational Meal Planning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用“营养师多轮对话 + 隐藏目标量化 + 预算硬约束”替换现有手动宏量滑块式配餐流程，只保留对话式入口。

**Architecture:** 后端新增会话持久化、DeepSeek 结构化抽取器、隐藏目标映射器和严格预算编排器；前端把 `MealPlanView` 重构为聊天页，并把用户资料改为服务端真源。RL 模型继续复用，但推理模式必须改成严格预算，不允许超预算兜底。

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, Vue 3, Pinia, Element Plus, DeepSeek(OpenAI-compatible), MaskablePPO, pytest

---

### Task 1: Make User Profile a Server-Side Source of Truth

**Files:**
- Create: `tests/api/conftest.py`
- Create: `tests/api/test_auth_profile.py`
- Modify: `src/intelligent_meal_planner/api/routers/auth.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/api/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from intelligent_meal_planner.api.main import app
from intelligent_meal_planner.db.database import Base, get_db


@pytest.fixture()
def client(tmp_path):
    db_file = tmp_path / "auth-profile.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_header(client):
    register_payload = {
        "username": "planner_user",
        "email": "planner@example.com",
        "password": "secret123",
        "age": 24,
        "gender": "male",
        "height": 175,
        "weight": 68,
        "activity_level": "moderate",
        "health_goal": "healthy",
    }
    client.post("/api/auth/register", json=register_payload)
    token_response = client.post(
        "/api/auth/token",
        data={"username": "planner_user", "password": "secret123"},
    )
    token = token_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

```python
# tests/api/test_auth_profile.py
def test_me_returns_full_profile(client, auth_header):
    response = client.get("/api/auth/me", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "planner_user"
    assert data["gender"] == "male"
    assert data["height"] == 175
    assert data["weight"] == 68
    assert data["activity_level"] == "moderate"
    assert data["health_goal"] == "healthy"


def test_patch_profile_updates_fields(client, auth_header):
    payload = {
        "age": 25,
        "weight": 70,
        "activity_level": "active",
        "health_goal": "gain_muscle",
    }
    response = client.patch(
        "/api/auth/me/profile",
        json=payload,
        headers=auth_header,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["age"] == 25
    assert data["weight"] == 70
    assert data["activity_level"] == "active"
    assert data["health_goal"] == "gain_muscle"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/api/test_auth_profile.py -v`

Expected: FAIL because `GET /api/auth/me` does not include full profile fields and `PATCH /api/auth/me/profile` does not exist.

- [ ] **Step 3: Implement the profile response and update endpoint**

```python
# src/intelligent_meal_planner/api/routers/auth.py
from pydantic import BaseModel, Field


class UserProfileUpdate(BaseModel):
    age: Optional[int] = Field(default=None, ge=10, le=100)
    gender: Optional[str] = Field(default=None)
    height: Optional[float] = Field(default=None, ge=100, le=250)
    weight: Optional[float] = Field(default=None, ge=30, le=250)
    activity_level: Optional[str] = Field(default=None)
    health_goal: Optional[str] = Field(default=None)


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    age: Optional[int]
    gender: Optional[str]
    height: Optional[float]
    weight: Optional[float]
    activity_level: Optional[str]
    health_goal: str

    class Config:
        from_attributes = True


@router.patch("/me/profile", response_model=UserOut)
async def update_profile(
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(current_user, field, value)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/api/test_auth_profile.py -v`

Expected: PASS for both tests.

- [ ] **Step 5: Commit**

```bash
git add tests/api/conftest.py tests/api/test_auth_profile.py src/intelligent_meal_planner/api/routers/auth.py
git commit -m "feat: add authenticated profile read and update APIs"
```

### Task 2: Add Hidden Target Mapping and Strict Budget RL Guard

**Files:**
- Create: `src/intelligent_meal_planner/meal_chat/__init__.py`
- Create: `src/intelligent_meal_planner/meal_chat/target_mapper.py`
- Create: `tests/meal_chat/test_target_mapper.py`
- Create: `tests/rl/test_strict_budget_env.py`
- Modify: `src/intelligent_meal_planner/rl/environment.py`
- Modify: `src/intelligent_meal_planner/tools/rl_model_tool.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/meal_chat/test_target_mapper.py
from intelligent_meal_planner.meal_chat.target_mapper import build_hidden_targets


def test_weight_loss_mapping_is_clamped_and_high_protein():
    profile = {
        "gender": "male",
        "age": 26,
        "height": 178,
        "weight": 80,
        "activity_level": "moderate",
    }
    targets = build_hidden_targets(profile, "lose_weight")

    assert 1200 <= targets["target_calories"] <= 3000
    assert 60 <= targets["target_protein"] <= 220
    assert 50 <= targets["target_carbs"] <= 400
    assert 30 <= targets["target_fat"] <= 120
    assert targets["target_protein"] > targets["target_fat"]


def test_gain_muscle_mapping_prefers_higher_carbs():
    profile = {
        "gender": "female",
        "age": 24,
        "height": 165,
        "weight": 58,
        "activity_level": "active",
    }
    targets = build_hidden_targets(profile, "gain_muscle")
    assert targets["target_carbs"] > targets["target_fat"]
```

```python
# tests/rl/test_strict_budget_env.py
from intelligent_meal_planner.rl.environment import MealPlanningEnv


def test_strict_budget_returns_empty_mask_when_no_affordable_action():
    env = MealPlanningEnv(
        budget_limit=1.0,
        training_mode=False,
        strict_budget=True,
    )
    env.reset()
    mask = env.action_masks()
    assert not mask.any()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/meal_chat/test_target_mapper.py tests/rl/test_strict_budget_env.py -v`

Expected: FAIL because the mapper does not exist and `MealPlanningEnv` does not support `strict_budget`.

- [ ] **Step 3: Implement hidden target mapping and strict-budget inference**

```python
# src/intelligent_meal_planner/meal_chat/target_mapper.py
ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

GOAL_MACROS = {
    "lose_weight": (0.35, 0.30, 0.35),
    "gain_muscle": (0.30, 0.45, 0.25),
    "maintain": (0.30, 0.40, 0.30),
    "healthy": (0.25, 0.45, 0.30),
}


def _clamp(value, low, high):
    return max(low, min(high, int(round(value))))


def build_hidden_targets(profile: dict, goal: str) -> dict:
    weight = profile["weight"]
    height = profile["height"]
    age = profile["age"]
    gender = profile["gender"]

    base = (10 * weight) + (6.25 * height) - (5 * age)
    bmr = base + 5 if gender == "male" else base - 161
    tdee = bmr * ACTIVITY_MULTIPLIERS.get(profile["activity_level"], 1.2)

    if goal == "lose_weight":
        calories = tdee - 500
    elif goal == "gain_muscle":
        calories = tdee + 300
    else:
        calories = tdee

    calories = _clamp(calories, 1200, 3000)
    protein_ratio, carb_ratio, fat_ratio = GOAL_MACROS.get(goal, GOAL_MACROS["healthy"])

    return {
        "target_calories": calories,
        "target_protein": _clamp((calories * protein_ratio) / 4, 60, 220),
        "target_carbs": _clamp((calories * carb_ratio) / 4, 50, 400),
        "target_fat": _clamp((calories * fat_ratio) / 9, 30, 120),
    }
```

```python
# src/intelligent_meal_planner/rl/environment.py
def __init__(
    self,
    recipes_path: Optional[str] = None,
    target_calories: float = 2000.0,
    target_protein: float = 100.0,
    target_carbs: float = 250.0,
    target_fat: float = 65.0,
    budget_limit: float = 100.0,
    disliked_tags: Optional[List[str]] = None,
    weight_nutrition: float = 1.0,
    weight_budget: float = 0.5,
    weight_variety: float = 0.3,
    training_mode: bool = True,
    price_scale: float = 1.0,
    custom_recipes: Optional[List[Dict]] = None,
    strict_budget: bool = False,
):
    ...
    self.strict_budget = strict_budget


def action_masks(self) -> np.ndarray:
    mask = np.zeros(self.action_space.n, dtype=bool)
    if self.current_step_idx >= self.max_steps:
        return mask

    current_meal_type = self._get_current_meal_type()
    remaining_budget = self.budget_limit - self.total_cost
    max_affordable_price = remaining_budget if self.strict_budget else remaining_budget + (self.budget_limit * 0.10)

    for i, recipe in enumerate(self.recipes):
        if current_meal_type not in recipe["meal_type"]:
            continue
        if i in self.selected_recipe_indices:
            continue
        if recipe["price"] <= max_affordable_price:
            mask[i] = True

    if self.strict_budget:
        return mask

    # keep the existing non-strict fallback logic here for training/backward compatibility
    ...
```

```python
# src/intelligent_meal_planner/tools/rl_model_tool.py
def _run(
    self,
    target_calories: int = 2000,
    target_protein: int = 100,
    target_carbs: int = 250,
    target_fat: int = 60,
    max_budget: float = 50.0,
    disliked_ingredients: Optional[List[str]] = None,
    preferred_tags: Optional[List[str]] = None,
    strict_budget: bool = True,
) -> str:
    self._load_model()
    self.env = MealPlanningEnv(
        target_calories=target_calories,
        target_protein=target_protein,
        target_carbs=target_carbs,
        target_fat=target_fat,
        budget_limit=max_budget,
        disliked_tags=disliked_ingredients or [],
        training_mode=False,
        strict_budget=strict_budget,
    )
    meal_plan, metrics, status = self._generate_meal_plan()
    return json.dumps(
        {
            "status": status,
            "meal_plan": meal_plan,
            "metrics": metrics,
        },
        ensure_ascii=False,
        indent=2,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/meal_chat/test_target_mapper.py tests/rl/test_strict_budget_env.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/intelligent_meal_planner/meal_chat/__init__.py src/intelligent_meal_planner/meal_chat/target_mapper.py src/intelligent_meal_planner/rl/environment.py src/intelligent_meal_planner/tools/rl_model_tool.py tests/meal_chat/test_target_mapper.py tests/rl/test_strict_budget_env.py
git commit -m "feat: add hidden target mapping and strict budget inference"
```

### Task 3: Persist Chat Sessions and Build the Conversation Orchestrator

**Files:**
- Create: `src/intelligent_meal_planner/meal_chat/types.py`
- Create: `src/intelligent_meal_planner/meal_chat/deepseek_extractor.py`
- Create: `src/intelligent_meal_planner/meal_chat/orchestrator.py`
- Create: `tests/meal_chat/test_orchestrator.py`
- Modify: `src/intelligent_meal_planner/db/models.py`

- [ ] **Step 1: Write the failing orchestrator tests**

```python
# tests/meal_chat/test_orchestrator.py
from types import SimpleNamespace

from intelligent_meal_planner.meal_chat.orchestrator import MealChatOrchestrator
from intelligent_meal_planner.meal_chat.types import ParsedTurn


class FakeExtractor:
    def __init__(self, parsed_turn):
        self.parsed_turn = parsed_turn

    def parse(self, *_args, **_kwargs):
        return self.parsed_turn


class FakeBudgetGuard:
    def __init__(self, feasible=True):
        self.feasible = feasible

    def check(self, *_args, **_kwargs):
        return self.feasible


class FakePlanner:
    def generate(self, *_args, **_kwargs):
        return {
            "id": "plan001",
            "created_at": "2026-04-01T10:00:00",
            "meals": [],
            "nutrition": {
                "total_calories": 1800,
                "total_protein": 120,
                "total_carbs": 180,
                "total_fat": 55,
                "total_price": 58,
                "calories_achievement": 100,
                "protein_achievement": 100,
                "budget_usage": 96.7,
            },
            "target": {
                "health_goal": "lose_weight",
                "target_calories": 1800,
                "target_protein": 120,
                "target_carbs": 180,
                "target_fat": 55,
                "max_budget": 60,
                "disliked_foods": [],
                "preferred_tags": [],
            },
            "score": 12.5,
        }
```

```python
def _user(**overrides):
    base = {
        "id": 1,
        "gender": None,
        "age": None,
        "height": None,
        "weight": None,
        "activity_level": None,
        "health_goal": "healthy",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _session(**overrides):
    base = {
        "status": "collecting_profile",
        "collected_slots": {},
        "hidden_targets": None,
        "final_plan": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_orchestrator_asks_for_missing_profile_before_anything_else():
    orchestrator = MealChatOrchestrator(
        extractor=FakeExtractor(
            ParsedTurn(
                profile_updates={},
                preference_updates={},
                acknowledged_restrictions=False,
            )
        ),
        budget_guard=FakeBudgetGuard(True),
        planner=FakePlanner(),
    )
    response = orchestrator.advance(_user(), _session(), "你好")
    assert response["status"] == "collecting_profile"
    assert "性别" in response["assistant_message"]


def test_orchestrator_rejects_budget_when_guard_fails():
    parsed = ParsedTurn(
        profile_updates={},
        preference_updates={
            "budget": 30,
            "health_goal": "lose_weight",
            "disliked_foods": ["香菜"],
            "preferred_tags": ["清淡"],
            "restrictions_answered": True,
        },
        acknowledged_restrictions=True,
    )
    orchestrator = MealChatOrchestrator(
        extractor=FakeExtractor(parsed),
        budget_guard=FakeBudgetGuard(False),
        planner=FakePlanner(),
    )
    user = _user(gender="male", age=24, height=175, weight=68, activity_level="moderate")
    response = orchestrator.advance(user, _session(status="collecting_preferences"), "预算 30 元，清淡一点，不吃香菜")
    assert response["status"] == "budget_rejected"
    assert "预算过低" in response["assistant_message"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/meal_chat/test_orchestrator.py -v`

Expected: FAIL because the orchestrator and parsed-turn types do not exist.

- [ ] **Step 3: Implement session models, parsed turn types, extractor, and orchestrator**

```python
# src/intelligent_meal_planner/db/models.py
from sqlalchemy import Boolean, Column, Float, Integer, String, Text, JSON, DateTime, ForeignKey
from datetime import datetime


class MealChatSession(Base):
    __tablename__ = "meal_chat_sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String, nullable=False, default="collecting_profile")
    collected_slots = Column(JSON, nullable=False, default=dict)
    hidden_targets = Column(JSON, nullable=True)
    final_plan = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MealChatMessage(Base):
    __tablename__ = "meal_chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("meal_chat_sessions.id"), nullable=False, index=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    stage = Column(String, nullable=False, default="collecting")
    created_at = Column(DateTime, default=datetime.utcnow)
```

```python
# src/intelligent_meal_planner/meal_chat/types.py
from pydantic import BaseModel, Field


class ParsedTurn(BaseModel):
    profile_updates: dict = Field(default_factory=dict)
    preference_updates: dict = Field(default_factory=dict)
    acknowledged_restrictions: bool = False
```

```python
# src/intelligent_meal_planner/meal_chat/deepseek_extractor.py
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
```

```python
# src/intelligent_meal_planner/meal_chat/orchestrator.py
from .target_mapper import build_hidden_targets


PROFILE_FIELDS = ["gender", "age", "height", "weight", "activity_level"]

QUESTION_TEXT = {
    "gender": "为了更准确地了解你的身体情况，我先确认一下你的性别。",
    "age": "告诉我一下你的年龄。",
    "height": "告诉我一下你的身高，单位厘米。",
    "weight": "告诉我一下你的体重，单位公斤。",
    "activity_level": "你平时的活动强度更接近久坐、轻度活动、中等活动，还是高活动量？",
    "health_goal": "你这段时间更偏向减脂、增肌、维持状态，还是日常健康饮食？",
    "budget": "这次你希望我把一天三餐预算控制在多少元以内？",
    "restrictions": "你有没有忌口、过敏或者明确不吃的食物？如果没有也可以直接告诉我。",
    "taste": "口味上你更偏向清淡、家常、重口一点，还是有什么特别想吃的方向？",
}


class MealChatOrchestrator:
    def __init__(self, extractor, budget_guard, planner):
        self.extractor = extractor
        self.budget_guard = budget_guard
        self.planner = planner

    def _missing_profile_field(self, user):
        for field in PROFILE_FIELDS:
            if getattr(user, field, None) in (None, ""):
                return field
        return None

    def _next_question_key(self, user, slots):
        missing_profile = self._missing_profile_field(user)
        if missing_profile:
            return missing_profile
        if not slots.get("health_goal") and not getattr(user, "health_goal", None):
            return "health_goal"
        if not slots.get("budget"):
            return "budget"
        if not slots.get("restrictions_answered"):
            return "restrictions"
        if "preferred_tags" not in slots:
            return "taste"
        return None

    def advance(self, user, session, user_message: str):
        parsed = self.extractor.parse(user_message)

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
            }

        goal = slots.get("health_goal") or getattr(user, "health_goal", "healthy")
        targets = build_hidden_targets(
            {
                "gender": user.gender,
                "age": user.age,
                "height": user.height,
                "weight": user.weight,
                "activity_level": user.activity_level,
            },
            goal,
        )
        session.hidden_targets = targets

        feasible = self.budget_guard.check(
            budget=slots["budget"],
            target_calories=targets["target_calories"],
            target_protein=targets["target_protein"],
            target_carbs=targets["target_carbs"],
            target_fat=targets["target_fat"],
        )
        if not feasible:
            session.status = "budget_rejected"
            return {
                "status": "budget_rejected",
                "assistant_message": "按你当前的需求，这个预算过低，需要适当提高预算后我再为你正式配餐。",
                "hidden_targets": None,
                "meal_plan": None,
            }

        meal_plan = self.planner.generate(
            goal=goal,
            budget=slots["budget"],
            disliked_foods=slots.get("disliked_foods", []),
            preferred_tags=slots.get("preferred_tags", []),
            hidden_targets=targets,
        )
        session.status = "completed"
        session.final_plan = meal_plan
        return {
            "status": "completed",
            "assistant_message": "我已经根据你的情况整理出一份预算内的一日三餐方案。",
            "hidden_targets": targets,
            "meal_plan": meal_plan,
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/meal_chat/test_orchestrator.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/intelligent_meal_planner/db/models.py src/intelligent_meal_planner/meal_chat/types.py src/intelligent_meal_planner/meal_chat/deepseek_extractor.py src/intelligent_meal_planner/meal_chat/orchestrator.py tests/meal_chat/test_orchestrator.py
git commit -m "feat: add meal chat persistence and orchestrator core"
```

### Task 4: Expose Conversational Meal Planning APIs and Remove Manual Planning Endpoints

**Files:**
- Create: `src/intelligent_meal_planner/api/routers/meal_chat.py`
- Create: `tests/api/test_meal_chat_router.py`
- Modify: `src/intelligent_meal_planner/api/schemas.py`
- Modify: `src/intelligent_meal_planner/api/routers/__init__.py`
- Modify: `src/intelligent_meal_planner/api/main.py`
- Modify: `src/intelligent_meal_planner/api/routers/meal_plans.py`
- Modify: `src/intelligent_meal_planner/api/services.py`

- [ ] **Step 1: Write the failing router tests**

```python
# tests/api/test_meal_chat_router.py
def test_create_session_returns_first_assistant_message(client, auth_header, monkeypatch):
    fake_response = {
        "session_id": "session001",
        "status": "collecting_profile",
        "messages": [
            {
                "role": "assistant",
                "content": "告诉我一下你的年龄。",
            }
        ],
        "meal_plan": None,
    }
    monkeypatch.setattr(
        "intelligent_meal_planner.api.routers.meal_chat.meal_chat_app.start_session",
        lambda db, user: fake_response,
    )
    response = client.post("/api/meal-chat/sessions", headers=auth_header)
    assert response.status_code == 200
    assert response.json()["messages"][0]["role"] == "assistant"


def test_send_message_returns_budget_rejected_status(client, auth_header, monkeypatch):
    fake_response = {
        "session_id": "session001",
        "status": "budget_rejected",
        "messages": [
            {"role": "assistant", "content": "按你当前的需求，这个预算过低，需要适当提高预算后我再为你正式配餐。"}
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
        json={"content": "预算 30 元"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "budget_rejected"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/api/test_meal_chat_router.py -v`

Expected: FAIL because `/api/meal-chat/*` routes do not exist.

- [ ] **Step 3: Implement chat schemas, chat router, history integration, and remove manual POST planning**

```python
# src/intelligent_meal_planner/api/schemas.py
class ChatMessage(BaseModel):
    role: str
    content: str
    created_at: Optional[datetime] = None


class MealChatMessageRequest(BaseModel):
    content: str = Field(..., min_length=1)


class MealChatSessionResponse(BaseModel):
    session_id: str
    status: str
    messages: List[ChatMessage]
    meal_plan: Optional[MealPlanResponse] = None
```

```python
# src/intelligent_meal_planner/api/routers/meal_chat.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import User
from .auth import get_current_user
from ..schemas import MealChatMessageRequest, MealChatSessionResponse
from ..services import meal_chat_app

router = APIRouter(prefix="/meal-chat", tags=["对话式配餐"])


@router.post("/sessions", response_model=MealChatSessionResponse)
async def create_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return meal_chat_app.start_session(db, current_user)


@router.get("/sessions/{session_id}", response_model=MealChatSessionResponse)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = meal_chat_app.get_session(db, current_user, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/sessions/{session_id}/messages", response_model=MealChatSessionResponse)
async def send_message(
    session_id: str,
    payload: MealChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return meal_chat_app.handle_message(db, current_user, session_id, payload.content)
```

```python
# src/intelligent_meal_planner/api/routers/__init__.py
from .recipes import router as recipes_router
from .meal_plans import router as meal_plans_router
from .meal_chat import router as meal_chat_router
from .auth import router as auth_router
```

```python
# src/intelligent_meal_planner/api/main.py
from .routers import recipes_router, meal_plans_router, meal_chat_router, auth_router

app.include_router(auth_router, prefix="/api")
app.include_router(recipes_router, prefix="/api")
app.include_router(meal_chat_router, prefix="/api")
app.include_router(meal_plans_router, prefix="/api")
```

```python
# src/intelligent_meal_planner/api/routers/meal_plans.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ...db.database import get_db
from ...db.models import User
from .auth import get_current_user
from ..schemas import MealPlanResponse
from ..services import meal_chat_app

router = APIRouter(prefix="/meal-plans", tags=["配餐历史"])


@router.get("", response_model=List[MealPlanResponse], summary="获取历史正式配餐")
async def get_history(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return meal_chat_app.get_completed_plans(db, current_user.id, limit)
```

```python
# src/intelligent_meal_planner/api/services.py
class BudgetGuardService:
    def check(self, budget, target_calories, target_protein, target_carbs, target_fat):
        result = feasibility_service.check_feasibility(
            budget=budget,
            target_calories=target_calories,
            target_protein=target_protein,
            target_carbs=target_carbs,
            target_fat=target_fat,
        )
        return (
            result.calories_feasibility >= 100
            and result.protein_feasibility >= 100
            and result.carbs_feasibility >= 100
            and result.fat_feasibility >= 100
        )


class StrictBudgetPlanner:
    def generate(self, goal, budget, disliked_foods, preferred_tags, hidden_targets):
        from ..tools.rl_model_tool import create_rl_model_tool

        tool = create_rl_model_tool()
        payload = json.loads(
            tool._run(
                target_calories=hidden_targets["target_calories"],
                target_protein=hidden_targets["target_protein"],
                target_carbs=hidden_targets["target_carbs"],
                target_fat=hidden_targets["target_fat"],
                max_budget=budget,
                disliked_ingredients=disliked_foods,
                preferred_tags=preferred_tags,
                strict_budget=True,
            )
        )
        if payload["status"] != "ok":
            raise ValueError("budget_infeasible")

        preferences = UserPreferences(
            health_goal=goal,
            target_calories=hidden_targets["target_calories"],
            target_protein=hidden_targets["target_protein"],
            target_carbs=hidden_targets["target_carbs"],
            target_fat=hidden_targets["target_fat"],
            max_budget=budget,
            disliked_foods=disliked_foods,
            preferred_tags=preferred_tags,
        )
        response = meal_plan_service._build_response(payload, preferences)
        if response.nutrition.total_price > budget:
            raise ValueError("budget_infeasible")
        return response.model_dump(mode="json")


class MealChatApplication:
    def __init__(self):
        self.orchestrator = MealChatOrchestrator(
            extractor=DeepSeekSlotExtractor(),
            budget_guard=BudgetGuardService(),
            planner=StrictBudgetPlanner(),
        )

    def _serialize_session(self, db: Session, session: MealChatSession):
        messages = (
            db.query(MealChatMessage)
            .filter(MealChatMessage.session_id == session.id)
            .order_by(MealChatMessage.created_at.asc())
            .all()
        )
        return {
            "session_id": session.id,
            "status": session.status,
            "messages": [
                {
                    "role": message.role,
                    "content": message.content,
                    "created_at": message.created_at,
                }
                for message in messages
            ],
            "meal_plan": session.final_plan,
        }

    def start_session(self, db: Session, user: User):
        session = MealChatSession(
            id=str(uuid.uuid4())[:8],
            user_id=user.id,
            status="collecting_profile",
            collected_slots={},
        )
        db.add(session)
        first_message = "我会先了解你的身体情况、当前目标、预算和口味偏好，再帮你整理一份预算内的一日三餐方案。"
        db.add(
            MealChatMessage(
                session_id=session.id,
                role="assistant",
                content=first_message,
                stage="collecting",
            )
        )
        db.commit()
        db.refresh(session)
        return self._serialize_session(db, session)

    def get_session(self, db: Session, user: User, session_id: str):
        session = (
            db.query(MealChatSession)
            .filter(MealChatSession.id == session_id, MealChatSession.user_id == user.id)
            .first()
        )
        if not session:
            return None
        return self._serialize_session(db, session)

    def handle_message(self, db: Session, user: User, session_id: str, content: str):
        session = (
            db.query(MealChatSession)
            .filter(MealChatSession.id == session_id, MealChatSession.user_id == user.id)
            .first()
        )
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
        db.refresh(session)
        return self._serialize_session(db, session)

    def get_completed_plans(self, db: Session, user_id: int, limit: int):
        rows = (
            db.query(MealChatSession)
            .filter(MealChatSession.user_id == user_id, MealChatSession.status == "completed")
            .order_by(MealChatSession.updated_at.desc())
            .limit(limit)
            .all()
        )
        return [row.final_plan for row in rows if row.final_plan]


meal_chat_app = MealChatApplication()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/api/test_meal_chat_router.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/intelligent_meal_planner/api/schemas.py src/intelligent_meal_planner/api/routers/meal_chat.py src/intelligent_meal_planner/api/routers/__init__.py src/intelligent_meal_planner/api/main.py src/intelligent_meal_planner/api/routers/meal_plans.py src/intelligent_meal_planner/api/services.py tests/api/test_meal_chat_router.py
git commit -m "feat: expose conversational meal planning APIs"
```

### Task 5: Sync Frontend Auth, Profile, and Chat APIs

**Files:**
- Modify: `frontend/src/api/index.ts`
- Modify: `frontend/src/stores/auth.ts`
- Modify: `frontend/src/stores/user.ts`
- Modify: `frontend/src/api/config.ts`

- [ ] **Step 1: Add failing TypeScript usages in the stores and API layer**

```ts
// frontend/src/api/index.ts
export interface ChatMessage {
  role: 'assistant' | 'user'
  content: string
  created_at?: string
}

export interface MealChatSession {
  session_id: string
  status: 'collecting_profile' | 'collecting_preferences' | 'budget_rejected' | 'completed'
  messages: ChatMessage[]
  meal_plan: MealPlan | null
}
```

```ts
// frontend/src/stores/user.ts
export interface UserProfile {
  username: string
  age: number | null
  gender: 'male' | 'female' | null
  height: number | null
  weight: number | null
  activityLevel: 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active' | null
  goal: 'lose_weight' | 'gain_muscle' | 'maintain' | 'healthy'
}
```

- [ ] **Step 2: Run the frontend build to capture current failures**

Run: `npm run build`

Workdir: `D:\Project\intelligent_meal_planner\frontend`

Expected: FAIL until the new API methods and store synchronization are fully wired.

- [ ] **Step 3: Implement auth header injection, full-profile hydration, and meal-chat API methods**

```ts
// frontend/src/api/index.ts
export interface UserProfilePatch {
  age?: number | null
  gender?: 'male' | 'female' | null
  height?: number | null
  weight?: number | null
  activity_level?: 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active' | null
  health_goal?: 'lose_weight' | 'gain_muscle' | 'maintain' | 'healthy'
}

import axios from 'axios'
import { API_BASE_URL } from './config'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const authApi = {
  me: () => api.get('/auth/me'),
  updateProfile: (payload: UserProfilePatch) => api.patch('/auth/me/profile', payload),
}

export const mealChatApi = {
  createSession: () => api.post<MealChatSession>('/meal-chat/sessions'),
  getSession: (sessionId: string) => api.get<MealChatSession>(`/meal-chat/sessions/${sessionId}`),
  sendMessage: (sessionId: string, content: string) =>
    api.post<MealChatSession>(`/meal-chat/sessions/${sessionId}/messages`, { content }),
}
```

```ts
// frontend/src/api/config.ts
const defaultApiBaseUrl = 'http://127.0.0.1:8000/api'

export const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() || defaultApiBaseUrl

export const AUTH_API_URL = `${API_BASE_URL}/auth`
```

```ts
// frontend/src/stores/auth.ts
import { authApi } from '@/api'

async function fetchUser() {
  if (!token.value) return
  try {
    const { data } = await authApi.me()
    user.value = data
  } catch (_error) {
    logout()
  }
}
```

```ts
// frontend/src/stores/user.ts
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { authApi } from '@/api'

export const useUserStore = defineStore('user', () => {
  const profile = ref<UserProfile>({
    username: '',
    age: null,
    gender: null,
    height: null,
    weight: null,
    activityLevel: null,
    goal: 'healthy',
  })

  const profileComplete = computed(() =>
    Boolean(
      profile.value.gender &&
      profile.value.age &&
      profile.value.height &&
      profile.value.weight &&
      profile.value.activityLevel
    )
  )

  function hydrateFromAuthUser(user: any) {
    if (!user) return
    profile.value = {
      username: user.username,
      age: user.age ?? null,
      gender: user.gender ?? null,
      height: user.height ?? null,
      weight: user.weight ?? null,
      activityLevel: user.activity_level ?? null,
      goal: user.health_goal ?? 'healthy',
    }
  }

  async function saveProfile(patch: Partial<UserProfile>) {
    const payload = {
      age: patch.age,
      gender: patch.gender,
      height: patch.height,
      weight: patch.weight,
      activity_level: patch.activityLevel,
      health_goal: patch.goal,
    }
    const { data } = await authApi.updateProfile(payload)
    hydrateFromAuthUser(data)
  }

  return {
    profile,
    profileComplete,
    hydrateFromAuthUser,
    saveProfile,
  }
})
```

- [ ] **Step 4: Run the frontend build to verify it passes**

Run: `npm run build`

Workdir: `D:\Project\intelligent_meal_planner\frontend`

Expected: PASS with no TypeScript errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/index.ts frontend/src/stores/auth.ts frontend/src/stores/user.ts frontend/src/api/config.ts
git commit -m "feat: wire frontend to authenticated profile and chat APIs"
```

### Task 6: Rebuild the Meal Plan Page as a Chat-Only Experience

**Files:**
- Modify: `frontend/src/views/MealPlanView.vue`
- Modify: `frontend/src/views/ProfileView.vue`
- Modify: `frontend/src/views/HomeView.vue`
- Modify: `frontend/src/locales/zh.json`
- Modify: `frontend/src/locales/en.json`

- [ ] **Step 1: Remove manual planning state and write the new chat view skeleton**

```vue
<!-- frontend/src/views/MealPlanView.vue -->
<template>
  <div class="meal-chat-page">
    <div class="page-header">
      <h1>{{ $t('meal_plan.chat_title') }}</h1>
      <p class="subtitle">{{ $t('meal_plan.chat_subtitle') }}</p>
    </div>

    <div class="chat-layout">
      <el-card class="chat-card" shadow="hover">
        <div class="messages" ref="messagesRef">
          <div
            v-for="(message, index) in messages"
            :key="`${message.role}-${index}`"
            :class="['message-row', message.role]"
          >
            <div class="bubble">{{ message.content }}</div>
          </div>
        </div>

        <div class="composer">
          <el-input
            v-model="draft"
            type="textarea"
            :rows="3"
            :placeholder="$t('meal_plan.chat_placeholder')"
            @keydown.enter.prevent="sendMessage"
          />
          <el-button type="primary" :loading="loading" @click="sendMessage">
            {{ $t('meal_plan.send') }}
          </el-button>
        </div>
      </el-card>

      <el-card v-if="finalPlan" class="result-card" shadow="hover">
        <h3>{{ $t('meal_plan.final_plan') }}</h3>
        <p>{{ $t('meal_plan.budget_safe_hint') }}</p>

        <div class="meal-list">
          <div v-for="meal in finalPlan.meals" :key="`${meal.meal_type}-${meal.recipe_id}`" class="meal-item">
            <div class="meal-type">{{ meal.meal_type }}</div>
            <div class="meal-name">{{ meal.recipe_name }}</div>
            <div class="meal-price">¥{{ meal.price }}</div>
          </div>
        </div>

        <div class="summary">
          <span>{{ $t('meal_plan.total_cost') }}: ¥{{ finalPlan.nutrition.total_price.toFixed(1) }}</span>
        </div>
      </el-card>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Implement the chat-only script logic**

```ts
// frontend/src/views/MealPlanView.vue <script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { mealChatApi, type ChatMessage, type MealPlan } from '@/api'

const sessionId = ref<string | null>(null)
const messages = ref<ChatMessage[]>([])
const draft = ref('')
const loading = ref(false)
const finalPlan = ref<MealPlan | null>(null)

async function bootstrapSession() {
  loading.value = true
  try {
    const { data } = await mealChatApi.createSession()
    sessionId.value = data.session_id
    messages.value = data.messages
    finalPlan.value = data.meal_plan
  } finally {
    loading.value = false
  }
}

async function sendMessage() {
  if (!sessionId.value || !draft.value.trim()) return
  loading.value = true
  const content = draft.value.trim()
  draft.value = ''
  messages.value.push({ role: 'user', content })

  try {
    const { data } = await mealChatApi.sendMessage(sessionId.value, content)
    messages.value = data.messages
    finalPlan.value = data.meal_plan
  } catch (_error) {
    ElMessage.error('发送失败，请稍后重试。')
  } finally {
    loading.value = false
    await nextTick()
  }
}

onMounted(bootstrapSession)
```

- [ ] **Step 3: Update profile and home screens to match the new product model**

```vue
<!-- frontend/src/views/ProfileView.vue -->
<template>
  <div class="profile-page">
    <div class="page-header">
      <h1>{{ $t('profile.title') }}</h1>
      <p class="subtitle">{{ $t('profile.subtitle') }}</p>
    </div>

    <el-card class="settings-card" shadow="hover">
      <el-form label-position="top" size="large">
        <el-form-item label="用户名">
          <el-input :model-value="profile.username" disabled />
        </el-form-item>
        <el-form-item :label="$t('auth.gender')">
          <el-radio-group v-model="localProfile.gender">
            <el-radio label="male">{{ $t('auth.male') }}</el-radio>
            <el-radio label="female">{{ $t('auth.female') }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="$t('auth.age')">
          <el-input-number v-model="localProfile.age" :min="10" :max="100" />
        </el-form-item>
        <el-form-item :label="$t('auth.height')">
          <el-input-number v-model="localProfile.height" :min="100" :max="250" />
        </el-form-item>
        <el-form-item :label="$t('auth.weight')">
          <el-input-number v-model="localProfile.weight" :min="30" :max="250" :step="0.5" />
        </el-form-item>
        <el-form-item :label="$t('auth.activity_level')">
          <el-select v-model="localProfile.activityLevel">
            <el-option label="久坐" value="sedentary" />
            <el-option label="轻度活动" value="light" />
            <el-option label="中等活动" value="moderate" />
            <el-option label="高活动量" value="active" />
            <el-option label="很高活动量" value="very_active" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('auth.goal')">
          <el-select v-model="localProfile.goal">
            <el-option label="减脂" value="lose_weight" />
            <el-option label="维持" value="maintain" />
            <el-option label="增肌" value="gain_muscle" />
            <el-option label="健康饮食" value="healthy" />
          </el-select>
        </el-form-item>
        <el-button type="primary" @click="save">{{ $t('common.save') }}</el-button>
      </el-form>
    </el-card>
  </div>
</template>
```

```ts
// frontend/src/views/ProfileView.vue <script setup lang="ts">
import { reactive, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const { profile } = storeToRefs(userStore)

const localProfile = reactive({
  username: '',
  age: null,
  gender: null,
  height: null,
  weight: null,
  activityLevel: null,
  goal: 'healthy',
})

watch(
  profile,
  (value) => {
    Object.assign(localProfile, value)
  },
  { immediate: true, deep: true }
)

async function save() {
  await userStore.saveProfile(localProfile)
  ElMessage.success('资料已更新')
}
```

```vue
<!-- frontend/src/views/HomeView.vue -->
<template>
  <div class="dashboard">
    <div class="header-section">
      <div class="greeting">
        <h1>{{ $t('dashboard.hello') }}, {{ profile.username }}!</h1>
        <p class="subtitle">{{ $t('dashboard.ready_msg') }}</p>
      </div>
    </div>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="12">
        <el-card shadow="hover" class="stat-card">
          <div class="label">{{ $t('dashboard.current_goal') }}</div>
          <div class="value text-cap">{{ profile.goal.replace('_', ' ') }}</div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover" class="stat-card">
          <div class="label">{{ $t('dashboard.profile_complete') }}</div>
          <div class="value">{{ profileComplete ? '100%' : '待补充' }}</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
```

```ts
// frontend/src/views/HomeView.vue <script setup lang="ts">
import { useUserStore } from '@/stores/user'
import { storeToRefs } from 'pinia'

const userStore = useUserStore()
const { profile, profileComplete } = storeToRefs(userStore)
```

- [ ] **Step 4: Update locale keys and verify the build**

```json
// frontend/src/locales/zh.json
{
  "meal_plan": {
    "chat_title": "营养师配餐对话",
    "chat_subtitle": "先聊清楚你的情况，再为你正式生成预算内的一日三餐方案",
    "chat_placeholder": "告诉我你的情况、预算或上一轮问题的答案",
    "send": "发送",
    "final_plan": "正式配餐结果",
    "budget_safe_hint": "以下方案已经按你当前预算进行了控制",
    "total_cost": "总花费"
  },
  "dashboard": {
    "profile_complete": "资料完整度"
  }
}
```

```json
// frontend/src/locales/en.json
{
  "meal_plan": {
    "chat_title": "Nutritionist Chat Planner",
    "chat_subtitle": "We will understand your situation first, then generate one budget-safe daily meal plan.",
    "chat_placeholder": "Tell me your situation, budget, or answer to the last question",
    "send": "Send",
    "final_plan": "Final Meal Plan",
    "budget_safe_hint": "The plan below has been constrained to your current budget.",
    "total_cost": "Total Cost"
  },
  "dashboard": {
    "profile_complete": "Profile Completeness"
  }
}
```

Run: `npm run build`

Workdir: `D:\Project\intelligent_meal_planner\frontend`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/MealPlanView.vue frontend/src/views/ProfileView.vue frontend/src/views/HomeView.vue frontend/src/locales/zh.json frontend/src/locales/en.json
git commit -m "feat: replace manual meal planning UI with chat experience"
```

### Task 7: Add Env Template, Remove Obsolete Product Surface, and Verify End-to-End

**Files:**
- Create: `.env.example`
- Modify: `README.md`
- Modify: `frontend/README.md`
- Modify: `src/intelligent_meal_planner/agents/crew.py`
- Modify: `src/intelligent_meal_planner/agents/user_profiler.py`
- Modify: `src/intelligent_meal_planner/agents/rl_chef.py`

- [ ] **Step 1: Add the environment template**

```env
# .env.example
DEEPSEEK_API_KEY=
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
```

- [ ] **Step 2: Update documentation to describe the new runtime flow**

~~~md
# README.md
## 对话式配餐

系统不再要求用户手动设置热量、蛋白质、碳水和脂肪。
用户进入配餐页后，将与“营养师”进行多轮对话：

1. 优先读取账户中的身体资料
2. 缺失资料时逐项追问并自动补全
3. 询问预算、忌口和口味偏好
4. 在后台映射隐藏营养目标
5. 使用严格预算模式调用 RL 模型
6. 若预算不足，明确提示用户提高预算

## DeepSeek 配置

将 `.env.example` 复制为 `.env`，并填写：

```env
DEEPSEEK_API_KEY=your_key_here
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
```

# frontend/README.md
## 智能配餐 (/meal-plan)

- 页面改为聊天式配餐流程
- 不再暴露热量、蛋白质、碳水和脂肪滑块
- 营养师会在信息足够后一次性生成正式配餐结果
- 当前预算不足时，页面只提示提高预算，不返回超预算方案
~~~

- [ ] **Step 3: Retire the old single-turn crew entry points from runtime usage**

```python
# src/intelligent_meal_planner/agents/crew.py
"""
This module is retained only for backward reference.
Runtime meal planning has moved to the conversational orchestrator in
`intelligent_meal_planner.meal_chat.orchestrator`.
"""
```

```python
# src/intelligent_meal_planner/agents/user_profiler.py
"""
Deprecated runtime entry. Profile collection is now handled by the
conversational session orchestrator and DeepSeek slot extractor.
"""
```

```python
# src/intelligent_meal_planner/agents/rl_chef.py
"""
Deprecated runtime entry. Final meal generation is now handled by the
strict-budget planner in `api.services.StrictBudgetPlanner`.
"""
```

- [ ] **Step 4: Run the backend verification suite**

Run: `uv run pytest tests/api tests/meal_chat tests/rl/test_strict_budget_env.py -v`

Expected: PASS for auth profile, orchestrator, router, target mapper, and strict-budget tests.

- [ ] **Step 5: Run the frontend verification suite**

Run: `npm run build`

Workdir: `D:\Project\intelligent_meal_planner\frontend`

Expected: PASS with no TypeScript or Vite build errors.

- [ ] **Step 6: Run an end-to-end manual smoke test**

Run: `uv run python main.py api`

Expected:
- API starts successfully
- login works
- `/meal-plan` opens a chat-only page
- missing body profile fields are asked one by one
- submitting a too-low budget returns the budget-too-low message
- submitting a sufficient budget returns a plan whose `total_price` is not greater than the user budget

- [ ] **Step 7: Commit**

```bash
git add .env.example README.md frontend/README.md src/intelligent_meal_planner/agents/crew.py src/intelligent_meal_planner/agents/user_profiler.py src/intelligent_meal_planner/agents/rl_chef.py
git commit -m "docs: document conversational meal planning runtime"
```
