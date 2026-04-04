# Post-Debug Meal Chat Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the remaining non-model issues exposed during manual testing: misleading meal-chat error messaging, weak auth failure handling around expired/invalid login state, and Element Plus radio deprecation warnings.

**Architecture:** Keep the current immersive meal-chat flow intact, but tighten failure classification at the frontend boundary so message-send failures, generation failures, and auth failures no longer collapse into the same generic UI. Clean up deprecated radio API usage in the relevant Vue views to remove runtime warnings and keep the frontend aligned with Element Plus 3.x migration guidance.

**Tech Stack:** Vue 3, TypeScript, Pinia, Axios, Element Plus, vue-i18n, FastAPI, pytest, Vite

---

## File Structure

- Modify: `frontend/src/views/MealPlanView.vue`
- Modify: `frontend/src/stores/auth.ts`
- Modify: `frontend/src/api/index.ts`
- Modify: `frontend/src/locales/zh.json`
- Modify: `frontend/src/locales/en.json`
- Modify: `frontend/src/views/ProfileView.vue`
- Modify: `frontend/src/views/RecipesView.vue`
- Modify: `tests/api/test_meal_chat_router.py`
- Create: `docs/2026-04-05-post-debug-meal-chat-hardening-review.md`

## Scope Notes

- Ignore the missing DQN model artifact issue for this plan. The user has identified that as a local environment problem and will restore the model separately.
- Do not change the immersive overlay architecture in this pass.
- Treat DeepSeek upstream 401s as configuration/environment signals unless a code-level failure path needs better messaging.

## Task 1: Split Meal Chat Failure States Into Accurate User Messaging

**Files:**
- Modify: `frontend/src/views/MealPlanView.vue`
- Modify: `frontend/src/locales/zh.json`
- Modify: `frontend/src/locales/en.json`

- [ ] **Step 1: Write the failure cases to preserve**

```ts
type MealChatFailureKind =
  | 'message_send_failed'
  | 'generation_failed'
  | 'auth_required'
```

- [ ] **Step 2: Replace the current shared message error path in generation**

```ts
catch (error) {
  overlayMode.value = 'hidden'
  messageError.value = t('meal_plan.generation_inline_error')
  ElMessage.error(t('meal_plan.generation_failed'))
}
```

- [ ] **Step 3: Keep send-message errors separate from generate errors**

```ts
catch (error) {
  optimisticMessages.value = null
  draft.value = content
  messageError.value = t('meal_plan.message_inline_error')
  ElMessage.error(t('meal_plan.message_failed'))
}
```

- [ ] **Step 4: Add dedicated locale copy**

```json
{
  "meal_plan": {
    "generation_failed": "正式生成失败，请稍后重试。",
    "generation_inline_error": "正式配餐没有生成成功。你可以稍后重试，或先返回聊天调整条件。"
  }
}
```

- [ ] **Step 5: Run frontend build**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/views/MealPlanView.vue frontend/src/locales/zh.json frontend/src/locales/en.json
git commit -m "fix: separate meal chat generation errors from send failures"
```

## Task 2: Handle Auth Failures Explicitly Instead Of Letting Them Look Like Chat Errors

**Files:**
- Modify: `frontend/src/views/MealPlanView.vue`
- Modify: `frontend/src/stores/auth.ts`
- Modify: `frontend/src/api/index.ts`
- Modify: `frontend/src/locales/zh.json`
- Modify: `frontend/src/locales/en.json`

- [ ] **Step 1: Add a small Axios classifier for auth failures**

```ts
import axios from 'axios'

