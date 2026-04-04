# Meal Planner UX Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair the product's trust gaps, first-run experience, information architecture, responsive behavior, and visual consistency so the app behaves like a coherent product instead of a partially connected demo.

**Architecture:** Start by locking design context, then fix the highest-risk promise gaps in core flows, then simplify onboarding and clarify the chat workflow, then normalize the shell and supporting pages into one product language. Keep the first pass focused on the existing Vue 3 + Element Plus app rather than introducing a new design system or major frontend rewrite.

**Tech Stack:** Vue 3, TypeScript, Vite, Pinia, Element Plus, Vue Router, vue-i18n, Axios

---

## Scope and Constraints

- This plan assumes the current backend APIs remain the source of truth where endpoints already exist.
- The repository does not currently include a frontend test harness. Verification for this remediation should use `npm run build` plus a structured manual acceptance checklist. If automated frontend tests are desired, create a separate plan.
- Because several design skills require established design context, execution must begin with `/teach-impeccable` before any major UI restyling.

## Skill Sequence

1. `/teach-impeccable` - establish audience, tone, and anti-references
2. `/harden` - remove fake affordances and broken promise paths
3. `/onboard` - redesign first-run and activation flow
4. `/distill` - cut redundant actions and reduce cognitive load
5. `/arrange` - restructure shell, home, and chat hierarchy
6. `/normalize` - unify tokens, brand, and component patterns
7. `/clarify` - rewrite UX copy, labels, errors, and empty states
8. `/adapt` - make mobile and touch behavior intentional
9. `/polish` - final alignment, spacing, state, and QA pass

## File Map

**Create**

- `.impeccable.md`
- `docs/superpowers/plans/2026-04-04-ux-remediation-plan.md`
- `frontend/src/components/meal-chat/MealChatStatusPanel.vue`
- `frontend/src/components/common/AppEmptyState.vue`

**Modify**

- `frontend/src/App.vue`
- `frontend/src/assets/main.css`
- `frontend/src/router/index.ts`
- `frontend/src/api/index.ts`
- `frontend/src/stores/user.ts`
- `frontend/src/stores/shopping.ts`
- `frontend/src/views/HomeView.vue`
- `frontend/src/views/MealPlanView.vue`
- `frontend/src/views/ProfileView.vue`
- `frontend/src/views/LoginView.vue`
- `frontend/src/views/RegisterView.vue`
- `frontend/src/views/HistoryView.vue`
- `frontend/src/views/RecipesView.vue`
- `frontend/src/views/ShoppingListView.vue`
- `frontend/src/locales/zh.json`
- `frontend/src/locales/en.json`

## Target Outcomes

- “再次使用此配置”, 菜谱筛选, 购物清单, 历史记录等入口都必须真实可用，或被降级为不误导用户的表达。
- 用户可以在最短路径内完成 `登录/注册 -> 资料补全 -> 对话 intake -> 查看结果 -> 继续/复用`。
- 对话页必须明确显示当前阶段、缺失信息、下一步动作和完成后的后续路径。
- 移动端不能依赖 hover，顶层导航不能在小屏上横向挤爆。
- 视觉、品牌名、语言和状态表达必须统一。

---

### Task 1: Establish Design Context and Success Criteria

**Skills:** `/teach-impeccable`

**Files:**
- Create: `.impeccable.md`
- Reference: `README.md`
- Reference: `frontend/README.md`

- [ ] Capture design context for this product before changing visuals.
- [ ] Record the target audience, usage context, product tone, aha moment, and anti-references in `.impeccable.md`.
- [ ] Define the primary job-to-be-done as one sentence:
  `Users should be able to tell the system their constraints and get a trustworthy daily meal plan without guessing what the system needs next.`
- [ ] Freeze the top-level product priorities for the remediation:
  1. Trustworthy behavior
  2. Clear first-run path
  3. Lower cognitive load
  4. Consistent, mobile-safe presentation

**Acceptance criteria**

- All downstream design changes can reference a concrete tone and audience.
- No later task depends on guessed brand direction.

---

### Task 2: Remove Broken Promise Paths and Trust Leaks

**Skills:** `/harden`, `/clarify`

**Files:**
- Modify: `frontend/src/views/HistoryView.vue`
- Modify: `frontend/src/views/MealPlanView.vue`
- Modify: `frontend/src/views/RecipesView.vue`
- Modify: `frontend/src/views/ShoppingListView.vue`
- Modify: `frontend/src/stores/shopping.ts`
- Modify: `frontend/src/api/index.ts`
- Modify: `frontend/src/locales/zh.json`
- Modify: `frontend/src/locales/en.json`

- [ ] Make history behavior match product reality.
  Decide one implementation path and keep it consistent:
  - Preferred: switch `HistoryView` to backend-backed history using `mealPlanApi.getHistory()`
  - Fallback: keep local history, but remove product language that implies durable account history
- [ ] Make “再次使用此配置” actually work.
  Required behavior:
  - Push reusable state through route query or store
  - Read it in `MealPlanView`
  - Prefill the first prompt or restore a resumable summary before bootstrapping the next turn
