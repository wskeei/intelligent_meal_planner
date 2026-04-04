import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

import type { MealPlan } from '@/api'

export interface ShoppingItem {
  id: string
  name: string
  amount: string
  checked: boolean
  category: string
  source: 'manual' | 'meal-plan'
}

export const useShoppingStore = defineStore('shopping', () => {
  const items = ref<ShoppingItem[]>([])

  if (localStorage.getItem('shoppingList')) {
    try {
      items.value = JSON.parse(localStorage.getItem('shoppingList')!)
    } catch (error) {
      console.error('Failed to load shopping list', error)
    }
  }

  watch(
    items,
    (newVal) => {
      localStorage.setItem('shoppingList', JSON.stringify(newVal))
    },
    { deep: true }
  )

  function buildId() {
    return `${Date.now()}-${Math.random().toString().slice(2)}`
  }

  function upsertItem(payload: Omit<ShoppingItem, 'id' | 'checked'>) {
    const existing = items.value.find(
      (item) => item.name.trim().toLowerCase() === payload.name.trim().toLowerCase()
    )

    if (existing) {
      existing.amount = payload.amount || existing.amount
      existing.category = payload.category || existing.category
      existing.source = payload.source
      return
    }

    items.value.push({
      id: buildId(),
      checked: false,
      ...payload
    })
  }

  function addItem(name: string, amount: string = '', category: string = 'manual') {
    upsertItem({
      name,
      amount,
      category,
      source: 'manual'
    })
  }

  function addItemsFromMealPlan(mealPlan: MealPlan) {
    for (const meal of mealPlan.meals) {
      upsertItem({
        name: meal.recipe_name,
        amount: '',
        category: meal.meal_type,
        source: 'meal-plan'
      })
    }
  }

  function toggleItem(id: string) {
    const item = items.value.find((entry) => entry.id === id)
    if (item) {
      item.checked = !item.checked
    }
  }

  function removeItem(id: string) {
    items.value = items.value.filter((entry) => entry.id !== id)
  }

  function clearChecked() {
    items.value = items.value.filter((entry) => !entry.checked)
  }

  function clearAll() {
    items.value = []
  }

  return {
    items,
    addItem,
    addItemsFromMealPlan,
    toggleItem,
    removeItem,
    clearChecked,
    clearAll
  }
})
