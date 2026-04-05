<template>
  <transition name="result-overlay">
    <section
      v-if="visible && mealPlan"
      ref="rootRef"
      class="result-overlay-root"
      aria-modal="true"
      role="dialog"
      aria-labelledby="meal-chat-result-title"
    >
      <div class="result-overlay-backdrop" />
      <div ref="shellRef" class="result-overlay-shell" tabindex="-1">
        <header class="result-overlay-head">
          <button
            ref="returnButtonRef"
            class="back-link"
            type="button"
            @click="$emit('return-to-chat')"
          >
            {{ t('meal_plan.return_to_chat') }}
          </button>
          <div class="result-title-copy">
            <p class="eyebrow">{{ t('meal_plan.final_plan') }}</p>
            <h1 id="meal-chat-result-title">{{ t('meal_plan.result_title') }}</h1>
          </div>
          <div class="price-pill">
            <span>{{ t('meal_plan.total_cost') }}</span>
            <strong>¥{{ mealPlan.nutrition.total_price.toFixed(1) }}</strong>
          </div>
        </header>

        <main class="result-main">
          <section class="summary-grid">
            <div class="summary-item">
              <span>{{ t('meal_plan.field_labels.health_goal') }}</span>
              <strong>{{ goalLabel }}</strong>
            </div>
            <div class="summary-item">
              <span>{{ t('meal_plan.field_labels.budget') }}</span>
              <strong>{{ budgetLabel }}</strong>
            </div>
            <div class="summary-item">
              <span>{{ t('meal_plan.calories') }}</span>
              <strong>{{ mealPlan.nutrition.total_calories.toFixed(0) }} kcal</strong>
            </div>
            <div class="summary-item">
              <span>{{ t('meal_plan.protein') }}</span>
              <strong>{{ mealPlan.nutrition.total_protein.toFixed(0) }} g</strong>
            </div>
          </section>

          <div class="meal-groups">
            <section v-for="group in groupedMeals" :key="group.key" class="meal-group">
              <div class="meal-group-head">
                <span class="meal-label">{{ mealLabel(group.key) }}</span>
                <span class="meal-count">{{ group.items.length }} {{ t('meal_plan.items') }}</span>
              </div>

              <div class="meal-list">
                <article
                  v-for="meal in group.items"
                  :key="`${group.key}-${meal.recipe_id}`"
                  class="meal-item"
                >
                  <div>
                    <p class="meal-name">{{ meal.recipe_name }}</p>
                    <p class="meal-metrics">
                      {{ meal.calories.toFixed(0) }} kcal · {{ meal.protein.toFixed(0) }}g P
                    </p>
                  </div>
                  <strong>¥{{ meal.price.toFixed(1) }}</strong>
                </article>
              </div>
            </section>
          </div>
        </main>

        <section class="result-secondary">
          <article v-if="alternatives.length" class="secondary-card alternatives-card collapsed">
            <details>
              <summary>
                <span>{{ t('meal_plan.alt_title') }}</span>
                <span>{{ alternatives.length }} {{ t('meal_plan.items') }}</span>
              </summary>
              <div class="alternative-list">
                <article
                  v-for="alternative in alternatives"
                  :key="alternative.option_key"
                  class="alternative-card"
                >
                  <div>
                    <p class="alternative-title">{{ alternative.title }}</p>
                    <p class="alternative-rationale">{{ alternative.rationale }}</p>
                  </div>
                  <strong>¥{{ alternative.meal_plan.nutrition.total_price.toFixed(1) }}</strong>
                </article>
              </div>
            </details>
          </article>

          <article v-if="hasTraceSection" class="secondary-card trace-card collapsed">
            <details>
              <summary>
                <span>{{ t('meal_plan.crew_title') }}</span>
                <span>{{ t('meal_plan.trace_toggle') }}</span>
              </summary>
              <p v-if="traceUnavailableMessage" class="crew-empty">{{ traceUnavailableMessage }}</p>
              <div v-else-if="visibleCrewTrace.length" class="crew-timeline">
                <article
                  v-for="event in visibleCrewTrace"
                  :key="`${event.agent}-${event.message}`"
                  class="crew-event"
                >
                  <div class="crew-event-head">
                    <strong>{{ event.agent }}</strong>
                    <span class="crew-status">{{ event.status }}</span>
                  </div>
                  <p>{{ event.message }}</p>
                </article>
              </div>
              <p v-else class="crew-empty">{{ t('meal_plan.crew_empty') }}</p>
            </details>
          </article>
        </section>

        <footer class="result-actions">
          <button class="action-button primary" type="button" @click="$emit('add-to-list')">
            {{ t('meal_plan.add_to_list') }}
          </button>
          <button class="action-button secondary" type="button" @click="$emit('start-over')">
            {{ t('meal_plan.start_over') }}
          </button>
        </footer>
      </div>
    </section>
  </transition>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import type { CrewTraceEvent, MealPlan, NegotiatedMealPlanAlternative } from '@/api'