- [ ] Fix the recipe filter affordance mismatch.
  Required behavior:
  - Either support true multi-select in request building
  - Or convert UI to a single-select control so the interface stops lying
- [ ] Fix the shopping list promise mismatch.
  Required behavior:
  - Either add “from meal plan” actions in the final result panel
  - Or rewrite empty-state and feature copy so it no longer claims automatic generation
- [ ] Replace generic or misleading empty-state copy with state-specific guidance.

**Acceptance criteria**

- Every visible CTA on `History`, `Recipes`, and `Shopping List` does what the label implies.
- No page claims a capability that does not exist.

**Verification**

- `cd frontend && npm run build`
- Manual:
  - Generate or open history, click `再次使用此配置`, confirm `MealPlanView` changes behavior
  - Select multiple meal types on `Recipes`; confirm results match UI expectation
  - From a final meal plan, verify the shopping list path exists or the copy no longer promises it

---

### Task 3: Redesign First-Run and Registration Flow

**Skills:** `/onboard`, `/distill`, `/clarify`

**Files:**
- Modify: `frontend/src/views/LoginView.vue`
- Modify: `frontend/src/views/RegisterView.vue`
- Modify: `frontend/src/views/ProfileView.vue`
- Modify: `frontend/src/stores/user.ts`
- Modify: `frontend/src/locales/zh.json`
- Modify: `frontend/src/locales/en.json`

- [ ] Reduce registration to minimum viable identity fields.
  Preferred first pass:
  - Keep username, email, password
  - Move body metrics and activity level out of signup
- [ ] Remove misleading defaults from registration.
  No prefilled sex, age, weight, height, activity level, or goal unless the user explicitly chooses them.
- [ ] Turn profile completion into a real progress model instead of binary `100% / 待补全`.
  Required behavior:
  - Show percent or step count based on missing fields
  - Show exactly which fields remain missing
- [ ] Make profile editing support the meal-planning task instead of feeling administrative.
  Required behavior:
  - Explain why each field matters when needed
  - Keep the CTA back to meal planning visible and context-specific
- [ ] Update login and register success/error copy to match locale and product tone.

**Acceptance criteria**

- A first-time user can create an account without immediately entering sensitive health details.
- The product clearly explains what profile data is still needed and why.

**Verification**

- `cd frontend && npm run build`
- Manual:
  - Register with minimal fields only
  - Land in a usable state
  - Open profile and verify missing-field guidance is visible

---

### Task 4: Make Meal Chat Legible as a Guided Workflow

**Skills:** `/onboard`, `/clarify`, `/arrange`

**Files:**
- Create: `frontend/src/components/meal-chat/MealChatStatusPanel.vue`
- Modify: `frontend/src/views/MealPlanView.vue`
- Modify: `frontend/src/api/index.ts`
- Modify: `frontend/src/locales/zh.json`
- Modify: `frontend/src/locales/en.json`

- [ ] Add a dedicated chat status panel that explains the workflow in user language.
  Required content:
  - Current phase
  - What the system already knows
  - What is still missing
  - What the user should answer next
- [ ] Replace vague “等待更多信息” messaging with phase-specific guidance.
- [ ] Add a post-result continuation path.
  Required behavior:
  - Clear action after finalization, such as “start new request”, “adjust budget”, or “save to shopping list”
- [ ] Preserve visible context across the conversation.
  The user should not need to remember budget, goal, or missing fields from previous turns.
- [ ] Keep the crew trace secondary.
  It can remain visible, but it must not compete with the next required user action.

**Acceptance criteria**

- A first-time user can understand what the assistant needs without inferring it from chat history.
- The final state has an obvious next step.

**Verification**

- `cd frontend && npm run build`
- Manual:
  - Start a fresh session with incomplete profile
  - Confirm the page explicitly tells the user what information is missing
  - Complete a plan and confirm the page offers a meaningful next action

---

### Task 5: Simplify the App Shell and Home Information Architecture

**Skills:** `/distill`, `/arrange`, `/adapt`

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/views/HomeView.vue`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/assets/main.css`

- [ ] Reduce top-level navigation competition.
  Preferred structure:
  - Keep `配餐`, `档案`, `历史`
  - Demote `菜谱` and `购物清单` to secondary navigation or page-level links
- [ ] Add a mobile-safe navigation pattern.
  Preferred first pass:
  - collapsible menu or bottom navigation
  - no horizontal overflow on small screens
- [ ] Rework the home page around one dominant action.
  Required behavior:
  - One primary CTA: start or continue meal planning
  - Secondary actions visually demoted
- [ ] Replace decorative dashboard language with task language.
  Example shift:
  - from “仪表盘 / 今日概览”
  - to “开始今天的配餐 / 继续上次的计划”
- [ ] Make “资料完整度” actionable, not just informational.

**Acceptance criteria**

- On both desktop and mobile, the primary action is obvious within 2 seconds.
- The shell no longer feels like multiple unrelated tools competing equally.

**Verification**

- `cd frontend && npm run build`
- Manual:
  - Check `320px`, `768px`, `1280px` widths
  - Confirm no nav overflow and no ambiguous primary CTA

