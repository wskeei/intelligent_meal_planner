<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDashboardStore } from '@/stores/dashboard'

const { t } = useI18n()
const store = useDashboardStore()

const nutrients = computed(() => {
  if (!store.daily) return []
  const { target, actual } = store.daily
  return [
    { label: t('nutrition.calories'), actual: actual.calories, target: target.calories, unit: 'kcal' },
    { label: t('nutrition.protein_g'), actual: actual.protein, target: target.protein, unit: 'g' },
    { label: t('nutrition.carbs_g'), actual: actual.carbs, target: target.carbs, unit: 'g' },
    { label: t('nutrition.fat_g'), actual: actual.fat, target: target.fat, unit: 'g' },
  ]
})
</script>

<template>
  <div class="daily-summary">
    <div v-for="n in nutrients" :key="n.label" class="nutrient-card">
      <span class="nutrient-label">{{ n.label }}</span>
      <span class="nutrient-value">
        {{ Math.round(n.actual) }}<span class="nutrient-target">/{{ Math.round(n.target) }}{{ n.unit }}</span>
      </span>
      <el-progress
        :percentage="Math.min(100, (n.actual / (n.target || 1)) * 100)"
        :stroke-width="8"
        :show-text="false"
      />
    </div>
  </div>
</template>

<style scoped>
.daily-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}
.nutrient-card {
  padding: 16px;
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
}
.nutrient-label {
  display: block;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}
.nutrient-value {
  font-size: 24px;
  font-weight: 600;
}
.nutrient-target {
  font-size: 14px;
  font-weight: 400;
  color: var(--el-text-color-secondary);
}
</style>
