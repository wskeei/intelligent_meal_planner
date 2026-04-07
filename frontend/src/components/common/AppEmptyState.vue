<template>
  <div class="empty-state">
    <div v-if="icon" class="empty-icon">
      <el-icon :size="32">
        <component :is="icon" />
      </el-icon>
    </div>
    <p v-if="eyebrow" class="empty-eyebrow">{{ eyebrow }}</p>
    <h3>{{ title }}</h3>
    <p class="empty-description">{{ description }}</p>
    <div v-if="$slots.actions" class="empty-actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Component } from 'vue'

defineProps<{
  title: string
  description: string
  eyebrow?: string
  icon?: Component
}>()
</script>

<style scoped>
.empty-state {
  display: grid;
  justify-items: start;
  gap: 10px;
  padding: 28px;
  border-radius: 20px;
  background: var(--gradient-surface);
  border: 1px solid var(--color-border-soft);
  box-shadow: var(--shadow-sm);
  min-width: 0;
}

.empty-icon {
  display: grid;
  place-items: center;
  width: 52px;
  height: 52px;
  border-radius: 16px;
  background: var(--color-accent-soft);
  color: var(--color-primary-dark);
}

.empty-eyebrow {
  margin: 0;
  color: var(--color-primary-dark);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  overflow-wrap: anywhere;
}

h3 {
  margin: 0;
  color: var(--color-secondary);
  font-size: 1.15rem;
  overflow-wrap: anywhere;
}

.empty-description {
  margin: 0;
  color: var(--color-text-secondary);
  line-height: 1.6;
  overflow-wrap: anywhere;
}

.empty-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 6px;
}

@media (max-width: 640px) {
  .empty-actions {
    width: 100%;
  }

  .empty-actions :deep(.el-button) {
    width: 100%;
    min-height: 44px;
  }
}
</style>
