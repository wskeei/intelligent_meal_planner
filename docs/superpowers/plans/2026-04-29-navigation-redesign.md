# Navigation Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Merge the two-row desktop navigation into a single flat nav bar with all 6 feature pages as primary items, and expand the mobile bottom tab bar from 3 to 5 items.

**Architecture:** All navigation lives in `App.vue` (no separate NavBar component). The refactor modifies the template structure (merge `.topbar` + `.primary-nav` into one `.topbar`), updates the mobile bottom nav (`.mobile-nav`) to 5 items, adds a shopping cart icon button with badge in the utility area, and removes the "More" dropdown entirely.

**Tech Stack:** Vue 3 + Composition API, Element Plus (icons, dropdown, badge), vue-i18n, vue-router, Pinia store

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `frontend/src/App.vue` | Modify | Merge nav rows, restructure template + CSS |
| `frontend/src/locales/zh.json` | Modify | Add/adjust `nav.*` i18n keys |
| `frontend/src/locales/en.json` | Modify | Add/adjust `nav.*` i18n keys |
| `frontend/src/stores/shopping.ts` | Modify | Add `listCount` computed for badge |
| `frontend/src/api/index.ts` | Modify | Add `shoppingListApi.count()` or reuse `list()` |

No new files created. No backend changes.

---

### Task 1: Update i18n Navigation Keys

**Files:**
- Modify: `frontend/src/locales/en.json`
- Modify: `frontend/src/locales/zh.json`

The current nav section has these keys: `planner`, `shopping`, `recipes`, `profile`, `history`, `more`, `exit`. We need to add `home`, `weekly_plan` (currently uses `weekly_plan.title`), and `shopping_cart` for the icon button tooltip. We can remove `more` since the dropdown is being eliminated.

- [ ] **Step 1: Update `en.json` nav section**

In `frontend/src/locales/en.json`, find the `"nav"` object (currently lines 7-15) and replace it with:

```json
"nav": {
  "home": "Home",
  "planner": "Planner",
  "weekly_plan": "Weekly Plan",
  "recipes": "Recipes",
  "history": "History",
  "profile": "Profile",
  "shopping_cart": "Shopping List",
  "exit": "Log out"
}
```

Changes: added `home`, `weekly_plan`, `shopping_cart`; removed `more`, `shopping` (replaced by `shopping_cart`).

- [ ] **Step 2: Update `zh.json` nav section**

In `frontend/src/locales/zh.json`, find the `"nav"` object and replace it with:

```json
"nav": {
  "home": "首页",
  "planner": "配餐",
  "weekly_plan": "周计划",
  "recipes": "菜谱",
  "history": "历史",
  "profile": "档案",
  "shopping_cart": "购物清单",
  "exit": "退出登录"
}
```

- [ ] **Step 3: Verify JSON is valid**

Run: `python3 -c "import json; json.load(open('frontend/src/locales/en.json')); json.load(open('frontend/src/locales/zh.json')); print('OK')"`

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add frontend/src/locales/en.json frontend/src/locales/zh.json
git commit -m "i18n: update nav keys for flat navigation redesign"
```

---

### Task 2: Add Shopping List Count to Store

**Files:**
- Modify: `frontend/src/stores/shopping.ts`

The shopping cart badge needs to display the number of shopping lists. We add a `listCount` computed value to the existing shopping store.

- [ ] **Step 1: Read current store**

Read `frontend/src/stores/shopping.ts` to understand existing structure. The store already has a `lists` ref (array of `ShoppingListSummary`) and a `loadLists()` action.

- [ ] **Step 2: Add `listCount` computed**

In `frontend/src/stores/shopping.ts`, add a computed property that returns the length of the `lists` array. The store already loads lists — we just need a derived count.

Add after the existing refs:

```ts
const listCount = computed(() => lists.value.length)
```

Make sure `computed` is imported from `vue`. Add `listCount` to the return object.

- [ ] **Step 3: Verify TypeScript compiles**

Run: `cd frontend && npx vue-tsc --noEmit`

Expected: no errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/stores/shopping.ts
git commit -m "feat(store): add listCount computed to shopping store"
```

---

### Task 3: Refactor Desktop Navigation in App.vue

**Files:**
- Modify: `frontend/src/App.vue` (template + script + CSS)

This is the main task. We merge the two-row navigation into a single row.

