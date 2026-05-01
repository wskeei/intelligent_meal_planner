<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { dashboardApi, type InsightResponse } from '@/api'

const insight = ref<InsightResponse | null>(null)
const loading = ref(false)

async function loadInsight() {
  loading.value = true
  try {
    const { data } = await dashboardApi.getInsights()
    insight.value = data
  } finally {
    loading.value = false
  }
}

onMounted(loadInsight)
</script>

<template>
  <section class="insight-panel">
    <h2>{{ $t('nutrition.ai_insight') }}</h2>
    <div v-if="loading" class="loading">{{ $t('common.loading') }}</div>
    <p v-else-if="insight" class="insight-text">{{ insight.insight }}</p>
    <el-button text @click="loadInsight">{{ $t('nutrition.refresh_insight') }}</el-button>
  </section>
</template>

<style scoped>
.insight-panel {
  margin-top: 24px;
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}
.insight-text {
  color: var(--el-text-color-regular);
  line-height: 1.6;
}
.loading {
  color: var(--el-text-color-secondary);
}
</style>
