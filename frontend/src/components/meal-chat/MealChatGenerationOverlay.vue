<template>
  <transition name="generation-overlay">
    <section
      v-if="visible"
      class="generation-overlay-root"
      aria-modal="true"
      role="dialog"
      aria-labelledby="meal-chat-generation-title"
      aria-describedby="meal-chat-generation-summary"
    >
      <div class="generation-overlay-backdrop" />
      <div ref="shellRef" class="generation-stage" tabindex="-1">
        <button
          ref="returnButtonRef"
          class="back-link"
          type="button"
          @click="$emit('return-to-chat')"
        >
          {{ t('meal_plan.return_to_chat') }}
        </button>
        <p class="eyebrow">{{ t('meal_plan.generation.eyebrow') }}</p>
        <h2 id="meal-chat-generation-title">{{ t('meal_plan.generation.title') }}</h2>
        <p id="meal-chat-generation-summary" class="summary">{{ t('meal_plan.generation.summary') }}</p>

        <ul class="generation-steps">
          <li
            v-for="item in steps"
            :key="item.key"
            :class="[
              'generation-step',
              { active: item.active, complete: item.complete }
            ]"
          >
            <span class="step-dot" />
            <span>{{ item.label }}</span>
          </li>
        </ul>
      </div>
    </section>
  </transition>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (event: 'return-to-chat'): void
}>()

const { t } = useI18n()
const shellRef = ref<HTMLElement | null>(null)
const returnButtonRef = ref<HTMLButtonElement | null>(null)

const activeIndex = ref(0)
const timerIds = ref<number[]>([])
let lastFocusedElement: HTMLElement | null = null

const steps = computed(() => {
  const labels = [
    { key: 'review', label: t('meal_plan.generation.steps.review') },
    { key: 'balance', label: t('meal_plan.generation.steps.balance') },
    { key: 'build', label: t('meal_plan.generation.steps.build') }
  ]

  return labels.map((item, index) => ({
    ...item,
    complete: index < activeIndex.value,
    active: index === activeIndex.value
  }))
})

function prefersReducedMotion() {
  return (
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  )
}

function clearTimers() {
  for (const timerId of timerIds.value) {
    window.clearTimeout(timerId)
  }
  timerIds.value = []
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

function startSequence() {
  clearTimers()
  activeIndex.value = prefersReducedMotion() ? 2 : 0

  if (prefersReducedMotion()) {
    return
  }

  timerIds.value.push(
    window.setTimeout(() => {
      activeIndex.value = 1
    }, 340)
  )
  timerIds.value.push(
    window.setTimeout(() => {
      activeIndex.value = 2
    }, 820)
  )
}

watch(
  () => props.visible,
  async (visible) => {
    if (visible) {
      startSequence()
      await activateModalBehavior()
      return
    }
    clearTimers()
    activeIndex.value = 0
    deactivateModalBehavior()
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  deactivateModalBehavior()
  clearTimers()
})
</script>

<style scoped>
.generation-overlay-root {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: grid;
  place-items: center;
  padding: clamp(20px, 4vw, 40px);
}

.generation-overlay-backdrop {
  position: absolute;
  inset: 0;
  background: var(--gradient-overlay-backdrop);
  backdrop-filter: blur(18px);
}

.generation-stage {
  position: relative;
  width: min(720px, calc(100vw - 48px));
  padding: clamp(32px, 5vw, 56px);
  border-radius: 32px;
  background: var(--color-overlay-surface);
  border: 1px solid var(--color-overlay-border);
  box-shadow: var(--shadow-lg);
}

.back-link {
  position: absolute;
  top: 16px;
  right: 16px;
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid var(--color-border-soft);
  background: var(--color-overlay-control);
  color: var(--color-secondary);
  font-weight: 700;
}

.back-link:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--color-primary-dark) 70%, white);
  outline-offset: 2px;
}

.eyebrow {
  margin: 0 0 10px;
  color: var(--color-primary-dark);
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.generation-stage h2 {
  margin: 0;
  color: var(--color-secondary);
  font-size: clamp(2rem, 4vw, 3rem);
  line-height: 1.04;
}

.summary {
  margin: 16px 0 0;
  max-width: 54ch;
  color: var(--color-text-secondary);
  font-size: 1rem;
  line-height: 1.7;
}

.generation-steps {
  display: grid;
  gap: 14px;
  margin: 28px 0 0;
  padding: 0;
  list-style: none;
}

.generation-step {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 18px;
  background: var(--color-overlay-step);
  color: var(--color-text-secondary);
  transition:
    transform var(--overlay-enter-duration) var(--overlay-ease),
    background-color var(--overlay-enter-duration) var(--overlay-ease),
    color var(--overlay-enter-duration) var(--overlay-ease),
    opacity var(--overlay-enter-duration) var(--overlay-ease);
}

.generation-step.active {
  transform: translateX(4px);
  background: var(--color-overlay-step-active);
  color: var(--color-secondary);
}

.generation-step.complete {
  color: var(--color-text-main);
}

.step-dot {
  width: 10px;
  height: 10px;
  flex: none;
  border-radius: 999px;
  background: var(--color-overlay-dot);
  transition:
    transform var(--overlay-enter-duration) var(--overlay-ease),
    opacity var(--overlay-enter-duration) var(--overlay-ease),
    background-color var(--overlay-enter-duration) var(--overlay-ease);
}

.generation-step.active .step-dot {
  transform: scale(1.12);
  opacity: 1;
  background: var(--color-primary-dark);
}

.generation-step.complete .step-dot {
  transform: scale(1);
  opacity: 0.72;
  background: color-mix(in srgb, var(--color-primary-dark) 78%, white);
}

.generation-overlay-enter-active {
  transition: opacity var(--overlay-enter-duration) var(--overlay-ease);
}

.generation-overlay-leave-active {
  transition: opacity var(--overlay-exit-duration) var(--overlay-ease);
}

.generation-overlay-enter-from,
.generation-overlay-leave-to {
  opacity: 0;
}

@media (max-width: 640px) {
  .generation-stage {
    width: min(100vw - 24px, 720px);
    padding: 28px 22px;
    border-radius: 26px;
  }

  .back-link {
    position: static;
    margin-bottom: 18px;
  }

  .generation-stage h2 {
    font-size: 1.8rem;
  }
}
</style>
