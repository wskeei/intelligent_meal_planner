<template>
  <div class="weekly-plan-page">
    <header class="page-header">
      <div>
        <h1>{{ $t('weekly_plan.title') }}</h1>
        <p class="subtitle">{{ $t('weekly_plan.subtitle') }}</p>
      </div>
      <el-button
        v-if="activePlan"
        type="primary"
        :loading="generating"
        @click="generateShoppingList"
      >
        {{ $t('weekly_plan.generate_list') }}
      </el-button>
    </header>

    <section class="weekly-layout">
      <aside class="sidebar-stack">
        <el-card class="create-card" shadow="never">
          <template #header>
            <div class="section-head">
              <div>
                <h2>{{ $t('weekly_plan.create') }}</h2>
                <p>{{ $t('weekly_plan.create_desc') }}</p>
              </div>
            </div>
          </template>

          <div class="form-stack">
            <el-input v-model="newPlanName" :placeholder="$t('weekly_plan.create_placeholder')" />
            <el-input
              v-model="newPlanNotes"
              type="textarea"
              :rows="3"
              resize="none"
              :placeholder="$t('weekly_plan.notes_placeholder')"
            />
            <el-button type="primary" :loading="creating" :disabled="!newPlanName.trim()" @click="createPlan">
              {{ $t('weekly_plan.create') }}
            </el-button>
          </div>
        </el-card>

        <el-card class="plans-card" shadow="never">
          <template #header>
            <div class="section-head">
              <div>
                <h2>{{ $t('weekly_plan.saved_plans') }}</h2>
                <p>{{ $t('weekly_plan.saved_desc') }}</p>
              </div>
            </div>
          </template>

          <div v-if="plans.length" class="plan-list">
            <button
              v-for="plan in plans"
              :key="plan.id"
              type="button"
              class="plan-button"
              :class="{ active: activePlan?.id === plan.id }"
              @click="openPlan(plan.id)"
            >
              <span class="plan-name">{{ plan.name }}</span>
              <span class="plan-meta">{{ $t('weekly_plan.days_count', { count: plan.day_count }) }}</span>
            </button>
          </div>

          <p v-else class="muted-copy">{{ $t('weekly_plan.empty_desc') }}</p>
        </el-card>
      </aside>

      <section class="content-stack">
        <el-card v-if="pendingAttach" class="attach-card" shadow="never">
          <template #header>
            <div class="section-head">
              <div>
                <h2>{{ $t('weekly_plan.attach_day') }}</h2>
                <p>{{ attachSourceLabel }}</p>
              </div>
            </div>
          </template>

          <div class="attach-grid">
            <el-input v-model="selectedPlanDate" type="date" />
            <el-button
              type="primary"
              :loading="attaching"
              :disabled="!activePlan || !selectedPlanDate"
              @click="attachPendingDay"
            >
              {{ $t('weekly_plan.attach_confirm') }}
            </el-button>
          </div>
          <p class="muted-copy" v-if="!activePlan">{{ $t('weekly_plan.pick_plan_first') }}</p>
        </el-card>

        <AppEmptyState
          v-if="!activePlan && !loading"
          :title="$t('weekly_plan.empty_title')"
          :description="$t('weekly_plan.empty_desc')"
        />

        <template v-else-if="activePlan">
          <el-card class="plan-shell" shadow="never">
            <template #header>
              <div class="plan-shell-head">
                <div>
                  <h2>{{ activePlan.name }}</h2>
                  <p>{{ activePlan.notes || $t('weekly_plan.no_notes') }}</p>
                </div>
                <el-input
                  v-model="shoppingListName"
                  class="list-name-input"
                  :placeholder="$t('weekly_plan.list_name_placeholder')"
                />
              </div>
            </template>

            <div v-if="activePlan.days.length" class="day-grid">
              <article v-for="day in activePlan.days" :key="day.id" class="day-card">
                <div class="day-head">
                  <div>
                    <p class="eyebrow">{{ formatDate(day.plan_date) }}</p>
                    <h3>{{ $t('weekly_plan.day_snapshot') }}</h3>
                  </div>
                  <el-button text type="danger" @click="removeDay(day.id)">
                    {{ $t('common.delete') }}
                  </el-button>
                </div>

                <div class="meal-list">
                  <article
                    v-for="meal in day.meal_plan_snapshot.meals || []"
                    :key="`${day.id}-${meal.recipe_id}-${meal.meal_type}`"
                    class="meal-item"
                  >
                    <div>
                      <p class="meal-name">{{ meal.recipe_name }}</p>
                      <p class="meal-meta">{{ meal.meal_type }} · {{ meal.calories }} kcal</p>
                    </div>
                    <strong>¥{{ Number(meal.price).toFixed(1) }}</strong>
                  </article>
                </div>
              </article>
            </div>

            <AppEmptyState
              v-else
              :title="$t('weekly_plan.days_empty_title')"
              :description="$t('weekly_plan.days_empty_desc')"
            />
          </el-card>
        </template>
      </section>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import AppEmptyState from '@/components/common/AppEmptyState.vue'
