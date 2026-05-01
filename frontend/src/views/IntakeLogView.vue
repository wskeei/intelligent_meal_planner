<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useDashboardStore } from '@/stores/dashboard'
import QuickLog from '@/components/intake/QuickLog.vue'

const store = useDashboardStore()
const selectedDate = ref(new Date().toISOString().slice(0, 10))

onMounted(() => store.loadTodayRecords())

function onLogged() {
  store.loadTodayRecords()
  store.loadDaily(selectedDate.value)
}
</script>

<template>
  <div class="intake-page">
    <h1>{{ $t('nutrition.intake_log') }}</h1>

    <QuickLog @logged="onLogged" />

    <section class="today-records">
      <h2>{{ $t('nutrition.today_records') }}</h2>
      <div v-if="store.todayRecords.length === 0" class="empty">
        {{ $t('nutrition.no_records') }}
      </div>
      <div v-for="r in store.todayRecords" :key="r.id" class="record-row">
        <div class="record-info">
          <span class="record-meal">{{ r.meal_type }}</span>
          <span class="record-name">{{ r.recipe_name || r.custom_food_name }}</span>
        </div>
        <div class="record-nutrition">
          {{ Math.round(r.actual_calories) }} kcal · {{ Math.round(r.actual_protein) }}g P
        </div>
        <el-rate v-if="r.rating" :model-value="r.rating" disabled size="small" />
      </div>
    </section>
  </div>
</template>

<style scoped>
.intake-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px 16px;
}
.today-records {
  margin-top: 24px;
}
.record-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.record-info {
  display: flex;
  gap: 8px;
}
.record-meal {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  text-transform: capitalize;
}
.record-nutrition {
  font-size: 13px;
  color: var(--el-text-color-regular);
}
.empty {
  padding: 24px;
  text-align: center;
  color: var(--el-text-color-secondary);
}
</style>