#### 3a: Restructure the Template

- [ ] **Step 1: Read the full App.vue**

Read `frontend/src/App.vue` completely to understand all template, script, and style sections.

- [ ] **Step 2: Replace the `.topbar` template**

Replace the existing `<header class="topbar">` block (lines 4-51) with a new structure that includes the primary nav items inline:

```html
<header class="topbar">
  <div class="container topbar-inner">
    <!-- Brand -->
    <router-link to="/" class="brand">
      <div class="logo-icon">
        <el-icon :size="22" class="brand-icon"><Food /></el-icon>
      </div>
      <div>
        <span class="brand-text">{{ $t('app.brand') }}</span>
        <p class="brand-subtitle">{{ $t('app.tagline') }}</p>
      </div>
    </router-link>

    <!-- Primary nav (inline, visible on auth pages only) -->
    <nav v-if="showPrimaryNav" class="primary-nav">
      <router-link to="/meal-plan" class="nav-item" active-class="active">
        <el-icon><MagicStick /></el-icon>
        <span>{{ $t('nav.planner') }}</span>
      </router-link>
      <router-link to="/weekly-plan" class="nav-item" active-class="active">
        <el-icon><Calendar /></el-icon>
        <span>{{ $t('nav.weekly_plan') }}</span>
      </router-link>
      <router-link to="/recipes" class="nav-item" active-class="active">
        <el-icon><Food /></el-icon>
        <span>{{ $t('nav.recipes') }}</span>
      </router-link>
      <router-link to="/history" class="nav-item" active-class="active">
        <el-icon><Clock /></el-icon>
        <span>{{ $t('nav.history') }}</span>
      </router-link>
      <router-link to="/profile" class="nav-item" active-class="active">
        <el-icon><User /></el-icon>
        <span>{{ $t('nav.profile') }}</span>
      </router-link>
    </nav>

    <!-- Utility nav -->
    <div class="utility-nav">
      <!-- Shopping cart with badge -->
      <template v-if="showPrimaryNav">
        <router-link to="/shopping-list" class="utility-link cart-link" :aria-label="$t('nav.shopping_cart')">
          <el-badge :value="shoppingListCount" :hidden="shoppingListCount === 0" :max="9">
            <el-icon :size="20"><ShoppingCart /></el-icon>
          </el-badge>
        </router-link>
      </template>

      <!-- Language switcher -->
      <el-dropdown @command="handleCommand">
        <span class="utility-link">
          {{ locale === 'zh' ? '中文' : 'English' }}
          <el-icon class="el-icon--right"><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="zh">中文</el-dropdown-item>
            <el-dropdown-item command="en">English</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <!-- Logout -->
      <button v-if="showPrimaryNav" class="utility-link" type="button" @click="handleLogout">
        {{ $t('nav.exit') }}
      </button>
    </div>
  </div>
</header>
```

**Key changes:**
- Removed the "More" dropdown entirely
- Added 5 nav items directly in the top bar (Planner, Weekly Plan, Recipes, History, Profile)
- Added shopping cart icon button with `<el-badge>` before the language switcher
- `Calendar` icon used for Weekly Plan (import from `@element-plus/icons-vue`)

- [ ] **Step 3: Remove the old `.primary-nav` section**

Delete the standalone `<nav v-if="showPrimaryNav" class="primary-nav">` block (currently lines 53-68) since those items are now inline in the topbar.

- [ ] **Step 4: Update the mobile bottom nav**

Replace the existing `.mobile-nav` (currently lines 86-99) with 5 items:

```html
<nav v-if="showPrimaryNav" class="mobile-nav">
  <router-link to="/meal-plan" class="mobile-nav-item" active-class="active">
    <el-icon><MagicStick /></el-icon>
    <span>{{ $t('nav.planner') }}</span>
  </router-link>
  <router-link to="/weekly-plan" class="mobile-nav-item" active-class="active">
    <el-icon><Calendar /></el-icon>
    <span>{{ $t('nav.weekly_plan') }}</span>
  </router-link>
  <router-link to="/recipes" class="mobile-nav-item" active-class="active">
    <el-icon><Food /></el-icon>
    <span>{{ $t('nav.recipes') }}</span>
  </router-link>
  <router-link to="/history" class="mobile-nav-item" active-class="active">
    <el-icon><Clock /></el-icon>
    <span>{{ $t('nav.history') }}</span>
  </router-link>
  <router-link to="/profile" class="mobile-nav-item" active-class="active">
    <el-icon><User /></el-icon>
    <span>{{ $t('nav.profile') }}</span>
  </router-link>
</nav>
```

