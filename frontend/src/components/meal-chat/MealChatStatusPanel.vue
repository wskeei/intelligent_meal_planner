<template>
  <section class="status-panel" :class="{ expanded }">
    <div class="status-header">
      <div class="status-copy">
        <p class="eyebrow">{{ eyebrow }}</p>
        <div class="heading-row">
          <h2>{{ title }}</h2>
          <span class="state-pill">{{ condensedLabel }}</span>
        </div>
        <p class="summary">{{ summary }}</p>
      </div>
      <button class="toggle-button" type="button" @click="$emit('toggle')">
        {{ expanded ? collapseLabel : expandLabel }}
      </button>
    </div>

    <div v-if="!expanded && $slots['primary-action']" class="status-primary-action">
      <slot name="primary-action" />
    </div>

    <div v-show="expanded" class="status-expanded">
      <div class="status-block next-step compact">
        <div class="block-title">{{ nextTitle }}</div>
        <p>{{ nextAction }}</p>
        <p v-if="assistantHint" class="assistant-hint">{{ assistantHint }}</p>
      </div>

      <div v-if="$slots.actions" class="status-actions">
        <slot name="actions" />
      </div>

      <div v-if="knownItems.length" class="status-block">
        <div class="block-title">{{ knownTitle }}</div>
        <div class="chips">
          <span v-for="item in knownItems" :key="`${item.label}-${item.value}`" class="chip">
            <strong>{{ item.label }}</strong>
            <span>{{ item.value }}</span>
          </span>
        </div>
      </div>

      <div class="status-block">
        <div class="block-title">{{ missingTitle }}</div>
        <div v-if="missingItems.length" class="missing-list">
          <article v-for="item in missingItems" :key="item.label" class="missing-item">
            <strong>{{ item.label }}</strong>
            <p>{{ item.hint }}</p>
          </article>
        </div>
        <p v-else class="complete-note">{{ completedCopy }}</p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
interface StatusItem {
  label: string
  value: string
}

interface MissingItem {
  label: string
  hint: string
}

defineProps<{
  eyebrow: string
  title: string
  summary: string
  condensedLabel: string
  expanded: boolean
  expandLabel: string
  collapseLabel: string
  knownTitle: string
  missingTitle: string
  nextTitle: string
  completedCopy: string
  nextAction: string
  assistantHint?: string
  knownItems: StatusItem[]
  missingItems: MissingItem[]
}>()

defineEmits<{
  (event: 'toggle'): void
}>()
</script>

<style scoped>
.status-panel {
  display: grid;
  gap: 12px;
  padding: 14px;
  border-radius: 20px;
  background: var(--gradient-surface);
  border: 1px solid var(--color-border-soft);
  box-shadow: var(--shadow-sm);
}

.status-panel.expanded {
  gap: 16px;
  padding: 18px;
  border-radius: 24px;
  background: var(--gradient-emphasis);
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-md);
}

.status-header,
.heading-row,
.status-actions {
  display: flex;
}

.status-header {
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.status-copy {
  display: grid;
  gap: 8px;
}

.heading-row {
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.status-header h2 {
  margin: 0;
  font-size: 1.02rem;
}

.state-pill {
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--color-accent-pill-bg);
  color: var(--color-accent-pill-text);
  font-size: 0.75rem;
  font-weight: 700;
}

.eyebrow {
  margin: 0;
  color: var(--color-primary-dark);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.summary {
  margin: 0;
  color: var(--color-text-secondary);
  line-height: 1.45;
  font-size: 0.88rem;
}

.toggle-button {
  min-height: 44px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid transparent;
  background: color-mix(in srgb, var(--color-border-soft) 56%, transparent);
  color: var(--color-secondary);
  font-weight: 700;
  transition:
    background 180ms ease,
    transform 180ms ease;
}

.toggle-button:hover {
  background: color-mix(in srgb, var(--color-accent-soft) 72%, transparent);
  transform: translateY(-1px);
}

.toggle-button:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--color-primary-dark) 70%, white);
  outline-offset: 2px;
}

.status-primary-action {
  display: flex;
}

.status-expanded {
  display: grid;
  gap: 14px;
}

.status-block {
  display: grid;
  gap: 8px;
}

.status-block.compact {
  padding: 12px 14px;
  border-radius: 18px;
  background: color-mix(in srgb, var(--color-surface-raised) 12%, transparent);
}

.block-title {
  color: var(--color-text-emphasis);
  font-size: 0.74rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.next-step p,
.assistant-hint,
.complete-note {
  margin: 0;
  color: var(--color-text-emphasis-muted);
  line-height: 1.5;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 9px 12px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-surface-raised) 14%, transparent);
  color: var(--color-text-emphasis);
  font-size: 0.86rem;
}

.chip strong,
.missing-item strong {
  font-size: 0.86rem;
}

.missing-list {
  display: grid;
  gap: 8px;
}

.missing-item {
  padding: 10px 12px;
  border-radius: 16px;
  background: color-mix(in srgb, var(--color-surface-raised) 10%, transparent);
}

.missing-item p {
  margin: 4px 0 0;
  color: var(--color-text-emphasis-muted);
  line-height: 1.5;
}

.assistant-hint {
  font-size: 0.88rem;
}

.status-actions {
  flex-wrap: wrap;
  gap: 10px;
}

.status-panel.expanded .status-header h2,
.status-panel.expanded .state-pill,
.status-panel.expanded .summary {
  color: var(--color-text-emphasis);
}

.status-panel.expanded .state-pill {
  background: color-mix(in srgb, var(--color-accent-soft) 76%, transparent);
}

.status-panel.expanded .eyebrow {
  color: var(--color-text-emphasis-muted);
}

.status-panel.expanded .toggle-button {
  background: color-mix(in srgb, var(--color-surface-raised) 12%, transparent);
  color: var(--color-text-emphasis);
}

.status-primary-action :deep(.el-button) {
  min-height: 44px;
}

@media (max-width: 640px) {
  .status-header,
  .status-actions,
  .status-primary-action {
    flex-direction: column;
  }

  .toggle-button {
    width: 100%;
  }
}
</style>