const props = defineProps<{
  visible: boolean
  mealPlan: MealPlan | null
  alternatives: NegotiatedMealPlanAlternative[]
  crewTrace: CrewTraceEvent[]
  preferences: Record<string, unknown>
}>()

const emit = defineEmits<{
  (event: 'return-to-chat'): void
  (event: 'add-to-list'): void
  (event: 'start-over'): void
}>()

const { t, locale } = useI18n()
const rootRef = ref<HTMLElement | null>(null)
const shellRef = ref<HTMLElement | null>(null)
const returnButtonRef = ref<HTMLButtonElement | null>(null)
let lastFocusedElement: HTMLElement | null = null

const groupedMeals = computed(() => {
  if (!props.mealPlan) return []

  const order = ['breakfast', 'lunch', 'dinner']
  const buckets = new Map<string, MealPlan['meals']>()

  for (const meal of props.mealPlan.meals) {
    const list = buckets.get(meal.meal_type) ?? []
    list.push(meal)
    buckets.set(meal.meal_type, list)
  }

  return order
    .filter((key) => buckets.has(key))
    .map((key) => ({ key, items: buckets.get(key) ?? [] }))
})

const goalLabel = computed(() => {
  const goal = props.preferences.health_goal
  return typeof goal === 'string' ? t(`meal_plan.goals.${goal}`) : '...'
})

const budgetLabel = computed(() => {
  const budget = props.preferences.budget ?? props.mealPlan?.target.max_budget
  return budget ? `¥${budget}` : '...'
})

const traceUnavailableMessage = computed(() =>
  locale.value === 'en' && props.crewTrace.length ? t('meal_plan.trace_unavailable_locale') : ''
)

const visibleCrewTrace = computed(() => (traceUnavailableMessage.value ? [] : props.crewTrace))

const hasTraceSection = computed(
  () => Boolean(traceUnavailableMessage.value) || props.crewTrace.length > 0
)

function mealLabel(type: string) {
  return t(`recipes.${type}`)
}

function getFocusableElements() {
  if (!shellRef.value) return []

  const selector = [
    'button:not([disabled])',
    '[href]',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])'
  ].join(', ')

  return Array.from(shellRef.value.querySelectorAll<HTMLElement>(selector)).filter(
    (element) => !element.hasAttribute('disabled') && element.tabIndex !== -1
  )
}

function restoreFocus() {
  if (lastFocusedElement) {
    lastFocusedElement.focus()
    lastFocusedElement = null
  }
}

function onKeydown(event: KeyboardEvent) {
  if (!props.visible) return

  if (event.key === 'Escape') {
    event.preventDefault()
    emit('return-to-chat')
    return
  }

  if (event.key !== 'Tab') return

  const focusable = getFocusableElements()
  if (!focusable.length) return

  const first = focusable[0]
  const last = focusable[focusable.length - 1]
  const active = document.activeElement as HTMLElement | null

  if (!active || !focusable.includes(active)) {
    event.preventDefault()
    first.focus()
    return
  }

  if (event.shiftKey && active === first) {
    event.preventDefault()
    last.focus()
    return
  }

  if (!event.shiftKey && active === last) {
    event.preventDefault()
    first.focus()
  }
}

async function activateModalBehavior() {
  lastFocusedElement = document.activeElement as HTMLElement | null
  document.addEventListener('keydown', onKeydown)
  await nextTick()
  if (returnButtonRef.value) {
    returnButtonRef.value.focus()
    return
  }
  shellRef.value?.focus()
}

function deactivateModalBehavior() {
  document.removeEventListener('keydown', onKeydown)
  restoreFocus()
}

watch(
  () => props.visible,
  async (visible) => {
    if (visible) {
      await activateModalBehavior()
      return
    }
    deactivateModalBehavior()
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  deactivateModalBehavior()
})
</script>

<style scoped>
.result-overlay-root {
  position: fixed;
  inset: 0;
  z-index: 81;
  overflow-y: auto;
  padding: clamp(16px, 3vw, 28px);
}

.result-overlay-backdrop {
  position: fixed;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(12, 24, 18, 0.2), rgba(12, 24, 18, 0.08)),
    rgba(245, 247, 242, 0.88);
  backdrop-filter: blur(18px);
}

.result-overlay-shell {
  position: relative;
  width: min(1220px, 100%);
  margin: 0 auto;
  padding: clamp(18px, 3vw, 28px);
  border-radius: 32px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(248, 251, 248, 0.96)),
    #ffffff;
  border: 1px solid rgba(47, 143, 81, 0.1);
  box-shadow: 0 32px 90px rgba(21, 48, 40, 0.16);
}

