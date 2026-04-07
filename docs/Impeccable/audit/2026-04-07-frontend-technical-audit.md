# Frontend Technical Audit

Audit date: 2026-04-07

Scope:

- Frontend application under `frontend/src`
- Current design context from `.impeccable.md` and `.github/copilot-instructions.md`
- Technical audit dimensions required by the `audit` skill:
  - Accessibility
  - Performance
  - Responsive Design
  - Theming
  - Anti-patterns

Verification performed:

- `cd frontend && npm run build`
- `cd frontend && npm run test`
- Static code scan for ARIA, keyboard support, theme hooks, hard-coded colors, breakpoints, and interactive semantics
- Manual code review of key surfaces:
  - `src/App.vue`
  - `src/views/HomeView.vue`
  - `src/views/MealPlanView.vue`
  - `src/views/RecipesView.vue`
  - `src/views/ShoppingListView.vue`
  - `src/views/ProfileView.vue`
  - `src/components/meal-chat/MealChatStatusPanel.vue`
  - `src/components/meal-chat/MealChatGenerationOverlay.vue`
  - `src/components/meal-chat/MealChatResultOverlay.vue`

Verification results:

- `npm run build` passed.
- `npm run test` passed.
- Build output emitted a chunk-size warning.
- The shared production bundle is still large:
  - `dist/assets/index-BbB_a_It.js`: `1,272.86 kB`
  - gzip: `412.77 kB`

## Audit Health Score

| # | Dimension | Score | Key Finding |
|---|-----------|-------|-------------|
| 1 | Accessibility | 1/4 | Unlabeled icon controls, mouse-only recipe cards, and broken modal semantics |
| 2 | Performance | 2/4 | Production build ships an oversized shared JS chunk |
| 3 | Responsive Design | 3/4 | Page-level breakpoints exist, but some control ergonomics still miss mobile targets |
| 4 | Theming | 1/4 | No dark mode implementation and extensive hard-coded color usage |
| 5 | Anti-Patterns | 2/4 | Generic green wellness dashboard styling still dominates |
| **Total** |  | **9/20** | **Poor** |

Rating band:

- `9/20`: Poor

## Anti-Patterns Verdict

Fail.

This does not look like an overt AI demo, but it still reads as a generic wellness-dashboard UI rather than a deliberate consumer product. The strongest tells are:

- repeated rounded white cards with soft shadows across most pages
- green-heavy accenting and wellness-style gradients on major surfaces
- default system typography rather than a more intentional branded type direction
- visual decisions implemented through one-off hard-coded colors instead of a coherent theme system

## Executive Summary

- Audit Health Score: `9/20` (`Poor`)
- Issues found:
  - `P0`: 0
  - `P1`: 5
  - `P2`: 3
  - `P3`: 0
- Highest-priority problems:
  - shopping list icon controls are missing accessible names
  - recipe cards are clickable but not keyboard accessible
  - generation overlay uses invalid modal semantics and does not manage focus
  - dark mode is not implemented despite current project direction
  - the shared frontend bundle is too large for a mobile-first product

## Detailed Findings By Severity

### P1 Major

#### [P1] Icon-only shopping list controls have no accessible name

- Location: `frontend/src/views/ShoppingListView.vue:79`, `frontend/src/views/ShoppingListView.vue:104`
- Category: Accessibility
- Impact: Screen-reader users will encounter unnamed controls for item completion and deletion, making the list difficult to operate reliably.
- WCAG/Standard: WCAG 2.1 AA, `4.1.2 Name, Role, Value`; `2.5.3 Label in Name`
- Recommendation: Add explicit accessible names such as `aria-label` that include both the action and the item name.
- Suggested command: `/harden`

#### [P1] Recipe cards are clickable but not keyboard accessible

- Location: `frontend/src/views/RecipesView.vue:87-93`
- Category: Accessibility
- Impact: Opening recipe details depends on clicking `el-card`, but the card does not expose button/link semantics or keyboard activation, so keyboard users cannot reliably trigger it.
- WCAG/Standard: WCAG 2.1 AA, `2.1.1 Keyboard`; `4.1.2 Name, Role, Value`
- Recommendation: Convert the card trigger into a real button or link, or add `role="button"`, `tabindex="0"`, keyboard handlers, and visible focus treatment.
- Suggested command: `/harden`

#### [P1] Generation overlay has broken modal semantics and no focus management

- Location: `frontend/src/components/meal-chat/MealChatGenerationOverlay.vue:3-12`
- Category: Accessibility
- Impact: The overlay visually blocks the page, but it is exposed as `role="status"` with `aria-modal="true"`. That does not match ARIA modal dialog behavior, and keyboard users can still navigate underlying content.
- WCAG/Standard: WCAG 2.1 AA, `2.4.3 Focus Order`; ARIA modal dialog pattern
- Recommendation: Treat this surface consistently as either a real modal dialog with managed focus, or a non-modal live region. Do not mix the two models.
- Suggested command: `/harden`

#### [P1] Dark mode is not implemented, and the current theme system cannot support it cleanly

- Location:
  - `frontend/src/assets/main.css:1-35`
  - `frontend/src/components/meal-chat/MealChatStatusPanel.vue:90-212`
  - `frontend/src/views/ProfileView.vue:99-106`
