# Post-Debug Meal Chat Hardening Review

- Invalid login shows credential-specific feedback instead of silent failure.
  Status: Implemented in `frontend/src/stores/auth.ts` and `frontend/src/views/LoginView.vue`. Browser/manual verification still recommended.
- Expired auth during meal-chat send or generate redirects or prompts re-login explicitly.
  Status: Implemented in `frontend/src/views/MealPlanView.vue` with 401-specific handling via `isUnauthorizedError()`, logout, and `meal_plan.auth_required` messaging.
- Generation failure copy is different from message-send failure copy.
  Status: Implemented in `frontend/src/views/MealPlanView.vue` and locale files.
- Meal chat no longer says "message not sent" when only `/generate` fails.
  Status: Implemented by splitting the generate catch path to `generation_inline_error` / `generation_failed`.
- Profile page no longer emits Element Plus radio deprecation warnings.
  Status: Deprecated `label` usage replaced with `value` in `frontend/src/views/ProfileView.vue`. Browser/manual console verification still recommended.
- Recipes page no longer emits Element Plus radio-button deprecation warnings.
  Status: Deprecated `label` usage replaced with `value` in `frontend/src/views/RecipesView.vue`. Browser/manual console verification still recommended.

Verification run:
- `uv run pytest tests/api/test_meal_chat_router.py -v`
- `cd frontend && npm run build`
- `rg -n "<el-radio|<el-radio-button" frontend/src`
