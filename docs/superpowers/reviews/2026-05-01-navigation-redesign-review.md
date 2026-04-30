# Navigation Redesign Code Review

**Branch:** `navigation-redesign` (worktree: `.claude/worktrees/navigation-redesign`)
**Commits:** 4 (`a987757..75fdd85`)
**Diff:** 5 files changed, +115 / -79

---

## Summary

The implementation correctly merges the two-row desktop navigation into a single flat top bar with 5 primary nav items, expands the mobile bottom tab bar from 3 to 5 items, and adds a shopping cart icon with badge. The core navigation refactor matches the plan and is well-executed.

**Assessment: Merge with minor fixes**

---

## Strengths

1. **Plan adherence is strong.** All 4 tasks from the plan are completed in order: i18n keys, store computed, App.vue refactor, regression test update. The 5 nav items (Planner, Weekly Plan, Recipes, History, Profile) appear in both desktop and mobile.

2. **Dead code cleanup is thorough.** `handleMoreCommand`, `useRouter` import, `.menu-link` CSS selectors, `.primary-nav-inner` styles, and the standalone `.primary-nav` bar are all removed cleanly. No stale references remain.

3. **Shopping cart badge is correctly wired.** `listCount` is a proper `computed(() => lists.value.length)`. The `<el-badge>` uses `:hidden="shoppingListCount === 0"` and `:max="9"`. Accessible `aria-label` is present on the icon-only button.

4. **Touch targets meet requirements.** Nav items have `min-height: 44px`, cart link is `44x44px`, mobile nav items are `min-height: 52px`.

5. **Regression test updated.** The audit test now asserts `class="primary-nav"`, `/weekly-plan`, and `<el-badge>` instead of the old `handleMoreCommand` assertions.

---

## Issues

### IMPORTANT: `onMounted` shopping list load has a timing bug

**File:** `App.vue:137-141`

```ts
onMounted(() => {
  if (showPrimaryNav.value) {
    shoppingStore.loadLists()
  }
})
```

**Problem:** If a user lands on `/login` (where `showPrimaryNav` is `false`), `onMounted` fires but skips the load. After login, the SPA redirects to `/meal-plan` — but `onMounted` does NOT re-fire because `App.vue` is already mounted. The badge stays at 0 until the user navigates to the shopping list page.

**Fix:** Use a `watch` on `showPrimaryNav` instead:

```ts
watch(showPrimaryNav, (visible) => {
  if (visible) shoppingStore.loadLists().catch(() => {})
}, { immediate: true })
```

This also handles the silent failure case (`.catch(() => {})` prevents unhandled rejection).

### MINOR: `nav.home` key defined but unused

Both `en.json` and `zh.json` define `"home": "Home"` / `"首页"` in the `nav` section, but no template references `$t('nav.home')`. Either remove it or use it (e.g., as an `aria-label` on the brand link).

### MINOR: Unnecessary `<template v-if>` wrapper

```html
<template v-if="showPrimaryNav">
  <router-link to="/shopping-list" class="utility-link cart-link" ...>
```

Since there's only one child, the `v-if` can go directly on the `<router-link>`.

---

## Reviewer Error Note

The initial automated review incorrectly claimed "13 files changed, 1814 lines removed" including removal of the weekly plan edit/delete feature, `main.css` overlay styles, and `api/index.ts` reformatting. **This is false.** The actual diff is exactly 5 files with +115/-79 lines. The weekly plan edit/delete feature, overlay CSS, and API client are untouched on this branch. This was verified via `git diff main...HEAD --stat`.

---

## Verdict

| Category | Count |
|----------|-------|
| Critical | 0 |
| Important | 1 (onMounted timing) |
| Minor | 2 (unused i18n key, template wrapper) |

**Merge after fixing the Important issue.** The `onMounted` → `watch` change is a one-line fix. The two Minor issues can be addressed in a follow-up.
