# Meal Plan Chat-First Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor `/meal-plan` into a chat-first page with collapsible status context, secondary system-trace access, and materially shorter copy without changing core meal-chat functionality.

**Architecture:** Keep the existing Vue view as the stateful meal-chat controller, but strip out the current hero-plus-dashboard composition. Rebuild the page around a dominant chat surface, a compact context module that can collapse, and a lighter result/trace presentation model. Preserve backend behavior and only adjust frontend presentation state where needed.

**Tech Stack:** Vue 3, TypeScript, Vite, Pinia, Element Plus, vue-i18n

---

## Scope and Constraints

- This plan only covers the `/meal-plan` frontend experience and the components directly owned by it.
- The backend meal-chat flow remains the source of truth and should not be redesigned.
- The current repository does not include a dedicated frontend unit-test harness for this view. Verification should use `npm run build` plus a manual acceptance checklist. Adding automated frontend tests is out of scope for this plan.
- The redesign must preserve existing session restore, message send, generation, result overlay, and shopping-list behaviors.

## File Map

**Create**

- `docs/superpowers/specs/2026-04-05-meal-plan-chat-first-redesign-design.md`
- `docs/superpowers/plans/2026-04-05-meal-plan-chat-first-redesign.md`

**Modify**

- `frontend/src/views/MealPlanView.vue`
- `frontend/src/components/meal-chat/MealChatStatusPanel.vue`
- `frontend/src/components/meal-chat/MealChatResultOverlay.vue`
- `frontend/src/locales/zh.json`
- `frontend/src/locales/en.json`

**Optional Create**

- `frontend/src/components/meal-chat/MealChatProcessDrawer.vue`

If the process detail can be handled cleanly inside `MealPlanView.vue`, avoid creating the optional component.

## Target Outcomes

- Chat is the dominant visual surface on desktop and mobile.
- The current hero block is removed.
- Status becomes a compact, user-collapsible module instead of a large permanent card.
- "系统过程" is demoted from a main-page content block to a small entry point or folded secondary surface.
- Result overlay remains the final plan surface, but with shorter copy and clearer hierarchy.

---

### Task 1: Simplify the `/meal-plan` page structure

**Files:**
- Modify: `frontend/src/views/MealPlanView.vue`

- [ ] Remove the current hero section from the `MealPlanView.vue` template.
- [ ] Replace the hero with a compact top bar that contains:
  - a short page title
  - one concise progress summary line
  - the existing "new session" action in lighter form
- [ ] Rebuild the page body so the chat area becomes the primary column and the support context becomes secondary.
- [ ] Keep the current session bootstrap, restore, send, generate, restart, and overlay handlers unchanged unless a small presentation-state adjustment is required.
- [ ] Replace the persistent trace card with a lightweight trace entry action.

**Acceptance criteria**

- The first screenful clearly reads as a conversation page instead of a feature intro page.
- No functional handler is removed from the meal-chat flow.

---

### Task 2: Make status user-collapsible and lighter

**Files:**
- Modify: `frontend/src/views/MealPlanView.vue`
- Modify: `frontend/src/components/meal-chat/MealChatStatusPanel.vue`

- [ ] Add frontend presentation state for status visibility:
  - expanded by default on desktop
  - easy to toggle by the user
  - still accessible on mobile without side-by-side layout dependence
- [ ] Refactor `MealChatStatusPanel.vue` into a compact context module with two states:
  - collapsed summary
  - expanded detail
- [ ] Ensure the collapsed summary still exposes:
  - current phase
  - missing count or generation-ready state
  - the primary next action
- [ ] Keep detailed known-items and missing-items content available in expanded mode, but shorten labels and reduce visual noise.
- [ ] Keep generate/result/shopping-list actions near the status module so the next step remains obvious.

**Acceptance criteria**

- Users can collapse status when they want a cleaner chat view.
- Users do not lose the main CTA when status is collapsed.

---

### Task 3: Demote "系统过程" to secondary detail

**Files:**
- Modify: `frontend/src/views/MealPlanView.vue`
- Modify: `frontend/src/components/meal-chat/MealChatResultOverlay.vue`
- Optional Create: `frontend/src/components/meal-chat/MealChatProcessDrawer.vue`

- [ ] Remove the dedicated trace card from the main page layout.
- [ ] Add a small, clearly secondary trigger such as "查看过程" near the context actions or result entry area.
- [ ] Present trace details in one of these two ways:
  - preferred: compact drawer or inline expandable panel that overlays or stacks without affecting the main page grid
  - acceptable: trace only inside the result overlay as a folded section, with no large main-page trace surface
