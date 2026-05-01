<script setup lang="ts">
import { onMounted } from 'vue'
import { useDashboardStore } from '@/stores/dashboard'
import DailySummary from '@/components/dashboard/DailySummary.vue'
import NutritionChart from '@/components/dashboard/NutritionChart.vue'
import ReminderList from '@/components/dashboard/ReminderList.vue'

const store = useDashboardStore()

onMounted(() => store.loadAll())
</script>

<template>
  <div class="dashboard-page">
    <h1>{{ $t('nutrition.dashboard_title') }}</h1>

    <DailySummary />

    <ReminderList v-if="store.reminders.length" />

    <NutritionChart />

    <section v-if="store.insight" class="insight-section">
      <h2>{{ $t('nutrition.ai_insight') }}</h2>
      <p class="insight-text">{{ store.insight.insight }}</p>
    </section>

    <div class="dashboard-actions">
      <el-button type="primary" tag="router-link" to="/intake">
        {{ $t('nutrition.log_meal') }}
      </el-button>
      <el-button tag="router-link" to="/reports">
        {{ $t('nutrition.view_reports') }}
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.dashboard-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px 16px;
}
.insight-section {
  margin-top: 24px;
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}
.insight-text {
  color: var(--el-text-color-regular);
  line-height: 1.6;
}
.dashboard-actions {
  margin-top: 24px;
  display: flex;
  gap: 12px;
}
</style>