import { getApiErrorDetail } from '@/api'
import { useShoppingStore } from '@/stores/shopping'
import { useWeeklyPlanStore } from '@/stores/weeklyPlan'

const { locale, t } = useI18n()
const route = useRoute()
const router = useRouter()

const weeklyPlanStore = useWeeklyPlanStore()
const shoppingStore = useShoppingStore()
const { plans, activePlan, loading } = storeToRefs(weeklyPlanStore)

const newPlanName = ref('')
const newPlanNotes = ref('')
const selectedPlanDate = ref(getLocalDateInputValue())
const shoppingListName = ref('')
const creating = ref(false)
const attaching = ref(false)
const generating = ref(false)

const pendingAttach = computed(() => {
  const sourceSessionId =
    typeof route.query.source_session_id === 'string' ? route.query.source_session_id : ''
  const mealPlanId = typeof route.query.meal_plan_id === 'string' ? route.query.meal_plan_id : ''

  if (!sourceSessionId || !mealPlanId) return null

  return {
    source_session_id: sourceSessionId,
    meal_plan_id: mealPlanId,
    source_label:
      typeof route.query.source_label === 'string' ? route.query.source_label : ''
  }
})

const attachSourceLabel = computed(() =>
  pendingAttach.value?.source_label || t('weekly_plan.pending_attach_desc')
)

const formatter = computed(
  () =>
    new Intl.DateTimeFormat(locale.value === 'zh' ? 'zh-CN' : 'en-US', {
      dateStyle: 'medium'
    })
)

function formatDate(value: string) {
  return formatter.value.format(new Date(value))
}