---

### Task 6: Normalize Visual Language, Brand, and Tokens

**Skills:** `/normalize`, `/clarify`

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/assets/main.css`
- Modify: `frontend/src/views/HomeView.vue`
- Modify: `frontend/src/views/MealPlanView.vue`
- Modify: `frontend/src/views/ProfileView.vue`
- Modify: `frontend/src/views/LoginView.vue`
- Modify: `frontend/src/views/RegisterView.vue`
- Modify: `frontend/src/views/HistoryView.vue`
- Modify: `frontend/src/views/RecipesView.vue`
- Modify: `frontend/src/views/ShoppingListView.vue`
- Modify: `frontend/src/locales/zh.json`
- Modify: `frontend/src/locales/en.json`

- [ ] Choose one product name and apply it consistently across shell, auth, footer, and metadata.
- [ ] Remove obvious AI-demo phrasing such as “Powered by Multi-Agent AI” from user-facing chrome unless explicitly part of brand voice.
- [ ] Normalize spacing, radius, shadow, and surface patterns.
  Target:
  - shared tokens in `main.css`
  - fewer one-off gradients and card treatments
- [ ] Bring old pages (`Login`, `Register`, `History`, `Recipes`, `Shopping List`) up to the same interaction and spacing standard as the newer pages.
- [ ] Remove mixed-language system messages and unify locale coverage.

**Acceptance criteria**

- The app reads as one product family, not two UI generations stitched together.
- Visual emphasis aligns with hierarchy, not with whichever page was most recently redesigned.

**Verification**

- `cd frontend && npm run build`
- Manual:
  - Compare all major routes side by side
  - Confirm consistent naming, tone, and component behavior

---

### Task 7: Make All Major Flows Mobile-Safe and Touch-Safe

**Skills:** `/adapt`, `/harden`

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/views/HomeView.vue`
- Modify: `frontend/src/views/MealPlanView.vue`
- Modify: `frontend/src/views/ProfileView.vue`
- Modify: `frontend/src/views/HistoryView.vue`
- Modify: `frontend/src/views/RecipesView.vue`
- Modify: `frontend/src/views/ShoppingListView.vue`
- Modify: `frontend/src/assets/main.css`

- [ ] Remove hover-only behaviors from touch-critical flows.
  Immediate targets:
  - shopping item delete affordance
  - any hidden action that appears only on hover
- [ ] Ensure touch targets meet at least `44x44px`.
- [ ] Reflow all two-column layouts for narrow screens with intentional order, not accidental stacking.
- [ ] Prevent overflow from long labels, timestamps, meal names, locale expansion, and dynamic values.
- [ ] Keep primary actions within comfortable mobile reach when possible.

**Acceptance criteria**

- No major flow requires hover, precision mouse input, or desktop-width assumptions.
- `320px` and `390px` widths remain usable without horizontal scrolling.

**Verification**

- `cd frontend && npm run build`
- Manual:
  - Test `320px`, `390px`, `768px`
  - Verify chat, history, and shopping flows one-handed in browser emulation

---

### Task 8: Final UX Writing, State Coverage, and Polish Pass

**Skills:** `/clarify`, `/polish`

**Files:**
- Create: `frontend/src/components/common/AppEmptyState.vue`
- Modify: all pages touched above
- Modify: `frontend/src/locales/zh.json`
- Modify: `frontend/src/locales/en.json`

- [ ] Standardize empty, loading, error, success, and confirmation states.
- [ ] Replace toast-only recovery with inline guidance where the user can act.
- [ ] Unify capitalization, button voice, and destructive-action wording.
- [ ] Remove debug/demo copy and any remaining jargon that speaks from system perspective instead of user perspective.
- [ ] Do a final consistency pass on spacing, focus states, touch targets, and route transitions.

**Acceptance criteria**

- Users can recover from common failures without guessing.
- Copy is direct, human, and consistent in both locales.

**Verification**

- `cd frontend && npm run build`
- Manual:
  - Failed login
  - failed profile save
  - failed chat send
  - empty history
  - empty shopping list
  - no recipe results

---

## Release Checklist

- [ ] `.impeccable.md` exists and reflects the chosen product tone
- [ ] Core broken-promise issues are fixed or removed from UI
- [ ] First-run path is reduced to minimum friction
- [ ] Chat flow exposes phase, missing info, and next action
- [ ] Navigation is mobile-safe
- [ ] Brand and locale are consistent
- [ ] `cd frontend && npm run build` passes
- [ ] Manual acceptance checklist completed on desktop and narrow mobile widths

## Recommended Execution Order

If this plan is executed across multiple passes, use this sequence:

1. Task 1
2. Task 2
3. Task 3
4. Task 4
5. Task 5
6. Task 6
7. Task 7
8. Task 8

## Notes

- Do not start with visual polish. The highest value work is removing false affordances and clarifying the meal-planning path.
- Prefer reducing or hiding unsupported features over designing around broken flows.
- Avoid introducing a new component library or a full design-system rewrite in this remediation.

Plan complete and saved to `docs/superpowers/plans/2026-04-04-ux-remediation-plan.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
