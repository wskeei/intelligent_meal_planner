<template>
  <article class="day-section">
    <!-- Day header -->
    <div class="day-header">
      <div class="day-header__left">
        <span class="day-header__date">{{ displayDate }}</span>
        <span class="day-header__weekday">{{ weekday }}</span>
      </div>
      <button
        class="day-delete-btn"
        type="button"
        :aria-label="t('weekly_plan.delete_day')"
        @click="onRemove"
      >
        <el-icon :size="16"><Delete /></el-icon>
      </button>
    </div>

    <!-- Meal rows -->
    <ul class="meal-list">
      <li
        v-for="meal in meals"
        :key="meal.recipe_id + '-' + meal.meal_type"
        class="meal-row"
      >
        <span class="meal-row__type">{{ mealTypeLabel(meal.meal_type) }}</span>
        <span class="meal-row__name">{{ meal.recipe_name }}</span>
        <span class="meal-row__calories">{{ meal.calories }} kcal</span>
        <span class="meal-row__price">{{ formatCurrencyAmount(meal.price, locale, 0) }}</span>
      </li>
      <li v-if="meals.length === 0" class="meal-row meal-row--empty">
        <span class="meal-row__empty-label">{{ t('common.not_available') }}</span>
      </li>
    </ul>

    <!-- Daily summary -->
    <p class="day-summary">
      {{
        t('weekly_plan.daily_total', {
          calories: nutrition.total_calories,
          price: formatCurrencyAmount(nutrition.total_price, locale, 0)
        })
      }}
    </p>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Delete } from '@element-plus/icons-vue'
import type { WeeklyPlanDay } from '@/api'
import { formatDisplayDate, formatCurrencyAmount, resolveIntlLocale } from '@/utils/resilience'

const props = defineProps<{
  day: WeeklyPlanDay
}>()

const emit = defineEmits<{
  'remove-day': [id: number]
}>()

const { t, locale } = useI18n()

const meals = computed(() => props.day.meal_plan_snapshot.meals)
const nutrition = computed(() => props.day.nutrition_snapshot)

const displayDate = computed(() =>
  formatDisplayDate(props.day.plan_date, locale.value)
)

const weekday = computed(() => {
  if (!props.day.plan_date) return ''
  try {
    const date = new Date(props.day.plan_date)
    if (Number.isNaN(date.getTime())) return ''
    return new Intl.DateTimeFormat(resolveIntlLocale(locale.value), {
      weekday: 'long'
    }).format(date)
  } catch {
    return ''
  }
})

function mealTypeLabel(type: string): string {
  const key = `meal_types.${type}`
  const translated = t(key)
  return translated !== key ? translated : type
}

function onRemove() {
  emit('remove-day', props.day.id)
}
</script>

<style scoped>
/* ── Day section ── */
.day-section + .day-section {
  border-top: 1px solid var(--color-border-soft);
}

/* ── Day header ── */
.day-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 12px 0 6px;
}

.day-header__left {
  display: flex;
  align-items: baseline;
  gap: 10px;
  min-width: 0;
}

.day-header__date {
  font-size: var(--text-base);
  font-weight: var(--weight-bold);
  letter-spacing: var(--tracking-tight);
  color: var(--color-secondary);
}

.day-header__weekday {
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  letter-spacing: var(--tracking-wider);
  color: var(--color-text-light);
  text-transform: capitalize;
}

/* ── Delete button (hidden by default, shown on parent hover) ── */
.day-delete-btn {
  display: inline-grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--color-danger);
  opacity: 0;
  cursor: pointer;
  transition: opacity 160ms, background 160ms;
  flex-shrink: 0;
}

.day-delete-btn:hover {
  background: var(--color-danger-soft);
}

.day-delete-btn:focus-visible {
  opacity: 1;
  outline: none;
  box-shadow: var(--focus-ring);
}

.day-section:hover .day-delete-btn {
  opacity: 1;
}

/* Touch devices: always visible */
@media (hover: none) {
  .day-delete-btn {
    opacity: 1;
  }
}

/* ── Meal list ── */
.meal-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

/* ── Meal row ── */
.meal-row {
  display: grid;
  grid-template-columns: auto 1fr auto auto;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  align-items: center;
  transition: background 120ms;
}

.meal-row:not(.meal-row--empty):hover {
  background: var(--color-surface-raised);
}

.meal-row__type {
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
  letter-spacing: var(--tracking-wider);
  color: var(--color-accent-strong);
  text-transform: uppercase;
  white-space: nowrap;
}

.meal-row__name {
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.meal-row__calories {
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  color: var(--color-text-light);
  text-align: right;
  white-space: nowrap;
}

.meal-row__price {
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  color: var(--color-text-secondary);
  text-align: right;
  white-space: nowrap;
}

.meal-row--empty {
  padding: 16px 12px;
}

.meal-row__empty-label {
  font-size: var(--text-sm);
  color: var(--color-text-light);
  grid-column: 1 / -1;
  text-align: center;
}

/* ── Daily summary ── */
.day-summary {
  margin: 0;
  padding: 8px 12px 14px;
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  color: var(--color-text-light);
  text-align: right;
}

/* ── Mobile: 2-column layout, hide price ── */
@media (max-width: 640px) {
  .day-header {
    padding: 10px 0 4px;
  }

  .meal-row {
    grid-template-columns: 1fr auto;
    padding: 8px 8px;
    gap: 4px 8px;
  }

  .meal-row__type {
    grid-column: 1 / -1;
    padding-bottom: 2px;
  }

  .meal-row__calories {
    text-align: left;
  }

  .meal-row__price {
    display: none;
  }
}
</style>
