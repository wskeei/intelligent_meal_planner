<script setup lang="ts">
import { useDashboardStore } from '@/stores/dashboard'

const store = useDashboardStore()

function severityIcon(severity: string) {
  if (severity === 'critical') return '🔴'
  if (severity === 'warning') return '⚠️'
  return 'ℹ️'
}
</script>

<template>
  <section class="reminders">
    <div class="reminders-header">
      <h2>{{ $t('nutrition.reminders') }}</h2>
      <el-button text size="small" @click="store.reminders.forEach(r => store.dismissReminder(r.id))">
        {{ $t('nutrition.dismiss_all') }}
      </el-button>
    </div>
    <div v-for="r in store.reminders" :key="r.id" class="reminder-item">
      <span>{{ severityIcon(r.severity) }}</span>
      <div class="reminder-content">
        <strong>{{ r.title }}</strong>
        <p>{{ r.message }}</p>
      </div>
      <el-button text size="small" @click="store.dismissReminder(r.id)">×</el-button>
    </div>
  </section>
</template>

<style scoped>
.reminders {
  margin-bottom: 24px;
}
.reminders-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.reminder-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  margin-bottom: 8px;
}
.reminder-content {
  flex: 1;
}
.reminder-content p {
  margin: 4px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
</style>