- Category: Theming
- Impact: The project direction now requires both light mode and dark mode, but the codebase defines only one light palette and then bypasses it with many one-off colors. A static scan found `165` hard-coded color and gradient usages across `14` source files, with no dark-mode selectors or alternate theme tokens.
- WCAG/Standard: Design-system/theming requirement; maintainability risk
- Recommendation: Introduce semantic theme tokens, add a dark theme source of truth, and remove direct hex/rgba/gradient styling from feature components.
- Suggested command: `/normalize`

#### [P1] Shared frontend bundle is too large

- Location:
  - `frontend/src/main.ts:3-7`
  - `frontend/src/main.ts:15-16`
- Category: Performance
- Impact: Production build emits a `1,272.86 kB` shared JS bundle and Vite warns about chunk size. Full `ElementPlus` registration and global registration of all Element Plus icons are visible contributors, increasing parse and execute cost on first load.
- WCAG/Standard: Performance best practice
- Recommendation: Stop globally registering all icons, audit actual icon usage, and split vendor code more intentionally.
- Suggested command: `/optimize`

### P2 Minor

#### [P2] Interactive elements are nested inside links in multiple pages

- Location:
  - `frontend/src/views/HomeView.vue:11-16`
  - `frontend/src/views/ShoppingListView.vue:8-10`
  - `frontend/src/views/ProfileView.vue:84-85`
- Category: Accessibility
- Impact: `router-link` typically renders links, and several of these wrap `el-button`. Nested interactive elements create inconsistent focus and announcement behavior across browsers and assistive technology.
- WCAG/Standard: HTML interactive-content rules; WCAG `4.1.2` risk
- Recommendation: Use link-styled buttons or programmatic navigation from buttons, but avoid link-wrapped buttons.
- Suggested command: `/harden`

#### [P2] Focus-visible styling is not defined, and one custom toggle is undersized for touch

- Location:
  - `frontend/src/assets/main.css:59-75`
  - `frontend/src/components/meal-chat/MealChatStatusPanel.vue:163-177`
- Category: Accessibility / Responsive Design
- Impact: A scan found no explicit `:focus` or `:focus-visible` rules in `frontend/src`, so custom controls rely on browser defaults. The meal-chat status toggle is also only `36px` tall, below common `44x44px` touch-target guidance.
- WCAG/Standard: WCAG 2.1 AA, `2.4.7 Focus Visible`; mobile target-size guidance
- Recommendation: Add a consistent focus-visible system and raise custom control hit areas to at least `44px`.
- Suggested command: `/harden`

#### [P2] Current visual language still reads as generic green wellness UI

- Location:
  - `frontend/src/assets/main.css:1-17`
  - `frontend/src/views/HomeView.vue:108-117`
  - `frontend/src/components/meal-chat/MealChatStatusPanel.vue:96-105`
- Category: Anti-Pattern
- Impact: The current implementation still signals template health-app styling through green gradients, white cards, generic shadows, and default typography. That conflicts with the documented goal of a refined, elegant, real consumer product.
- WCAG/Standard: Product-quality anti-pattern
- Recommendation: Replace the current green-heavy system with a calmer, more premium neutral-first theme and tighter visual hierarchy.
- Suggested command: `/quieter`

## Patterns And Systemic Issues

- Hard-coded visual values are systemic:
  - `165` color/gradient matches found in `frontend/src`
  - spread across `14` source files
- Responsive coverage is present but uneven:
  - `17` `@media (max-width: ...)` blocks were found
  - page shells adapt, but control-level ergonomics still need work
- Frontend verification depth is still limited:
  - only `1` frontend test ran during `vitest`
  - most UX regression protection still depends on manual review

## Positive Findings

- Route-level lazy loading is already in place in `frontend/src/router/index.ts:4-54`.
- The meal result overlay has materially better accessibility than the generation overlay:
  - dialog semantics in `frontend/src/components/meal-chat/MealChatResultOverlay.vue:3-12`
  - focus trapping and restoration in `frontend/src/components/meal-chat/MealChatResultOverlay.vue:206-257`
- Reduced-motion support exists at the token level in `frontend/src/assets/main.css:112-117`.
- Several primary controls already meet `44px` touch-target sizing, for example `frontend/src/views/ShoppingListView.vue:338-346`.

## Recommended Actions

1. **[P1] `/harden`** — Fix accessible names, keyboard activation, modal semantics, focus visibility, and nested interactive controls.
2. **[P1] `/normalize`** — Replace hard-coded colors with semantic tokens and establish a real light/dark theming system.
3. **[P1] `/optimize`** — Reduce the shared bundle by changing global Element Plus/icon registration and improving chunking.
4. **[P2] `/adapt`** — Raise undersized touch targets and review control-level mobile ergonomics.
5. **[P2] `/quieter`** — Remove the generic green wellness chrome and move toward the documented consumer-product visual direction.
6. **[P2] `/polish`** — Run a final consistency pass after the structural fixes land.

## Notes

The audit was intentionally limited to verifiable implementation issues and technical anti-patterns. It does not include feature redesign proposals or code changes.

You can run the recommended commands one at a time, all at once, or in any order.

Re-run `/audit` after fixes to measure score improvement.
