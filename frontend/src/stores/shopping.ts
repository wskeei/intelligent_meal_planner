import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export interface ShoppingItem {
    id: string
    name: string
    amount: string
    checked: boolean
    category: string
}

export const useShoppingStore = defineStore('shopping', () => {
    const items = ref<ShoppingItem[]>([])

    // Load from LocalStorage
    if (localStorage.getItem('shoppingList')) {
        try {
            items.value = JSON.parse(localStorage.getItem('shoppingList')!)
        } catch (e) {
            console.error('Failed to load shopping list', e)
        }
    }

    // Auto-save
    watch(items, (newVal) => {
        localStorage.setItem('shoppingList', JSON.stringify(newVal))
    }, { deep: true })

    function addItem(name: string, amount: string = '1', category: string = 'Other') {
        // Simple deduplication or merge logic could go here
        items.value.push({
            id: Date.now().toString() + Math.random().toString().slice(2),
            name,
            amount,
            checked: false,
            category
        })
    }

    function toggleItem(id: string) {
        const item = items.value.find(i => i.id === id)
        if (item) {
            item.checked = !item.checked
        }
    }

    function removeItem(id: string) {
        items.value = items.value.filter(i => i.id !== id)
    }

    function clearChecked() {
        items.value = items.value.filter(i => !i.checked)
    }

    function clearAll() {
        items.value = []
    }

    return {
        items,
        addItem,
        toggleItem,
        removeItem,
        clearChecked,
        clearAll
    }
})
