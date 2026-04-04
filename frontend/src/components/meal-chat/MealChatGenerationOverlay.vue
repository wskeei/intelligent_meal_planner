<template>
  <transition name="generation-overlay">
    <section
      v-if="visible"
      class="generation-overlay-root"
      aria-live="polite"
      aria-modal="true"
      role="status"
    >
      <div class="generation-overlay-backdrop" />
      <div class="generation-stage">
        <p class="eyebrow">{{ t('meal_plan.generation.eyebrow') }}</p>
        <h2>{{ t('meal_plan.generation.title') }}</h2>
        <p class="summary">{{ t('meal_plan.generation.summary') }}</p>

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
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
  visible: boolean
}>()

const { t } = useI18n()

const activeIndex = ref(0)
const timerIds = ref<number[]>([])

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
  (visible) => {
    if (visible) {
      startSequence()
      return
    }
    clearTimers()
    activeIndex.value = 0
  },
  { immediate: true }
)

onBeforeUnmount(() => {
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
  background:
    radial-gradient(circle at top center, rgba(126, 216, 139, 0.2), transparent 34%),
    linear-gradient(180deg, rgba(245, 247, 242, 0.9), rgba(239, 244, 240, 0.96));
  backdrop-filter: blur(18px);
}

.generation-stage {
  position: relative;
  width: min(720px, calc(100vw - 48px));
  padding: clamp(32px, 5vw, 56px);
  border-radius: 32px;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(47, 143, 81, 0.12);
  box-shadow: 0 28px 80px rgba(21, 48, 40, 0.14);
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
  background: #f7faf8;
  color: var(--color-text-secondary);
  transition:
    transform var(--overlay-enter-duration) var(--overlay-ease),
    background-color var(--overlay-enter-duration) var(--overlay-ease),
    color var(--overlay-enter-duration) var(--overlay-ease),
    opacity var(--overlay-enter-duration) var(--overlay-ease);
}

.generation-step.active {
  transform: translateX(4px);
  background: rgba(126, 216, 139, 0.18);
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
  background: rgba(47, 143, 81, 0.3);
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

  .generation-stage h2 {
    font-size: 1.8rem;
  }
}
</style>
