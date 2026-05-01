<template>
  <div class="weekly-plan-page">
    <!-- 1. Page header -->
    <header class="page-header">
      <div class="page-header__left">
        <h1>{{ $t('weekly_plan.title') }}</h1>
        <PlanSwitcher
          :plans="plans"
          :active-plan-id="activePlan?.id ?? null"
          @select="openPlan"
        />
      </div>
      <div
        v-if="activePlan && activePlan.days.length"
        class="page-header__right"
      >
        <el-input
          v-model="shoppingListName"
          class="list-name-input"
          :placeholder="$t('weekly_plan.list_name_placeholder')"
        />
        <el-button
          type="primary"
          :loading="generating"
          @click="generateShoppingList"
        >
          {{ $t('weekly_plan.generate_list') }}
        </el-button>
      </div>
    </header>

    <!-- 2. Pending attach banner -->
    <section v-if="pendingAttach" class="attach-banner">
      <div class="attach-banner__info">
        <p class="attach-banner__label">{{ $t('weekly_plan.attach_day') }}</p>
        <p class="attach-banner__source">{{ attachSourceLabel }}</p>
      </div>
      <div class="attach-banner__actions">
        <el-input v-model="selectedPlanDate" type="date" class="attach-banner__date" />
        <el-button
          type="primary"
          :loading="attaching"
          :disabled="!activePlan || !selectedPlanDate"
          @click="attachPendingDay"
        >
          {{ $t('weekly_plan.attach_confirm') }}
        </el-button>
      </div>
      <p v-if="!activePlan" class="attach-banner__hint">
        {{ $t('weekly_plan.pick_plan_first') }}
      </p>
    </section>

    <!-- 3. Loading skeleton -->
    <div v-if="loading" class="skeleton-list">
      <div v-for="n in 3" :key="n" class="skeleton-section">
        <div class="skeleton-line skeleton-line--heading" />
        <div class="skeleton-line skeleton-line--body" />
        <div class="skeleton-line skeleton-line--body short" />
      </div>
    </div>

    <!-- 4. Load error -->
    <AppEmptyState
      v-else-if="loadError && !activePlan && !plans.length"
      :title="$t('weekly_plan.load_failed_title')"
      :description="loadError"
    >
      <template #actions>
        <el-button type="primary" @click="loadInitialState">
          {{ $t('common.retry') }}
        </el-button>
      </template>
    </AppEmptyState>

    <!-- 5. No plans empty state -->
    <AppEmptyState
      v-else-if="!plans.length && !loading"
      :title="$t('weekly_plan.empty_title')"
      :description="$t('weekly_plan.empty_desc')"
    />

    <!-- 6. Plan with no days -->
    <AppEmptyState
      v-else-if="activePlan && !activePlan.days.length"
      :title="$t('weekly_plan.days_empty_title')"
      :description="$t('weekly_plan.days_empty_desc')"
    />

    <!-- 7. Day list -->
    <section
      v-else-if="activePlan && activePlan.days.length"
      class="day-list"
    >
      <div class="plan-info">
        <span class="plan-info__count">
          {{
            $t('weekly_plan.plan_info', {
              count: activePlan.days.length,
              date: formatDate(activePlan.created_at ?? '')
            })
          }}
        </span>
        <span v-if="activePlan.notes" class="plan-info__notes">{{ activePlan.notes }}</span>
      </div>
      <DaySection
        v-for="day in sortedDays"
        :key="day.id"
        :day="day"
        @remove-day="removeDay"
      />
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
import DaySection from '@/components/weekly-plan/DaySection.vue'
import PlanSwitcher from '@/components/weekly-plan/PlanSwitcher.vue'
import { getApiErrorDetail } from '@/api'
import { useShoppingStore } from '@/stores/shopping'
import { useWeeklyPlanStore } from '@/stores/weeklyPlan'
import { formatDisplayDate } from '@/utils/resilience'

const { locale, t } = useI18n()
const route = useRoute()
const router = useRouter()