function getLocalDateInputValue(baseDate = new Date()) {
  const year = baseDate.getFullYear()
  const month = `${baseDate.getMonth() + 1}`.padStart(2, '0')
  const day = `${baseDate.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

function handleWeeklyPlanError(error: unknown, fallbackKey: string) {
  const detail = getApiErrorDetail(error)
  if (detail === 'Plan date already occupied') {
    ElMessage.error(t('weekly_plan.errors.plan_date_occupied'))
    return
  }
  if (detail === 'Weekly plan not found' || detail === 'Meal chat session not found') {
    ElMessage.error(t('weekly_plan.errors.resource_missing'))
    return
  }
  ElMessage.error(t(fallbackKey))
}

async function ensureActivePlan() {
  if (activePlan.value || !plans.value.length) return
  await weeklyPlanStore.openPlan(plans.value[0].id)
}

async function createPlan() {
  const name = newPlanName.value.trim()
  if (!name) return

  creating.value = true
  try {
    await weeklyPlanStore.createPlan(name, newPlanNotes.value.trim())
    newPlanName.value = ''
    newPlanNotes.value = ''
    ElMessage.success(t('weekly_plan.create_success'))
  } catch (error) {
    handleWeeklyPlanError(error, 'weekly_plan.errors.create_failed')
  } finally {
    creating.value = false
  }
}

async function openPlan(planId: number) {
  try {
    await weeklyPlanStore.openPlan(planId)
  } catch (error) {
    handleWeeklyPlanError(error, 'weekly_plan.errors.load_failed')
  }
}

async function attachPendingDay() {
  if (!activePlan.value || !pendingAttach.value || !selectedPlanDate.value) return

  attaching.value = true
  try {
    await weeklyPlanStore.attachDay(activePlan.value.id, {
      plan_date: selectedPlanDate.value,
      meal_plan_id: pendingAttach.value.meal_plan_id,
      source_session_id: pendingAttach.value.source_session_id
    })
    await router.replace({ path: '/weekly-plan' })
    ElMessage.success(t('weekly_plan.attach_success'))
  } catch (error) {
    handleWeeklyPlanError(error, 'weekly_plan.errors.attach_failed')
  } finally {
    attaching.value = false
  }
}

async function removeDay(dayId: number) {
  if (!activePlan.value) return
  try {
    await weeklyPlanStore.removeDay(activePlan.value.id, dayId)
    ElMessage.success(t('weekly_plan.remove_success'))
  } catch (error) {
    handleWeeklyPlanError(error, 'weekly_plan.errors.remove_failed')
  }
}

async function generateShoppingList() {
  if (!activePlan.value) return

  generating.value = true
  try {
    const list = await shoppingStore.generateFromWeeklyPlan(
      activePlan.value.id,
      shoppingListName.value.trim()
    )
    await router.push({
      path: '/shopping-list',
      query: { list: String(list.id) }
    })
    ElMessage.success(t('weekly_plan.generate_success'))
  } catch (error) {
    const detail = getApiErrorDetail(error)
    if (detail === 'Weekly plan not found') {
      ElMessage.error(t('weekly_plan.errors.resource_missing'))
    } else {
      ElMessage.error(t('weekly_plan.errors.generate_failed'))
    }
  } finally {
    generating.value = false
  }
}

onMounted(async () => {
  await weeklyPlanStore.loadPlans()
  await ensureActivePlan()
})
</script>

<style scoped>
.weekly-plan-page {
  display: grid;
  gap: 24px;
}

.page-header,
.weekly-layout,
.attach-grid,
.plan-shell-head,
.day-head,
.meal-item {
  display: flex;
  gap: 16px;
}

.page-header,
.day-head,
.meal-item {
  justify-content: space-between;
  align-items: center;
}

.page-header {
  flex-wrap: wrap;
}

.page-header h1,
.section-head h2,
.plan-shell-head h2,
.day-head h3,
.meal-name {
  margin: 0;
  color: var(--color-secondary);
}

.subtitle,
.section-head p,
.muted-copy,
.plan-shell-head p,
.meal-meta,
.plan-meta {
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.subtitle,
.section-head p,
.plan-shell-head p {
  margin: 8px 0 0;
}

.weekly-layout {
  align-items: flex-start;
}

.sidebar-stack,
.content-stack,
.form-stack,
.plan-list,
.day-grid,
.meal-list {
  display: grid;
  gap: 16px;
}

.sidebar-stack {
  width: min(340px, 100%);
  flex-shrink: 0;
}

.content-stack {
  flex: 1;
  min-width: 0;
}

.plan-button {
  width: 100%;
  display: grid;
  gap: 6px;
  padding: 16px;
  border-radius: 18px;
  border: 1px solid var(--color-border-soft);
  background: var(--gradient-surface);
  text-align: left;
}

.plan-button.active {
  border-color: var(--color-border-accent);
  background: color-mix(in srgb, var(--color-accent-soft) 84%, var(--color-surface-raised));
}

.plan-name,
.meal-name {
  font-weight: 700;
}

.attach-grid {
  align-items: center;
  flex-wrap: wrap;
}

.attach-grid :deep(.el-input) {
  width: min(240px, 100%);
}

.plan-shell-head {
  align-items: flex-start;
  flex-wrap: wrap;
}

.list-name-input {
  width: min(320px, 100%);
}

.day-grid {
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
}

.day-card {
  display: grid;
  gap: 14px;
  padding: 20px;
  border-radius: 22px;
  background: var(--gradient-surface);
  border: 1px solid var(--color-border-soft);
  box-shadow: var(--shadow-sm);
}

.eyebrow {
  margin: 0 0 6px;
  color: var(--color-primary-dark);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.meal-list {
  gap: 10px;
}

.meal-item {
  padding: 12px 14px;
  border-radius: 14px;
  background: var(--color-surface-muted);
  border: 1px solid var(--color-border-soft);
  align-items: flex-start;
}

@media (max-width: 960px) {
  .weekly-layout {
    flex-direction: column;
  }

  .sidebar-stack {
    width: 100%;
  }
}

@media (max-width: 640px) {
  .attach-grid,
  .page-header,
  .plan-shell-head,
  .day-head,
  .meal-item {
    flex-direction: column;
    align-items: stretch;
  }

  .attach-grid :deep(.el-button),
  .form-stack :deep(.el-button),
  .page-header :deep(.el-button) {
    width: 100%;
    min-height: 44px;
  }
}
</style>
