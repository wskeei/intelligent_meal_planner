# Meal Chat Stuck Debug And Local Trace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复对话式配餐里“用户已回答但系统重复追问同一问题”的卡住问题，并把每轮对话与关键调试上下文落盘到本地 JSONL 文件，便于后续溯源。  
**Architecture:** 根因修复放在后端对话编排链路里；`MealChatOrchestrator` 先根据当前会话状态计算 `expected_slot`，再把它传给 `DeepSeekSlotExtractor`；抽取器增加确定性兜底规则，避免“没有，都能吃”这类短句因为缺少上文而解析失败。排障留痕单独实现为 `meal_chat` 下的本地 trace writer，由 `MealChatApplication` 在会话开始、消息处理成功、消息处理失败三个时机写入 JSONL，不改现有业务表结构。  
**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, Python `pathlib` / `json`

---

### Task 1: Reproduce The Stuck Conversation With Regression Tests

**Files:**
- Create: `tests/meal_chat/test_deepseek_extractor.py`
- Modify: `tests/meal_chat/test_orchestrator.py`
- Test: `tests/meal_chat/test_orchestrator.py`
- Test: `tests/meal_chat/test_deepseek_extractor.py`

- [ ] **Step 1: Add the failing orchestrator regression test**
- [ ] **Step 2: Add the failing extractor fallback regression test**
- [ ] **Step 3: Run tests to verify they fail**
- [ ] **Step 4: Commit the failing regression tests**

### Task 2: Make Slot Extraction Context-Aware And Deterministic

**Files:**
- Modify: `src/intelligent_meal_planner/meal_chat/types.py`
- Modify: `src/intelligent_meal_planner/meal_chat/deepseek_extractor.py`
- Modify: `src/intelligent_meal_planner/meal_chat/orchestrator.py`
- Test: `tests/meal_chat/test_orchestrator.py`
- Test: `tests/meal_chat/test_deepseek_extractor.py`

- [ ] **Step 1: Extend the parsed turn type to carry debug metadata**
- [ ] **Step 2: Implement expected-slot-aware fallback logic in the extractor**
- [ ] **Step 3: Pass the current slot into the extractor before merging the turn**
- [ ] **Step 4: Preserve the trace payload in all return branches**
- [ ] **Step 5: Run tests to verify they pass**
- [ ] **Step 6: Commit the root-cause fix**

### Task 3: Add Local JSONL Trace Logging For Session Replay And Debugging

**Files:**
- Create: `src/intelligent_meal_planner/meal_chat/local_trace.py`
- Create: `tests/meal_chat/test_local_trace.py`
- Modify: `src/intelligent_meal_planner/api/services.py`
- Modify: `.env.example`
- Modify: `README.md`
- Test: `tests/meal_chat/test_local_trace.py`

- [ ] **Step 1: Add the failing trace writer unit test**
- [ ] **Step 2: Run the trace test to verify it fails**
- [ ] **Step 3: Implement the local trace writer**
- [ ] **Step 4: Wire the trace writer into session start and message handling**
- [ ] **Step 5: Document the local trace directory**
- [ ] **Step 6: Run tests to verify the trace writer passes**
- [ ] **Step 7: Commit the local trace logging work**

### Task 4: Verify The Full Backend Flow Before Hand-off

**Files:**
- Test: `tests/meal_chat/test_orchestrator.py`
- Test: `tests/meal_chat/test_deepseek_extractor.py`
- Test: `tests/meal_chat/test_local_trace.py`
- Test: `tests/api/test_meal_chat_router.py`

- [ ] **Step 1: Run the focused meal-chat backend suite**
- [ ] **Step 2: Run one manual API smoke test**
- [ ] **Step 3: Inspect the generated trace file**
- [ ] **Step 4: Commit the verification checkpoint**
