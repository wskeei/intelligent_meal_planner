import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  dashboardApi,
  intakeApi,
  type DailyDashboard,
  type WeeklyDashboard,
  type Reminder,
  type IntakeRecord,
  type TrendPoint,
  type WeightLog,
  type InsightResponse
} from '@/api'

export const useDashboardStore = defineStore('dashboard', () => {
  const today = new Date().toISOString().slice(0, 10)

  const daily = ref<DailyDashboard | null>(null)
  const weekly = ref<WeeklyDashboard | null>(null)
  const reminders = ref<Reminder[]>([])
  const trends = ref<TrendPoint[]>([])
  const weightHistory = ref<WeightLog[]>([])
  const insight = ref<InsightResponse | null>(null)
  const todayRecords = ref<IntakeRecord[]>([])
  const loading = ref(false)

  const unreadCount = computed(() => reminders.value.filter((r) => !r.is_read).length)

  async function loadDaily(date?: string) {
    loading.value = true
    try {
      const { data } = await dashboardApi.getDaily(date || today)
      daily.value = data
    } finally {
      loading.value = false
    }
  }

  async function loadWeekly() {
    const { data } = await dashboardApi.getWeekly()
    weekly.value = data
  }

  async function loadReminders() {
    const { data } = await dashboardApi.getReminders()
    reminders.value = data
  }

  async function loadTodayRecords() {
    const { data } = await intakeApi.getDaily(today)
    todayRecords.value = data.records
  }

  async function loadTrends(months = 3) {
    const { data } = await dashboardApi.getTrends(months)
    trends.value = data
  }

  async function loadInsight() {
    const { data } = await dashboardApi.getInsights()
    insight.value = data
  }

  async function loadWeight() {
    const { data } = await dashboardApi.getWeight()
    weightHistory.value = data
  }

  async function dismissReminder(id: number) {
    await dashboardApi.dismissReminder(id)
    reminders.value = reminders.value.filter((r) => r.id !== id)
  }

  async function quickLog(recipeId: number, portionSize = 1.0) {
    await intakeApi.quickLog({ date: today, recipe_id: recipeId, portion_size: portionSize })
    await Promise.all([loadDaily(), loadTodayRecords()])
  }

  async function logWeightEntry(weight: number) {
    await dashboardApi.logWeight({ date: today, weight })
    await loadWeight()
  }

  async function loadAll() {
    await Promise.all([
      loadDaily(),
      loadWeekly(),
      loadReminders(),
      loadTodayRecords(),
      loadInsight(),
    ])
  }

  return {
    daily,
    weekly,
    reminders,
    trends,
    weightHistory,
    insight,
    todayRecords,
    loading,
    unreadCount,
    loadDaily,
    loadWeekly,
    loadReminders,
    loadTodayRecords,
    loadTrends,
    loadInsight,
    loadWeight,
    dismissReminder,
    quickLog,
    logWeightEntry,
    loadAll
  }
})
