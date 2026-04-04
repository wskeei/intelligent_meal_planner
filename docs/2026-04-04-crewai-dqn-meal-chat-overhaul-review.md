# CrewAI DQN Meal Chat Overhaul Review

Review target:

- Plan: `docs/superpowers/plans/2026-04-04-crewai-dqn-meal-chat-overhaul.md`
- Worktree: `.worktrees/crewai-dqn-meal-chat-overhaul`
- Branch: `feat/crewai-dqn-meal-chat-overhaul`

Verification performed:

- `uv run pytest tests/tools/test_rl_model_tool.py tests/test_main_cli.py tests/meal_chat/test_intake_runtime.py tests/meal_chat/test_crew_factory.py tests/meal_chat/test_crew_runner.py tests/meal_chat/test_orchestrator.py tests/api/test_meal_chat_router.py -v`
- `cd frontend && npm run build`
- Manual runtime probe of `CrewMealPlannerRunner` with an instrumented fake planner

Result:

- Targeted tests passed.
- Frontend build passed.
- There are still blocking gaps between the implementation and the plan.

## Findings

### 1. Blocking: Stage 2 is not actually driven by CrewAI outputs; the runner fabricates the final plan outside the crew

Plan Task 3 requires a real CrewAI planning stage where the crew runs specialist agents, calls the DQN planning tool, and returns typed results. The current implementation does not do that.

Evidence:

- `src/intelligent_meal_planner/meal_chat/crew_factory.py:10-38` defines `PlaceholderCrewLLM`, which ignores the conversation inputs and returns canned text.
- `src/intelligent_meal_planner/meal_chat/crew_factory.py:41-124` wires every agent to that placeholder LLM and does not configure a typed CrewAI output contract for the final result.
- `src/intelligent_meal_planner/meal_chat/crew_runner.py:79-88` falls back whenever the crew output is not parseable.
- `src/intelligent_meal_planner/meal_chat/crew_runner.py:104-115` then calls `planning_tool.generate(...)` directly in `_fallback_meal_plan()`, outside the CrewAI task graph.

Why this matters:

- The plan explicitly required “a real CrewAI `Crew` after the intake is complete”.
- The shipped runtime only uses CrewAI as a shell. The actual meal plan can be produced by runner fallback even when the crew itself returns only placeholder text.
- This hides CrewAI integration problems instead of exposing them.

Manual confirmation:

- An instrumented runtime probe showed the planner call originated from `CrewMealPlannerRunner._fallback_meal_plan`, not from `DQNMealPlanningTool._run`.

### 2. Blocking: `crew_trace` is synthetic status data, not the collaboration transcript required by the plan

The plan goal says the user should see the CrewAI collaboration trace / transcript. The current code persists and returns fabricated events instead of the actual runtime trace.

Evidence:

- `src/intelligent_meal_planner/meal_chat/crew_factory.py:125-136` hardcodes one static message per agent in `event_messages`.
- `src/intelligent_meal_planner/meal_chat/crew_runner.py:73-74` substitutes fallback events whenever the crew result does not include events.
- `src/intelligent_meal_planner/meal_chat/crew_runner.py:117-136` converts every configured agent into a `"completed"` event with a canned message.
- `src/intelligent_meal_planner/meal_chat/orchestrator.py:35-58` stores those events into `memory.crew_events` and returns them as `trace.crew_trace`.
- `src/intelligent_meal_planner/api/services.py:296-309` serializes `crew_events` straight into the HTTP response as `crew_trace`.

Why this matters:

- The frontend now shows a timeline, but it is not a real transcript of collaboration, tool calls, negotiation, or failure states.
- Even if the crew does nothing useful, the UI still reports that every agent completed its work.
- This does not satisfy the plan requirement that the collaboration trace be visible to users.

### 3. Medium: The typed-output contract required by the plan is still weak at the API boundary, and the new tests do not protect the real requirement

The plan called for typed CrewAI outputs and a typed session response carrying structured meal plans. The code introduces internal models, but the boundary that matters most still accepts arbitrary dictionaries.

Evidence:

- `src/intelligent_meal_planner/api/schemas.py:182-187` keeps `MealChatSessionResponse.meal_plan` as `Optional[dict]` instead of a typed `MealPlan | NegotiatedMealPlan | None` contract.
- `tests/meal_chat/test_crew_factory.py:1-12` only checks agent role names.
- `tests/meal_chat/test_crew_runner.py:5-28` uses a fake crew that already returns the expected dict and therefore never exercises the real CrewAI path.
- `tests/api/test_meal_chat_router.py:169-194` only checks that `crew_trace` is present, not that it is derived from actual CrewAI execution.

Why this matters:

- The current suite allows the placeholder/fallback implementation to pass while still missing the central behavior promised by the plan.
- The untyped API response also weakens validation for malformed or incomplete meal-plan payloads.

## Conclusion

This branch completed most of the file moves, API shape changes, and UI plumbing from the plan, but the core architectural promise is still not met: Stage 2 is not truly “CrewAI planning with visible collaboration output”. The current implementation wraps a placeholder crew around fallback logic that generates both the final plan and the displayed trace outside the actual CrewAI result path.
