import { defineStore } from 'pinia'
import { ref } from 'vue'

import {
  weeklyPlanApi,
  type WeeklyPlan,
  type WeeklyPlanAttachPayload,
  type WeeklyPlanSummary
} from '@/api'

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

  return {
    plans,
    activePlan,
    loading,
    loadPlans,
    openPlan,
    createPlan,
    attachDay,
    removeDay
  }
})
