<template>
  <section class="status-panel">
    <div class="status-header">
      <p class="eyebrow">{{ eyebrow }}</p>
      <h2>{{ title }}</h2>
      <p class="summary">{{ summary }}</p>
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

    <div class="status-block next-step">
      <div class="block-title">{{ nextTitle }}</div>
      <p>{{ nextAction }}</p>
      <p v-if="assistantHint" class="assistant-hint">{{ assistantHint }}</p>
    </div>

    <div v-if="$slots.actions" class="status-actions">
      <slot name="actions" />
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
  knownTitle: string
  missingTitle: string
  nextTitle: string
  completedCopy: string
  nextAction: string
  assistantHint?: string
  knownItems: StatusItem[]
  missingItems: MissingItem[]
}>()
</script>

<style scoped>
.status-panel {
  display: grid;
  gap: 18px;
}

.status-header h2 {
  margin: 8px 0 10px;
  font-size: 1.25rem;
}

.eyebrow {
  margin: 0;
  color: rgba(239, 255, 245, 0.7);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.summary,
.next-step p,
.assistant-hint,
.complete-note {
  margin: 0;
  color: rgba(239, 255, 245, 0.82);
  line-height: 1.6;
}

.status-block {
  display: grid;
  gap: 10px;
}

.block-title {
  color: #d6f7df;
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.chip {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.1);
  color: #effff5;
}

.chip strong,
.missing-item strong {
  font-size: 0.86rem;
}

.missing-list {
  display: grid;
  gap: 10px;
}

.missing-item {
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.08);
}

.missing-item p {
  margin: 4px 0 0;
  color: rgba(239, 255, 245, 0.76);
  line-height: 1.5;
}

.assistant-hint {
  font-size: 0.92rem;
}

.status-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
</style>
