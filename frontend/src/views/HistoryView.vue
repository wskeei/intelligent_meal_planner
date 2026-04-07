<template>
  <div class="history-page">
    <header class="page-header">
      <h1>{{ $t('history.title') }}</h1>
      <p class="subtitle">{{ $t('history.subtitle') }}</p>
    </header>

    <section v-loading="loading" class="history-content">
      <AppEmptyState
        v-if="error"
        :icon="WarningFilled"
        :eyebrow="$t('history.error_eyebrow')"
        :title="$t('history.error_title')"
        :description="$t('history.error_desc')"
      >
        <template #actions>
          <el-button type="primary" @click="loadHistory">{{ $t('common.retry') }}</el-button>
        </template>
      </AppEmptyState>

      <AppEmptyState
        v-else-if="!history.length"
        :icon="Clock"
        :eyebrow="$t('history.empty_eyebrow')"
        :title="$t('history.empty_title')"
        :description="$t('history.empty_desc')"
      >
        <template #actions>
          <el-button type="primary" @click="$router.push('/meal-plan')">
            {{ $t('history.go_generate') }}
          </el-button>
        </template>
      </AppEmptyState>

      <div v-else class="history-list">
        <article v-for="item in history" :key="item.id" class="history-card">
          <div class="history-head">
            <div>
              <p class="eyebrow">{{ $t('history.session_label') }}</p>
              <h2>{{ formatDate(item.created_at) }}</h2>
            </div>
            <div class="head-meta">
              <span class="meta-pill">{{ goalLabel(item.target.health_goal) }}</span>
              <span class="meta-pill accent">¥{{ item.target.max_budget }}</span>
            </div>
          </div>

          <div class="meal-grid">
            <section v-for="group in groupMeals(item)" :key="group.key" class="meal-group">
              <div class="meal-group-head">
                <span>{{ mealLabel(group.key) }}</span>
                <span>{{ group.items.length }} {{ $t('meal_plan.items') }}</span>
              </div>

              <div class="meal-list">
                <article
                  v-for="meal in group.items"
                  :key="`${item.id}-${group.key}-${meal.recipe_id}`"
                  class="meal-item"
                >
                  <div>
                    <p class="meal-name">{{ meal.recipe_name }}</p>
                    <p class="meal-info">{{ meal.calories.toFixed(0) }} kcal</p>
                  </div>
                  <strong>¥{{ meal.price.toFixed(1) }}</strong>
                </article>
              </div>
            </section>
          </div>

          <div class="summary-row">
            <span>{{ $t('history.total_calories') }} <strong>{{ item.nutrition.total_calories }}</strong> kcal</span>
            <span>{{ $t('history.total_price') }} <strong>¥{{ item.nutrition.total_price.toFixed(1) }}</strong></span>
          </div>

          <div class="actions">
            <el-button
              v-if="item.source_session_id"
              plain
              @click="attachToWeeklyPlan(item)"
            >
              {{ $t('weekly_plan.attach_day') }}
            </el-button>
            <el-button type="primary" @click="reuse(item)">
              {{ $t('history.reuse') }}
            </el-button>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Clock, WarningFilled } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { mealPlanApi, type MealPlan } from '@/api'
import AppEmptyState from '@/components/common/AppEmptyState.vue'

const { t, locale } = useI18n()
const router = useRouter()

const history = ref<MealPlan[]>([])
const loading = ref(false)
const error = ref(false)

const formatter = computed(
  () =>
    new Intl.DateTimeFormat(locale.value === 'zh' ? 'zh-CN' : 'en-US', {
      dateStyle: 'medium',
      timeStyle: 'short'
    })
)

function goalLabel(goal: string) {
  return t(`meal_plan.goals.${goal}`)
}

function mealLabel(type: string) {
  return t(`recipes.${type}`)
}

function groupMeals(item: MealPlan) {
  const order = ['breakfast', 'lunch', 'dinner']
  return order
    .map((key) => ({
      key,
      items: item.meals.filter((meal) => meal.meal_type === key)
    }))
    .filter((group) => group.items.length > 0)
}

function formatDate(value: string) {
  return formatter.value.format(new Date(value))
}

async function loadHistory() {
  loading.value = true
  error.value = false

  try {
    const { data } = await mealPlanApi.getHistory(12)
    history.value = data
  } catch (fetchError) {
    console.error(fetchError)
    error.value = true
  } finally {
    loading.value = false
  }
}

function reuse(item: MealPlan) {
  const tags = item.target.preferred_tags.join(',')
  const disliked = item.target.disliked_foods.join(',')

  router.push({
    path: '/meal-plan',
    query: {
      reuse_source: 'history',
      reuse_goal: item.target.health_goal,
      reuse_budget: String(item.target.max_budget),
      reuse_tags: tags || undefined,
      reuse_disliked: disliked || undefined
    }
  })
}

function attachToWeeklyPlan(item: MealPlan) {
  if (!item.source_session_id) return

  router.push({
    path: '/weekly-plan',
    query: {
      source_session_id: item.source_session_id,
      meal_plan_id: item.id,
      source_label: item.meals.map((meal) => meal.recipe_name).join(' / ')
    }
  })
}

onMounted(loadHistory)
</script>

<style scoped>
.history-page {
  display: grid;
  gap: 24px;
}

.page-header h1 {
  margin: 0;
  color: var(--color-secondary);
  font-size: clamp(2rem, 4vw, 2.6rem);
}

.subtitle {
  margin: 8px 0 0;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.history-content {
  min-height: 240px;
}

.history-list {
  display: grid;
  gap: 18px;
}

.history-card {
  display: grid;
  gap: 18px;
  padding: 24px;
  border-radius: 24px;
  background: var(--gradient-surface);
  border: 1px solid var(--color-border-soft);
  box-shadow: var(--shadow-md);
}

.history-head,
.summary-row,
.actions {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.eyebrow {
  margin: 0 0 8px;
  color: var(--color-text-light);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.history-head h2,
.meal-name,
.meal-group-head span:first-child {
  margin: 0;
  color: var(--color-secondary);
}

.head-meta {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.meta-pill {
  padding: 10px 14px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-border-soft) 54%, transparent);
  color: var(--color-text-secondary);
  font-weight: 600;
}

.meta-pill.accent {
  background: var(--color-accent-soft);
  color: var(--color-primary-dark);
}

.meal-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}

.meal-group {
  display: grid;
  gap: 12px;
  padding: 16px;
  border-radius: 18px;
  background: var(--color-surface-muted);
  border: 1px solid var(--color-border-soft);
}

.meal-group-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: var(--color-text-secondary);
  font-size: 0.86rem;
}

.meal-list {
  display: grid;
  gap: 10px;
}

.meal-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  min-width: 0;
  padding: 12px;
  border-radius: 14px;
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-soft);
}

.meal-name {
  font-weight: 700;
  word-break: break-word;
}

.meal-info {
  margin: 4px 0 0;
  color: var(--color-text-secondary);
  font-size: 0.84rem;
}

.summary-row {
  flex-wrap: wrap;
  color: var(--color-text-secondary);
}

.summary-row strong {
  color: var(--color-secondary);
}

.actions {
  justify-content: flex-end;
}

@media (max-width: 720px) {
  .history-card,
  .history-head,
  .summary-row,
  .actions {
    align-items: flex-start;
  }

  .history-head,
  .summary-row,
  .actions {
    flex-direction: column;
  }

  .head-meta {
    justify-content: flex-start;
  }

  .actions :deep(.el-button) {
    width: 100%;
    min-height: 44px;
  }
}
</style>
