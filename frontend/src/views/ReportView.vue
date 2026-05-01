<script setup lang="ts">
import { ref } from 'vue'
import { dashboardApi, type ReportResponse } from '@/api'
import InsightPanel from '@/components/reports/InsightPanel.vue'

const reportType = ref('weekly')
const report = ref<ReportResponse | null>(null)
const loading = ref(false)

async function generate() {
  loading.value = true
  try {
    const { data } = await dashboardApi.generateReport({ report_type: reportType.value })
    report.value = data
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="report-page">
    <h1>{{ $t('nutrition.reports') }}</h1>

    <div class="report-controls">
      <el-radio-group v-model="reportType">
        <el-radio-button value="weekly">{{ $t('nutrition.weekly_report') }}</el-radio-button>
        <el-radio-button value="monthly">{{ $t('nutrition.monthly_report') }}</el-radio-button>
      </el-radio-group>
      <el-button type="primary" :loading="loading" @click="generate">
        {{ $t('nutrition.generate_report') }}
      </el-button>
    </div>

    <div v-if="report" class="report-preview" v-html="report.html" />

    <InsightPanel />
  </div>
</template>

<style scoped>
.report-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px 16px;
}
.report-controls {
  display: flex;
  gap: 16px;
  align-items: center;
  margin-bottom: 24px;
}
.report-preview {
  padding: 24px;
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
}
</style>
