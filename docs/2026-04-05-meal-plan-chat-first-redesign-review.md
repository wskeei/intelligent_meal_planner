# Meal Plan Chat-First Redesign Review

Review target:

- Plan: `docs/superpowers/plans/2026-04-05-meal-plan-chat-first-redesign.md`
- Spec: `docs/superpowers/specs/2026-04-05-meal-plan-chat-first-redesign-design.md`
- Worktree: `.worktrees/feat-meal-plan-chat-first-redesign`
- Branch: `feat/meal-plan-chat-first-redesign`
- Head commit: `a2160d3`

Verification performed:

- `cd .worktrees/feat-meal-plan-chat-first-redesign/frontend && npm run build`
- Manual code review against the plan tasks, target outcomes, and acceptance criteria

Verification limits:

- Frontend production build passed.
- No browser/manual interaction pass was executed in this review session, so the findings below are based on code inspection plus build verification.

Result:

- The branch covers the planned files and removes the old hero-plus-trace-card structure.
- There are still requirement gaps against the approved chat-first redesign direction.

## Findings

### 1. Important: The desktop layout still gives the dominant column to the status rail instead of the chat surface

The plan's primary outcome is explicit: desktop should use a dominant primary chat column with a narrow secondary rail. The current implementation inverts that layout.

Evidence:

- `frontend/src/views/MealPlanView.vue:19-75` renders the `context-rail` before `chat-main` in the desktop grid.
- `frontend/src/views/MealPlanView.vue:937-940` defines `grid-template-columns: minmax(0, 1.7fr) minmax(290px, 0.88fr)`.

Why this matters:

- In CSS Grid, the first child takes the first column. That means the status rail gets the `1.7fr` column while the chat surface is pushed into the narrower `0.88fr` column.
- This directly conflicts with Task 1 and Task 6, which require chat to become the primary column and the support context to become secondary.
- It also weakens the user’s core request that the page should be “以 chat 为主”.

Recommended change:

- Either swap the DOM order so `chat-main` is first and `context-rail` is second, or swap the column sizes so the chat surface receives the wider track.
- Recheck desktop focus order after the change so keyboard flow also reaches the chat first.

### 2. Medium: “收起状态” does not actually create a much cleaner chat view because most of the heavy status module stays visible

The approved direction was not just “hide some details”; it was to let the user collapse status when they want a cleaner, chat-first page. The current collapse behavior is too shallow to satisfy that requirement.

Evidence:

- `frontend/src/components/meal-chat/MealChatStatusPanel.vue:17-25` keeps the next-step block and the full action cluster visible at all times.
- `frontend/src/components/meal-chat/MealChatStatusPanel.vue:27-48` only hides the known-items and missing-items sections behind `v-show="expanded"`.
- `frontend/src/components/meal-chat/MealChatStatusPanel.vue:87-94` keeps the same large dark card shell and visual weight in both states.

Why this matters:

- Even in the collapsed state, the page still shows a large dark panel with summary text, next-step copy, and multiple buttons.
- That means the user does not really get the “cleaner chat view” requested in the review discussion and described in Task 2.
- This is especially noticeable because the status module remains visually heavier than the chat card.

Recommended change:

- Define a truly compact collapsed state: one short status line, one badge, and one expand control.
- Move the heavier next-step text and secondary actions into the expanded state, keeping only the single primary CTA visible when collapsed.

### 3. Medium: The system-trace entry is still too content-heavy on the main page, especially in English locale

Task 3 requires “系统过程” to be demoted to a small secondary trigger. The current implementation still turns that surface back into content instead of a lightweight entry point.

Evidence:

- `frontend/src/views/MealPlanView.vue:67-72` renders a persistent `context-secondary` block with both a trigger and explanatory text.
- `frontend/src/views/MealPlanView.vue:541-547` makes `traceCallout` fall back to the full `trace_unavailable_locale` warning when English locale has trace data.
- `frontend/src/locales/en.json:62-70` defines that warning as a full sentence-length explanation rather than a short secondary label.

Why this matters:

- In the exact case where trace data exists in English locale, the main page starts showing a long warning sentence under the “View process” trigger.
- That undermines the Task 3 goal of reducing “系统过程” to a small secondary entry point.
- It also works against Task 4’s copy-reduction goal by bringing a low-priority explanatory paragraph back into the main page.

Recommended change:

- Keep the main-page process surface to a short trigger plus, at most, a very short one-line hint.
- Move the full locale warning entirely inside the drawer or result overlay, where the user has already opted into viewing process details.

## Open Questions / Assumptions

- This review assumes the approved plan is the source of truth, not the current visual outcome in the worktree.
- No browser pass was executed here, so there may be additional polish or responsive issues beyond the plan-level gaps listed above.

## Conclusion

The branch is directionally close, but it is not yet fully compliant with the approved redesign plan. The highest-priority fix is to restore a true chat-first desktop layout by making the chat column wider and visually primary. After that, the status collapse and system-trace entry both still need another simplification pass to meet the “简洁为主” requirement that drove the redesign.