function isUnauthorizedError(error: unknown) {
  return axios.isAxiosError(error) && error.response?.status === 401
}
```

- [ ] **Step 2: Route meal-chat auth failures to re-login UX**

```ts
catch (error) {
  if (isUnauthorizedError(error)) {
    authStore.logout()
    ElMessage.error(t('meal_plan.auth_required'))
    return
  }
  ...
}
```

- [ ] **Step 3: Tighten login failure reporting in the auth store**

```ts
catch (error) {
  if (axios.isAxiosError(error) && error.response?.status === 401) {
    return { ok: false, reason: 'invalid_credentials' as const }
  }
  return { ok: false, reason: 'request_failed' as const }
}
```

- [ ] **Step 4: Update callers to distinguish invalid credentials from generic request errors**

```ts
const result = await authStore.login(username, password)
if (!result.ok && result.reason === 'invalid_credentials') {
  loginError.value = t('auth.invalid_credentials')
}
```

- [ ] **Step 5: Add locale copy for expired/invalid auth state**

```json
{
  "meal_plan": {
    "auth_required": "登录状态已失效，请重新登录后继续。"
  },
  "auth": {
    "invalid_credentials": "用户名或密码不正确。"
  }
}
```

- [ ] **Step 6: Run targeted frontend build**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add frontend/src/views/MealPlanView.vue frontend/src/stores/auth.ts frontend/src/api/index.ts frontend/src/locales/zh.json frontend/src/locales/en.json
git commit -m "fix: surface auth failures explicitly in meal chat and login flows"
```

## Task 3: Remove Element Plus Radio Deprecation Warnings

**Files:**
- Modify: `frontend/src/views/ProfileView.vue`
- Modify: `frontend/src/views/RecipesView.vue`

- [ ] **Step 1: Replace deprecated radio `label` usage with `value`**

```vue
<el-radio value="male">{{ $t('auth.male') }}</el-radio>
<el-radio value="female">{{ $t('auth.female') }}</el-radio>
```

```vue
<el-radio-button value="">{{ $t('recipes.all_meals') }}</el-radio-button>
<el-radio-button value="breakfast">{{ $t('recipes.breakfast') }}</el-radio-button>
<el-radio-button value="lunch">{{ $t('recipes.lunch') }}</el-radio-button>
<el-radio-button value="dinner">{{ $t('recipes.dinner') }}</el-radio-button>
```

- [ ] **Step 2: Search for any remaining deprecated radio patterns**

Run: `rg -n "<el-radio|<el-radio-button" frontend/src`
Expected: only `value=` usage remains for radios/buttons that carry values.

- [ ] **Step 3: Run frontend build**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/ProfileView.vue frontend/src/views/RecipesView.vue
git commit -m "chore: migrate radio controls to element plus value api"
```

## Task 4: Verify Runtime Behavior And Record Manual Checks

**Files:**
- Create: `docs/2026-04-05-post-debug-meal-chat-hardening-review.md`

- [ ] **Step 1: Run verification commands**

Run: `uv run pytest tests/api/test_meal_chat_router.py -v`
Expected: PASS

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 2: Execute manual checks and write them down**

```md
# Post-Debug Meal Chat Hardening Review

- Invalid login shows credential-specific feedback instead of silent failure.
- Expired auth during meal-chat send or generate redirects or prompts re-login explicitly.
- Generation failure copy is different from message-send failure copy.
- Meal chat no longer says "message not sent" when only `/generate` fails.
- Profile page no longer emits Element Plus radio deprecation warnings.
- Recipes page no longer emits Element Plus radio-button deprecation warnings.
```

- [ ] **Step 3: Commit**

```bash
git add docs/2026-04-05-post-debug-meal-chat-hardening-review.md
git commit -m "docs: record post-debug meal chat hardening verification"
```

## Risks To Watch

- Do not over-normalize every Axios error into auth state. Only 401 should trigger auth-required handling.
- `authStore.login()` currently returns a bare boolean; changing its contract will ripple into login callers. Keep that change small and update all call sites in the same patch.
- Avoid regressing the immersive flow by resetting `overlayMode` too aggressively on recoverable failures.
- The backend may still log upstream DeepSeek auth issues; this plan is only for making frontend behavior accurate and less misleading.

## Execution Notes

- Use `@systematic-debugging` evidence already gathered:
  - `/generate` failure was environment-driven but surfaced with the wrong message.
  - `auth/token` 401 is a distinct auth path and should not be conflated with meal-chat send/generate failures.
  - Element Plus radio warnings are caused by deprecated `label`-as-value usage in existing views.
- Before claiming completion, run the exact verification commands above and manually confirm the console warning cleanup in the browser.
