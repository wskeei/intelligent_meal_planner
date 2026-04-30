<template>
  <div class="home-page">
    <!-- Greeting -->
    <section class="greeting">
      <h1>{{ greetingText }}，{{ profile.username || $t('dashboard.guest') }}</h1>
      <p class="action-prompt">{{ $t('dashboard.action_prompt') }}</p>
      <el-button type="primary" size="large" tag="router-link" to="/meal-plan" class="cta">
        {{ $t('dashboard.start_planning') }}
      </el-button>
    </section>

    <!-- Continue session banner -->
    <section v-if="hasActiveSession" class="continue-banner">
      <div class="continue-text">
        <span class="continue-label">{{ $t('dashboard.continue_session') }}</span>
        <span class="continue-hint">{{ $t('dashboard.continue_session_hint') }}</span>
      </div>
      <div class="continue-actions">
        <el-button text type="primary" tag="router-link" to="/meal-plan">
          {{ $t('dashboard.continue_session') }}
        </el-button>
        <el-button text @click="dismissSession">
          {{ $t('dashboard.dismiss') }}
        </el-button>
      </div>
    </section>

    <!-- Loading skeleton -->
    <template v-if="loading">
      <div v-for="n in 3" :key="n" class="skeleton-row">
        <div class="skeleton-line skeleton-line--wide" />
        <div class="skeleton-line skeleton-line--narrow" />
      </div>
    </template>

    <!-- Activity stream -->
    <template v-else>
      <!-- Recent plans -->
      <section v-if="recentPlans.length" class="activity-section">
        <h2 class="section-heading">{{ $t('dashboard.recent_plans') }}</h2>
        <div class="activity-list">
          <div v-for="plan in recentPlans" :key="plan.id" class="activity-row">
            <div class="activity-info">
              <span class="activity-date">{{ formatRelativeDate(plan.created_at) }}</span>
              <span class="activity-detail">
                {{ Math.round(plan.nutrition.total_calories) }} kcal
                · ¥{{ plan.nutrition.total_price.toFixed(0) }}
                · {{ $t('dashboard.meal_count_hint', { count: plan.meals.length }) }}
              </span>
            </div>
            <el-button text type="primary" @click="reusePlan(plan)">
              {{ $t('dashboard.reuse') }}
            </el-button>
          </div>
        </div>
      </section>

      <!-- Active weekly plans -->
      <section v-if="weeklyPlans.length" class="activity-section">
        <h2 class="section-heading">{{ $t('dashboard.active_weekly_plans') }}</h2>
        <div class="activity-list">
          <router-link
            v-for="wp in weeklyPlans"
            :key="wp.id"
            to="/weekly-plan"
            class="activity-row activity-row--link"
          >
            <div class="activity-info">
              <span class="activity-name">{{ wp.name }}</span>
              <span class="activity-detail">{{ $t('dashboard.days_count', { n: wp.day_count }) }}</span>
            </div>
          </router-link>
        </div>
      </section>

      <!-- Empty state -->
      <AppEmptyState
        v-if="!recentPlans.length && !weeklyPlans.length"
        :title="$t('dashboard.empty_title')"
        :description="$t('dashboard.empty_desc')"
      >
        <template #actions>
          <el-button type="primary" tag="router-link" to="/meal-plan">
            {{ $t('dashboard.start_planning') }}
          </el-button>
        </template>
      </AppEmptyState>
    </template>
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { mealPlanApi, type MealPlan } from '@/api'
import AppEmptyState from '@/components/common/AppEmptyState.vue'
import { useUserStore } from '@/stores/user'
import { useWeeklyPlanStore } from '@/stores/weeklyPlan'

const { t } = useI18n()
const router = useRouter()

const userStore = useUserStore()
const { profile } = storeToRefs(userStore)

const weeklyPlanStore = useWeeklyPlanStore()

const recentPlans = ref<MealPlan[]>([])
const loading = ref(true)

const weeklyPlans = computed(() => weeklyPlanStore.plans)

const activeSessionKey = 'meal-chat-active-session-id'
const hasActiveSession = ref(!!localStorage.getItem(activeSessionKey))

const greetingText = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return t('dashboard.greeting_morning')
  if (hour < 18) return t('dashboard.greeting_afternoon')
  return t('dashboard.greeting_evening')
})

function formatRelativeDate(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return t('dashboard.today')
  if (diffDays === 1) return t('dashboard.yesterday')
  return t('dashboard.days_ago', { n: diffDays })
}

function reusePlan(plan: MealPlan) {
  const target = plan.target
  router.push({
    path: '/meal-plan',
    query: {
      reuse_source: 'home',
      reuse_goal: target.health_goal || undefined,
      reuse_budget: target.max_budget ? String(target.max_budget) : undefined,
      reuse_tags: target.preferred_tags?.length ? target.preferred_tags.join(',') : undefined,
      reuse_disliked: target.disliked_foods?.length ? target.disliked_foods.join(',') : undefined
    }
  })
}

function dismissSession() {
  localStorage.removeItem(activeSessionKey)
  hasActiveSession.value = false
}

onMounted(async () => {
  try {
    const [plans] = await Promise.all([
      mealPlanApi.getHistory(5),
      weeklyPlanStore.loadPlans()
    ])
    recentPlans.value = plans.data
  } catch (e) {
    console.error('[HomeView] Failed to load activity data:', e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.home-page {
  display: grid;
  gap: 28px;
  max-width: 640px;
}

.greeting {
  display: grid;
  gap: 10px;
}

.greeting h1 {
  margin: 0;
  color: var(--color-secondary);
  font-size: var(--text-4xl);
  font-weight: var(--weight-bold);
  line-height: var(--leading-tight);
  letter-spacing: var(--tracking-tight);
}

.action-prompt {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
}

.cta {
  margin-top: 4px;
  justify-self: start;
}

/* Continue session banner */
.continue-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 14px 18px;
  border-radius: 12px;
  background: var(--color-accent-soft);
  border: 1px solid var(--color-border-accent);
}

.continue-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.continue-label {
  font-size: var(--text-sm);
  font-weight: var(--weight-bold);
  color: var(--color-accent-strong);
}

.continue-hint {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.continue-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

/* Activity sections */
.activity-section {
  display: grid;
  gap: 12px;
}

.section-heading {
  margin: 0;
  font-size: var(--text-sm);
  font-weight: var(--weight-bold);
  color: var(--color-text-light);
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
}

.activity-list {
  display: grid;
  gap: 2px;
}

.activity-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  border-radius: 10px;
  transition: background-color 160ms ease;
}

.activity-row:hover {
  background: var(--color-surface-raised);
}

.activity-row--link {
  text-decoration: none;
  color: inherit;
  cursor: pointer;
}

.activity-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.activity-date,
.activity-name {
  font-size: var(--text-base);
  font-weight: var(--weight-medium);
  color: var(--color-secondary);
}

.activity-detail {
  font-size: var(--text-sm);
  color: var(--color-text-light);
}

/* Skeleton loading */
.skeleton-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px 16px;
  border-radius: 10px;
  background: var(--color-surface-raised);
}

.skeleton-line {
  height: 14px;
  border-radius: 6px;
  background: var(--color-border-soft);
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-line--wide {
  width: 60%;
}

.skeleton-line--narrow {
  width: 35%;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* Mobile */
@media (max-width: 640px) {
  .cta {
    width: 100%;
  }

  .continue-banner {
    flex-direction: column;
    align-items: flex-start;
  }

  .continue-actions {
    width: 100%;
  }
}
</style>
