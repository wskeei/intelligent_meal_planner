import { defineStore } from 'pinia'
import { ref } from 'vue'

import {
  weeklyPlanApi,
  type WeeklyPlan,
  type WeeklyPlanAttachPayload,
  type WeeklyPlanSummary
} from '@/api'
import { useDashboardStore } from './dashboard'

export const useWeeklyPlanStore = defineStore('weekly-plan', () => {
  const plans = ref<WeeklyPlanSummary[]>([])
  const activePlan = ref<WeeklyPlan | null>(null)
  const loading = ref(false)

  async function loadPlans() {
    loading.value = true
    try {
      const { data } = await weeklyPlanApi.list()
      plans.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function openPlan(id: number) {
    loading.value = true
    try {
      const { data } = await weeklyPlanApi.getById(id)
      activePlan.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function syncAfterMutation(nextPlan: WeeklyPlan) {
    activePlan.value = nextPlan
    await loadPlans()
    return nextPlan
  }

  async function createPlan(name: string, notes = '') {
    const { data } = await weeklyPlanApi.create({
      name,
      notes: notes || undefined
    })
    return syncAfterMutation(data)
  }

  async function attachDay(planId: number, payload: WeeklyPlanAttachPayload) {
    const { data } = await weeklyPlanApi.attachDay(planId, payload)
    return syncAfterMutation(data)
  }

  async function removeDay(planId: number, dayId: number) {
    const { data } = await weeklyPlanApi.removeDay(planId, dayId)
    return syncAfterMutation(data)
  }

  async function updatePlan(id: number, payload: { name?: string; notes?: string }) {
    const { data } = await weeklyPlanApi.update(id, payload)
    return syncAfterMutation(data)
  }

  async function deletePlan(id: number) {
    await weeklyPlanApi.delete(id)
    if (activePlan.value?.id === id) {
      activePlan.value = null
    }
    await loadPlans()
  }

  async function confirmDay(planId: number, date: string) {
    const { data } = await weeklyPlanApi.confirmDay(planId, date)
    if (activePlan.value?.id === planId) {
      const day = activePlan.value.days.find((d) => d.plan_date === date)
      if (day) {
        day.completed = true
        day.completed_at = new Date().toISOString()
      }
    }
    const dashboard = useDashboardStore()
    await dashboard.loadAll()
    return data
  }

  async function cancelConfirm(planId: number, date: string) {
    await weeklyPlanApi.cancelConfirm(planId, date)
    if (activePlan.value?.id === planId) {
      const day = activePlan.value.days.find((d) => d.plan_date === date)
      if (day) {
        day.completed = false
        day.completed_at = undefined
      }
    }
    const dashboard = useDashboardStore()
    await dashboard.loadAll()
  }

  return {
    plans,
    activePlan,
    loading,
    loadPlans,
    openPlan,
    createPlan,
    updatePlan,
    deletePlan,
    attachDay,
    removeDay,
    confirmDay,
    cancelConfirm
  }
})
