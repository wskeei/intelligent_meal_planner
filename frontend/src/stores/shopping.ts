import { defineStore } from 'pinia'
import { ref } from 'vue'

import { shoppingListApi, type ShoppingList, type ShoppingListSummary } from '@/api'

export const useShoppingStore = defineStore('shopping', () => {
  const lists = ref<ShoppingListSummary[]>([])
  const activeList = ref<ShoppingList | null>(null)
  const loading = ref(false)
  const viewMode = ref<'ingredients' | 'sources'>('ingredients')

  async function loadLists() {
    loading.value = true
    try {
      const { data } = await shoppingListApi.list()
      lists.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function openList(id: number) {
    loading.value = true
    try {
      const { data } = await shoppingListApi.getById(id)
      activeList.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function syncAfterMutation(nextList: ShoppingList) {
    activeList.value = nextList
    await loadLists()
    return nextList
  }

  async function generateFromWeeklyPlan(weeklyPlanId: number, name = '') {
    const { data } = await shoppingListApi.generate({
      weekly_plan_id: weeklyPlanId,
      name: name || undefined
    })
    return syncAfterMutation(data)
  }

  async function addItem(
    listId: number,
    payload: { ingredient_name: string; display_amount?: string; category?: string }
  ) {
    const { data } = await shoppingListApi.addItem(listId, payload)
    return syncAfterMutation(data)
  }

  async function toggleItem(itemId: number, checked: boolean) {
    if (!activeList.value) return null
    const { data } = await shoppingListApi.updateItem(activeList.value.id, itemId, { checked })
    return syncAfterMutation(data)
  }

  async function updateItem(
    itemId: number,
    payload: { checked?: boolean; display_amount?: string; category?: string }
  ) {
    if (!activeList.value) return null
    const { data } = await shoppingListApi.updateItem(activeList.value.id, itemId, payload)
    return syncAfterMutation(data)
  }

  async function deleteItem(itemId: number) {
    if (!activeList.value) return null
    const { data } = await shoppingListApi.deleteItem(activeList.value.id, itemId)
    return syncAfterMutation(data)
  }

  return {
    lists,
    activeList,
    loading,
    viewMode,
    loadLists,
    openList,
    generateFromWeeklyPlan,
    addItem,
    toggleItem,
    updateItem,
    deleteItem
  }
})
