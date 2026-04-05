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

    <div class="status-block next-step compact">
      <div class="block-title">{{ nextTitle }}</div>
      <p>{{ nextAction }}</p>
      <p v-if="assistantHint" class="assistant-hint">{{ assistantHint }}</p>
    </div>

    <div v-if="$slots.actions" class="status-actions">
      <slot name="actions" />
    </div>

    <div v-show="expanded" class="status-details">
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
  gap: 16px;
  padding: 18px;
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(15, 37, 27, 0.98), rgba(20, 46, 34, 0.96));
  box-shadow: 0 18px 34px rgba(16, 37, 27, 0.18);
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
  font-size: 1.16rem;
}

.state-pill {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(214, 247, 223, 0.14);
  color: #e6fff0;
  font-size: 0.75rem;
  font-weight: 700;
}

.eyebrow {
  margin: 0;
  color: rgba(239, 255, 245, 0.7);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.summary {
  margin: 0;
  color: rgba(239, 255, 245, 0.82);
  line-height: 1.55;
  font-size: 0.94rem;
}

.toggle-button {
  min-height: 40px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: #effff5;
  font-weight: 700;
  transition:
    background 180ms ease,
    transform 180ms ease;
}

.toggle-button:hover {
  background: rgba(255, 255, 255, 0.14);
  transform: translateY(-1px);
}

.status-block {
  display: grid;
  gap: 8px;
}

.status-block.compact {
  padding: 12px 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.07);
}

.block-title {
  color: #d6f7df;
  font-size: 0.74rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.next-step p,
.assistant-hint,
.complete-note {
  margin: 0;
  color: rgba(239, 255, 245, 0.82);
  line-height: 1.5;
}

.status-details {
  display: grid;
  gap: 14px;
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
  background: rgba(255, 255, 255, 0.09);
  color: #effff5;
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
  background: rgba(255, 255, 255, 0.07);
}

.missing-item p {
  margin: 4px 0 0;
  color: rgba(239, 255, 245, 0.76);
  line-height: 1.5;
}

.assistant-hint {
  font-size: 0.88rem;
}

.status-actions {
  flex-wrap: wrap;
  gap: 10px;
}

@media (max-width: 640px) {
  .status-header,
  .status-actions {
    flex-direction: column;
  }

  .toggle-button {
    width: 100%;
  }
}
</style>
