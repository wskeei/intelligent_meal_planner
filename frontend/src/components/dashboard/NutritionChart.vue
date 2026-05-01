<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useDashboardStore } from '@/stores/dashboard'

use([LineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const store = useDashboardStore()
const metric = ref<'calories' | 'protein' | 'carbs' | 'fat'>('calories')

onMounted(() => store.loadWeekly())

const chartOption = computed(() => {
  if (!store.weekly) return {}
  const days = store.weekly.days
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['Actual', 'Target'] },
    xAxis: {
      type: 'category',
      data: days.map((d) => d.date.slice(5)),
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: 'Actual',
        type: 'line',
        data: days.map((d) => d[metric.value]),
        smooth: true,
      },
      {
        name: 'Target',
        type: 'line',
        data: days.map(() => store.daily?.target[metric.value] ?? 0),
        lineStyle: { type: 'dashed' },
      },
    ],
  }
})
</script>

<template>
  <div class="chart-section">
    <div class="chart-header">
      <h2>{{ $t('nutrition.weekly_trend') }}</h2>
      <el-select v-model="metric" size="small" style="width: 120px">
        <el-option label="Calories" value="calories" />
        <el-option label="Protein" value="protein" />
        <el-option label="Carbs" value="carbs" />
        <el-option label="Fat" value="fat" />
      </el-select>
    </div>
    <VChart :option="chartOption" style="height: 300px" autoresize />
  </div>
</template>

<style scoped>
.chart-section {
  margin-bottom: 24px;
}
.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
</style>