#### 3b: Update Script Section

- [ ] **Step 5: Add new icon imports**

In the `<script setup>` section, add `Calendar` and `ShoppingCart` to the existing icon import:

```ts
import { ArrowDown, Calendar, Clock, Food, MagicStick, ShoppingCart, User } from '@element-plus/icons-vue'
```

- [ ] **Step 6: Add shopping store and listCount**

Import the shopping store and expose the count:

```ts
import { useShoppingStore } from '@/stores/shopping'

const shoppingStore = useShoppingStore()
const shoppingListCount = computed(() => shoppingStore.listCount)
```

Add an `onMounted` call to load the shopping lists on app init so the badge count is available:

```ts
onMounted(() => {
  if (showPrimaryNav.value) {
    shoppingStore.loadLists()
  }
})
```

- [ ] **Step 7: Remove unused `handleMoreCommand` function**

Delete the `handleMoreCommand` function since the "More" dropdown is removed.

#### 3c: Update CSS

- [ ] **Step 8: Update `.topbar` CSS**

The `.topbar` now contains the nav items inline, so it needs more horizontal space. Adjust:

```css
.topbar-inner {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  min-height: 72px;
}
```

- [ ] **Step 9: Style the inline `.primary-nav`**

The `.primary-nav` is now inside the topbar, not a separate bar. Update its CSS:

```css
.primary-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
  flex: 1;
  justify-content: center;
}
```

Remove the old `.primary-nav { border-bottom: 1px solid ... }` and `.primary-nav-inner` styles.

- [ ] **Step 10: Update mobile nav grid**

Change the mobile grid from 3 columns to 5:

```css
.mobile-nav {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}
```

- [ ] **Step 11: Style the cart link**

Add CSS for the cart icon button:

```css
.cart-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  padding: 0;
  border-radius: 12px;
  color: var(--color-text-secondary);
  transition: background-color 180ms ease, color 180ms ease;
}

.cart-link:hover {
  background: color-mix(in srgb, var(--color-accent-soft) 70%, transparent);
  color: var(--color-secondary);
}
```

- [ ] **Step 12: Remove dead CSS**

Remove `.primary-nav-inner` styles and any references to `.menu-link` if unused.

#### 3d: Verify

- [ ] **Step 13: TypeScript check**

Run: `cd frontend && npx vue-tsc --noEmit`

Expected: no errors

- [ ] **Step 14: Visual verification checklist**

Start the dev server (`cd frontend && npm run dev`) and verify:
- [ ] Desktop (>720px): single top bar with brand, 5 nav items, cart icon, language, logout
- [ ] Active nav item has accent highlight
- [ ] Cart icon shows badge when shopping lists exist
- [ ] Mobile (<720px): top bar simplified, bottom tab bar has 5 items
- [ ] All nav links navigate to correct pages
- [ ] Language switcher still works
- [ ] Logout still works
- [ ] No "More" dropdown visible anywhere
- [ ] Login/register pages hide all nav elements

- [ ] **Step 15: Commit**

```bash
git add frontend/src/App.vue
git commit -m "feat(nav): merge two-row nav into single flat bar with all features visible"
```

---

### Task 4: Final Verification

- [ ] **Step 1: Full TypeScript check**

Run: `cd frontend && npx vue-tsc --noEmit`

Expected: no errors

- [ ] **Step 2: Verify no dead references**

Search for any remaining references to `nav.more`, `nav.shopping`, `handleMoreCommand` in the codebase:

Run: `grep -r "nav.more\|nav.shopping\|handleMoreCommand" frontend/src/`

Expected: no results (all removed)

- [ ] **Step 3: Test responsive breakpoints**

Manually verify at these widths:
- 1200px+ (desktop): single top bar, no bottom nav
- 720-1200px (tablet): single top bar, no bottom nav
- <720px (mobile): simplified top bar + 5-item bottom tab bar
- <560px (small phone): stacked top bar + 5-item bottom tab bar

- [ ] **Step 4: Commit any final fixes**

If any issues found during testing, fix and commit separately.