.result-overlay-head,
.meal-group-head,
.meal-item,
.crew-event-head,
.result-actions,
.alternative-card,
summary {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.result-overlay-head {
  align-items: flex-start;
  margin-bottom: 20px;
}

.back-link {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(21, 48, 40, 0.06);
  color: var(--color-secondary);
  font-weight: 700;
}

.result-title-copy {
  flex: 1;
  min-width: 0;
}

.price-pill {
  display: inline-grid;
  gap: 2px;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(126, 216, 139, 0.18);
  color: var(--color-primary-dark);
  font-weight: 700;
  text-align: right;
}

.price-pill span {
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.price-pill strong {
  font-size: 1.06rem;
}

.result-main {
  display: grid;
  gap: 16px;
}

.eyebrow,
.secondary-eyebrow {
  margin: 0 0 10px;
  color: var(--color-primary-dark);
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.result-title-copy h1 {
  margin: 0;
  color: var(--color-secondary);
  font-size: clamp(2rem, 4vw, 3.2rem);
  line-height: 1.02;
}

.meal-groups {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.meal-group {
  padding: 18px;
  border-radius: 24px;
  background: linear-gradient(180deg, #f8fbf8, #f2f7f3);
}

.meal-list,
.summary-grid,
.crew-timeline,
.alternative-list {
  display: grid;
  gap: 12px;
}

.meal-label,
.meal-name,
.alternative-title,
.crew-event-head strong,
.summary-item strong {
  color: var(--color-secondary);
}

.meal-label,
.meal-name,
.alternative-title {
  font-weight: 700;
}

.meal-count,
.meal-metrics,
.alternative-rationale,
.crew-event p,
.crew-empty,
.summary-item span {
  color: var(--color-text-secondary);
}

.meal-count {
  font-size: 0.82rem;
}

.meal-item,
.secondary-card,
.alternative-card,
.crew-event {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.9);
}

.meal-item {
  align-items: center;
}

.meal-name {
  margin: 0;
}

.meal-metrics,
.alternative-rationale,
.crew-event p {
  margin: 4px 0 0;
  line-height: 1.5;
}

.result-secondary {
  display: grid;
  gap: 12px;
  margin-top: 14px;
}

.summary-grid {
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.summary-item {
  padding: 14px;
  border-radius: 16px;
  background: #f7faf8;
}

.summary-item span {
  display: block;
  margin-bottom: 6px;
  font-size: 0.82rem;
}

.trace-card details {
  width: 100%;
}

.alternatives-card details,
.trace-card details {
  width: 100%;
}

.alternatives-card summary,
.trace-card summary {
  align-items: center;
  cursor: pointer;
  list-style: none;
  font-weight: 700;
  color: var(--color-secondary);
}

.alternatives-card summary::-webkit-details-marker,
.trace-card summary::-webkit-details-marker {
  display: none;
}

.alternatives-card details[open] .alternative-list,
.trace-card details[open] .crew-timeline,
.trace-card details[open] .crew-empty {
  margin-top: 16px;
}

.crew-event {
  border: 1px solid rgba(34, 197, 94, 0.12);
}

.crew-status {
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(34, 197, 94, 0.12);
  color: #166534;
  font-size: 0.76rem;
  font-weight: 700;
  text-transform: uppercase;
}

.result-actions {
  flex-wrap: wrap;
  margin-top: 18px;
}

.action-button {
  min-height: 46px;
  padding: 0 18px;
  border-radius: 999px;
  font-weight: 700;
}

.action-button.primary {
  background: linear-gradient(135deg, var(--color-primary-dark), var(--color-primary));
  color: #0d2b1b;
}

.action-button.secondary {
  background: rgba(21, 48, 40, 0.08);
  color: var(--color-secondary);
}

.result-overlay-enter-active {
  transition:
    opacity 360ms var(--overlay-ease),
    transform 420ms var(--overlay-ease);
}

.result-overlay-leave-active {
  transition:
    opacity var(--overlay-exit-duration) var(--overlay-ease),
    transform 220ms var(--overlay-ease);
}

.result-overlay-enter-from,
.result-overlay-leave-to {
  opacity: 0;
  transform: translateY(24px) scale(0.985);
}

@media (max-width: 900px) {
  .result-overlay-head {
    flex-wrap: wrap;
  }
}

@media (max-width: 640px) {
  .result-overlay-shell {
    padding: 16px;
    border-radius: 26px;
  }

  .result-overlay-head,
  .meal-group-head,
  .meal-item,
  .alternative-card,
  .result-actions,
  summary {
    flex-direction: column;
    align-items: flex-start;
  }

  .result-title-copy h1 {
    font-size: 2.1rem;
  }

  .price-pill {
    text-align: left;
  }

  .action-button {
    width: 100%;
  }
}
</style>
