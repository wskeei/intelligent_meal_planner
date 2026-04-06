# Weekly Plan Shopping Closure Review

## Scope

- Reviewed worktree: `.worktrees/weekly-plan-shopping-closure`
- Compared against plan: `docs/superpowers/plans/2026-04-06-weekly-plan-and-shopping-closure.md`
- Reviewed commits:
  - `3d33491 feat: add weekly plan and shopping list backend`
  - `f16c0c0 feat: add weekly plan and persisted shopping ui`
  - `8a12aa3 test: verify weekly plan shopping closure flow`

## Findings

### High: aggregated shopping quantities are incorrect for repeated ingredients

- Files:
  - `src/intelligent_meal_planner/api/services.py:796`
  - `src/intelligent_meal_planner/api/services.py:822`
- Problem:
  - The ingredient aggregation logic only keeps the first non-empty `display_amount` for an ingredient key and then appends more source references without combining amounts.
  - That means a weekly plan containing `鸡胸肉 200g` on one day and `鸡胸肉 300g` on another still produces a single row with `display_amount = 200g`.
- Impact:
  - The list is visually aggregated, but the quantity shown to the user is wrong for actual purchasing.
  - This violates the practical meaning of an "ingredient aggregate view" and will understate shopping needs whenever ingredients repeat across days.
- Evidence:
  - A direct service-level check in the worktree produced one aggregated `鸡胸肉` row with `display_amount: '200g'` while the source list contained two separate day references.
- Recommendation:
  - Either aggregate quantities when they are parseable, or explicitly surface multiple amounts in the aggregate row instead of silently keeping the first one.

### Medium: the default attach date is off by one day for users west of UTC

- File:
  - `frontend/src/views/WeeklyPlanView.vue:181`
- Problem:
  - The default date is initialized with `new Date().toISOString().slice(0, 10)`, which derives the date from UTC rather than the user's local calendar day.
- Impact:
  - For users in timezones west of UTC, the prefilled date can become tomorrow late in the day.
  - Example: a local time of `2026-04-06 20:00` in `UTC-07:00` produces an ISO date slice of `2026-04-07`.
  - That makes it easy to attach a meal plan to the wrong day without noticing.
- Evidence:
  - Reproduced with `node`:
  - Intended local date: `2026-04-06`
  - `toISOString().slice(0, 10)`: `2026-04-07`
- Recommendation:
  - Build the default date from local date parts instead of UTC serialization.

### Medium: weekly plans and shopping lists never update their parent `updated_at` on child mutations

- Files:
  - `src/intelligent_meal_planner/api/services.py:654`
  - `src/intelligent_meal_planner/api/services.py:677`
  - `src/intelligent_meal_planner/api/services.py:717`
  - `src/intelligent_meal_planner/api/services.py:876`
  - `src/intelligent_meal_planner/api/services.py:922`
  - `src/intelligent_meal_planner/api/services.py:946`
  - `src/intelligent_meal_planner/api/services.py:967`
- Problem:
  - List ordering is based on parent `updated_at`, but attach/remove day operations only mutate `WeeklyPlanDay`, and add/update/delete item operations only mutate `ShoppingListItem`.
  - The parent `WeeklyPlan` and `ShoppingList` rows are never touched during those mutations, so their `updated_at` timestamps stay unchanged.
- Impact:
  - "Recently modified" ordering becomes stale.
  - Timestamps shown or inferred from summaries no longer reflect real activity.
  - This gets worse as users manage multiple weekly plans and shopping lists.
- Evidence:
  - A direct service-level check in the worktree showed identical `updated_at` timestamps before and after:
  - attaching a day to a weekly plan
  - toggling a shopping-list item
- Recommendation:
  - Explicitly bump the parent row timestamp whenever a child mutation changes the plan or list contents.

### Medium: expected conflict and failure paths have no user-facing handling in the new pages

- Files:
  - `frontend/src/views/WeeklyPlanView.vue:222`
  - `frontend/src/views/WeeklyPlanView.vue:240`
  - `frontend/src/views/WeeklyPlanView.vue:257`
  - `frontend/src/views/WeeklyPlanView.vue:262`
  - `frontend/src/views/ShoppingListView.vue:165`
  - `frontend/src/views/ShoppingListView.vue:183`
  - `frontend/src/views/ShoppingListView.vue:194`
  - `frontend/src/views/ShoppingListView.vue:198`
- Problem:
  - The new async actions call store methods inside `try/finally` or bare `await` flows but do not catch and present backend errors.
  - This is especially relevant because the backend has expected business-rule failures, for example duplicate day assignment returns `409 Plan date already occupied`.
- Impact:
  - Users get no inline explanation when a known conflict happens.
  - In practice this degrades into silent failure plus console noise, which is a poor fit for a management workflow.
- Recommendation:
  - Catch API failures in these views and surface concise messages for expected cases such as duplicate day conflicts and missing resources.

## Verification

- `uv run pytest tests/api -v`
  - Passed
- `uv run pytest tests/meal_chat -v`
  - Passed
- `cd frontend && npm run build`
  - Passed

## Summary

The feature is broadly integrated and the main happy-path works, but it is not yet ready to treat as fully correct against the intended workflow. The biggest functional gap is that the generated shopping list can display incorrect aggregated quantities, which undermines the core value of the procurement step. The date default and mutation timestamp issues are also real product bugs, and the new views still need user-facing handling for expected API conflicts.