const weeklyPlanStore = useWeeklyPlanStore()
const shoppingStore = useShoppingStore()
const { plans, activePlan, loading } = storeToRefs(weeklyPlanStore)

const selectedPlanDate = ref(getLocalDateInputValue())
const shoppingListName = ref('')
const attaching = ref(false)
const generating = ref(false)
const loadError = ref('')

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

const sortedDays = computed(() => {
  if (!activePlan.value) return []
  return [...activePlan.value.days].sort((a, b) =>
    a.plan_date.localeCompare(b.plan_date)
  )
})

function formatDate(value: string) {
  return formatDisplayDate(value, locale.value)
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

async function openPlan(planId: number) {
  loadError.value = ''
  try {
    await weeklyPlanStore.openPlan(planId)
  } catch (error) {
    handleWeeklyPlanError(error, 'weekly_plan.errors.load_failed')
  }
}

async function loadInitialState() {
  loadError.value = ''

  try {
    await weeklyPlanStore.loadPlans()
    await ensureActivePlan()
  } catch (error) {
    loadError.value = t('weekly_plan.errors.load_failed')
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

onMounted(() => {
  loadInitialState()
})
</script>

<style scoped>
.weekly-plan-page {
  max-width: 800px;
  display: grid;
  gap: 24px;
  margin: 0 auto;
}

/* ── Page header ── */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
}

.page-header__left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.page-header__left h1 {
  margin: 0;
  font-size: var(--text-4xl);
  font-weight: var(--weight-bold);
  color: var(--color-secondary);
  letter-spacing: var(--tracking-tight);
}

.page-header__right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.list-name-input {
  width: min(240px, 100%);
}

/* ── Pending attach banner ── */
.attach-banner {
  display: grid;
  gap: 12px;
  padding: 16px 20px;
  background: var(--color-accent-soft);
  border: 1px solid var(--color-border-accent);
  border-radius: 12px;
}

.attach-banner__info {
  min-width: 0;
}

.attach-banner__label {
  margin: 0;
  font-size: var(--text-base);
  font-weight: var(--weight-bold);
  color: var(--color-secondary);
}

.attach-banner__source {
  margin: 4px 0 0;
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
  overflow-wrap: anywhere;
}

.attach-banner__actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.attach-banner__date {
  width: min(200px, 100%);
}

.attach-banner__hint {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
}

/* ── Loading skeleton ── */
.skeleton-list {
  display: grid;
  gap: 20px;
}

.skeleton-section {
  display: grid;
  gap: 12px;
  padding: 20px;
  border-radius: 14px;
  background: var(--gradient-surface);
  border: 1px solid var(--color-border-soft);
}

.skeleton-line {
  height: 14px;
  border-radius: 7px;
  background: var(--color-border-soft);
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}

.skeleton-line--heading {
  height: 18px;
  width: 40%;
}

.skeleton-line--body {
  width: 80%;
}

.skeleton-line--body.short {
  width: 55%;
}

@keyframes skeleton-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ── Plan info ── */
.plan-info {
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex-wrap: wrap;
  padding-bottom: 8px;
}

.plan-info__count {
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-text-secondary);
}

.plan-info__notes {
  font-size: var(--text-sm);
  color: var(--color-text-light);
  font-style: italic;
  overflow-wrap: anywhere;
}

/* ── Day list ── */
.day-list {
  display: grid;
  gap: 0;
}

/* ── Mobile ── */
@media (max-width: 640px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .page-header__left {
    flex-direction: column;
    align-items: flex-start;
  }

  .page-header__right {
    flex-direction: column;
    align-items: stretch;
  }

  .page-header__right :deep(.el-button) {
    width: 100%;
    min-height: 44px;
  }

  .list-name-input {
    width: 100%;
  }

  .attach-banner__actions {
    flex-direction: column;
    align-items: stretch;
  }

  .attach-banner__date {
    width: 100%;
  }

  .attach-banner__actions :deep(.el-button) {
    width: 100%;
    min-height: 44px;
  }
}
</style>
