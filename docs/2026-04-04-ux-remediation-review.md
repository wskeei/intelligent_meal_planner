# UX Remediation Review

Review target:

- Plan: `docs/superpowers/plans/2026-04-04-ux-remediation-plan.md`
- Worktree: `.worktrees/ux-remediation-2026-04-04`
- Branch: `feat/ux-remediation-2026-04-04`

Verification performed:

- `cd frontend && npm run build`
- Manual code review against the plan acceptance criteria and release checklist

Verification limits:

- Frontend build passed.
- Backend pytest-based verification was not executed because `pytest` is not available in the current environment.

Result:

- The branch covers most of the planned surface area.
- There are still requirement gaps that should be fixed before considering the UX remediation complete.

## Findings

### 1. Important: Registration still injects a default health goal, which violates the minimum-friction signup requirement

Task 3 requires registration to be reduced to minimum viable identity fields and explicitly says not to prefill sensitive or planning-related fields unless the user chooses them.

Evidence:

- `frontend/src/views/RegisterView.vue:51-56` still defines the signup payload with `health_goal: 'healthy'`.
- `frontend/src/views/RegisterView.vue:66-75` sends that same payload during registration.

Why this matters:

- The UI only shows `username`, `email`, and `password`, but the request still silently sets a planning preference.
- This is still a hidden default, so the implementation does not fully satisfy the plan's “minimum fields only” and “no misleading defaults” requirements.

Recommended change:

- Remove `health_goal` from the registration form payload entirely.
- Keep goal selection in profile completion or in the meal-planning chat, where the user explicitly chooses it.

### 2. Important: The chat status panel can show incorrect "missing information" because it treats natural-language questions as structured field keys

Task 4 requires the meal chat page to clearly show what is still missing and what the user should do next. The current implementation is not robust enough to guarantee that.

Evidence:

- `frontend/src/views/MealPlanView.vue:379-388` falls back to `openQuestions` when `known_facts.missing_fields` is absent, then maps each item through `fieldLabel()` and `fieldReason()`.
- `tests/api/test_meal_chat_session_metadata.py:42-47` shows that `open_questions` may contain natural-language prompts such as `你更偏好米饭还是面食？`, not field identifiers.

Why this matters:

- If `open_questions` contains user-facing questions instead of canonical field keys, the UI will try to translate them as `meal_plan.field_labels.<question>` and `meal_plan.field_reasons.<question>`.
- That breaks the plan requirement that the page explicitly and legibly communicates missing information and next actions.

Recommended change:

- Do not use `open_questions` as a fallback source for `missingItems`.
- Restrict `missingItems` to canonical missing field identifiers only.
- If the backend only has natural-language questions available, render them in the "next action" area as copy, not as missing-field cards.

### 3. Important: Locale coverage is still incomplete; English mode will leak Chinese chat text

Tasks 6 and 8 require consistent brand, language, and state coverage across the product. That is not fully true yet.

Evidence:

- `frontend/src/views/MealPlanView.vue:310-327` builds the reuse prefill draft with hardcoded Chinese text.
- `src/intelligent_meal_planner/api/services.py:343-348` seeds the first assistant message in Chinese.
- `src/intelligent_meal_planner/meal_chat/question_strategy.py:6-27` defines follow-up prompts in Chinese only.

Why this matters:

- In English locale, the shell and labels can appear in English while the core chat workflow still responds in Chinese.
- That directly conflicts with the plan requirement to remove mixed-language system messages and unify locale coverage.

Recommended change:

- Move the frontend reuse-prefill sentence generation into locale-backed strings.
- Decide whether the backend should be Chinese-only or locale-aware; if locale-aware is intended, the initial assistant message and follow-up prompts need a localization strategy instead of hardcoded Chinese.
- At minimum, align the shipped locale promise with actual runtime behavior so the product does not claim bilingual coverage it does not really provide.

### 4. Medium: Failure recovery still relies mainly on toast messages instead of inline, actionable guidance

Task 8 requires replacing toast-only recovery with inline guidance where the user can act. Several key flows still fail this requirement.

Evidence:

- `frontend/src/views/LoginView.vue:55-71` shows login failure only via `ElMessage`.
- `frontend/src/views/ProfileView.vue:168-176` shows profile save failure only via `ElMessage`.
- `frontend/src/views/MealPlanView.vue:499-525` shows session creation and chat-send failures only via `ElMessage`.

Why this matters:

- Toasts are transient and easy to miss.
- The user is not given an inline explanation, retry surface, or page-level recovery hint in those critical flows.
- This leaves Task 8 only partially implemented.

Recommended change:

- Add inline error state blocks near the relevant form or interaction area.
- Keep toast messages optional and secondary.
- Ensure each major failure state exposes a concrete next action such as retry, edit input, or check login/session state.

## Conclusion

The branch is close, but it is not yet fully aligned with the UX remediation plan. The highest-priority fixes are:

1. Remove the hidden default `health_goal` from signup.
2. Make the meal chat status panel strictly use structured missing-field data.
3. Resolve mixed-language behavior in the chat flow.
4. Add inline recovery guidance for critical failure states.