- [ ] Preserve current locale behavior for trace messaging, including the English warning when raw trace content is Chinese-only.
- [ ] Ensure opening process details does not create a large empty area in the surrounding layout.

**Acceptance criteria**

- "系统过程" is accessible but visually de-emphasized.
- Opening it no longer breaks the surrounding page rhythm.

---

### Task 4: Shorten copy and tighten hierarchy

**Files:**
- Modify: `frontend/src/views/MealPlanView.vue`
- Modify: `frontend/src/components/meal-chat/MealChatStatusPanel.vue`
- Modify: `frontend/src/components/meal-chat/MealChatResultOverlay.vue`
- Modify: `frontend/src/locales/zh.json`
- Modify: `frontend/src/locales/en.json`

- [ ] Audit all `meal_plan` strings used by the page and classify them as:
  - required for action clarity
  - redundant
  - decorative
- [ ] Remove or rewrite redundant and decorative strings:
  - long subtitles
  - repeated explanatory copy
  - duplicate section intros
- [ ] Keep only the shortest copy needed to explain:
  - current phase
  - what is missing
  - whether the user can generate
  - what action comes next
- [ ] Keep tone plainspoken and calm in both Chinese and English locales.

**Acceptance criteria**

- The page has visibly fewer words than the current version.
- No removed sentence creates ambiguity about the next user action.

---

### Task 5: Simplify the result overlay without changing result behavior

**Files:**
- Modify: `frontend/src/components/meal-chat/MealChatResultOverlay.vue`

- [ ] Keep the existing modal behavior, focus management, and result actions.
- [ ] Tighten the overlay header so it emphasizes:
  - result title
  - total price
  - return to chat
- [ ] Reduce top-of-overlay explanatory copy and avoid repeating information already visible in meal groups or summary metrics.
- [ ] Keep alternatives and system trace folded behind clearly secondary sections when present.
- [ ] Maintain mobile-safe layout and full-width actions on small screens.

**Acceptance criteria**

- The result overlay feels lighter and faster to scan.
- Existing result actions still work exactly as before.

---

### Task 6: Rework responsive behavior around chat-first priorities

**Files:**
- Modify: `frontend/src/views/MealPlanView.vue`
- Modify: `frontend/src/components/meal-chat/MealChatStatusPanel.vue`
- Modify: `frontend/src/components/meal-chat/MealChatResultOverlay.vue`

- [ ] Make desktop use a dominant primary chat column with a narrow secondary rail only when width allows.
- [ ] Make mobile collapse into a single-column flow.
- [ ] Remove any layout rule that depends on persistent secondary cards to establish page balance.
- [ ] Preserve comfortable message width, composer reachability, and CTA visibility across breakpoints.

**Acceptance criteria**

- Desktop feels chat-led rather than split evenly between chat and support content.
- Mobile keeps all critical actions without horizontal crowding.

---

### Task 7: Verify no core workflow regression

**Files:**
- Modify: `frontend/src/views/MealPlanView.vue`
- Modify: `frontend/src/components/meal-chat/MealChatStatusPanel.vue`
- Modify: `frontend/src/components/meal-chat/MealChatResultOverlay.vue`
- Modify: `frontend/src/locales/zh.json`
- Modify: `frontend/src/locales/en.json`

- [ ] Run `cd frontend && npm run build`.
- [ ] Manually verify the following flows:
  - fresh page load creates a session successfully
  - saved session restores correctly
  - sending a message still appends optimistic UI then resolves to server state
  - generation still opens the loading overlay and then the result overlay
  - returning from result overlay restores chat view
  - restarting session clears prior local presentation state
  - adding meals to shopping list still succeeds
  - collapsing and expanding status does not affect session data
  - opening process details does not distort the layout

**Acceptance criteria**

- Build passes.
- Manual acceptance checklist passes without a meal-chat functional regression.

## Self-Review

### Spec Coverage

- Chat-first structure: covered by Tasks 1 and 6.
- Collapsible status: covered by Task 2.
- System trace demotion: covered by Task 3.
- Reduced copy: covered by Task 4.
- Result preservation with simplification: covered by Task 5.
- No core workflow regression: covered by Task 7.

### Placeholder Scan

- No `TODO`, `TBD`, or deferred placeholders remain.
- Optional process drawer is explicitly bounded as optional, with an in-place fallback.

### Type and Naming Consistency

- Status presentation state is consistently described as collapse/expand behavior.
- Process detail is consistently described as trace/system-process secondary UI.
