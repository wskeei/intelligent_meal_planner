<template>
  <div class="shopping-page">
    <div class="page-header">
      <h1>Smart Shopping List</h1>
      <p class="subtitle">Ingredients gathered from your meal plans.</p>
    </div>

    <div class="shopping-container">
      <!-- Add New Item -->
      <el-card class="add-card" shadow="sm">
        <div class="input-group">
          <el-input 
            v-model="newItemName" 
            placeholder="Add new item (e.g., 1L Milk)" 
            size="large"
            @keyup.enter="handleAddItem"
          >
            <template #prefix>
              <el-icon><Plus /></el-icon>
            </template>
          </el-input>
          <el-button type="primary" size="large" @click="handleAddItem" :disabled="!newItemName.trim()">
            Add Item
          </el-button>
        </div>
      </el-card>

      <!-- List -->
      <div v-if="items.length > 0" class="list-area">
        <div class="options-bar">
          <span>{{ items.length }} Items ({{ checkedCount }} bought)</span>
          <div class="actions">
            <el-button link type="danger" @click="shoppingStore.clearChecked" v-if="checkedCount > 0">
              Clear Bought
            </el-button>
            <el-button link type="danger" @click="shoppingStore.clearAll">
              Clear All
            </el-button>
          </div>
        </div>

        <transition-group name="list" tag="div" class="item-list">
          <div 
            v-for="item in items" 
            :key="item.id" 
            class="shopping-item" 
            :class="{ 'is-checked': item.checked }"
          >
            <div class="checkbox" @click="toggleItem(item.id)">
               <div class="check-circle">
                 <el-icon v-if="item.checked"><Check /></el-icon>
               </div>
            </div>
            
            <div class="item-content">
              <span class="item-name">{{ item.name }}</span>
              <span class="item-amount" v-if="item.amount && item.amount !== '1'">x {{ item.amount }}</span>
            </div>

            <el-button class="delete-btn" circle text @click="removeItem(item.id)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </transition-group>
      </div>

      <!-- Empty State -->
      <div v-else class="empty-state">
        <el-icon :size="64" color="#e2e8f0"><ShoppingCart /></el-icon>
        <h3>Your list is empty</h3>
        <p>Add items manually or generate from a meal plan.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useShoppingStore } from '@/stores/shopping'
import { storeToRefs } from 'pinia'
import { Plus, Check, Delete, ShoppingCart } from '@element-plus/icons-vue'

const shoppingStore = useShoppingStore()
const { items } = storeToRefs(shoppingStore)

const newItemName = ref('')

const checkedCount = computed(() => items.value.filter(i => i.checked).length)

const handleAddItem = () => {
  if (newItemName.value.trim()) {
    shoppingStore.addItem(newItemName.value.trim())
    newItemName.value = ''
  }
}

const toggleItem = (id: string) => shoppingStore.toggleItem(id)
const removeItem = (id: string) => shoppingStore.removeItem(id)
</script>

<style scoped>
.page-header {
  margin-bottom: 24px;
  text-align: center;
}

.page-header h1 {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-secondary);
}

.shopping-container {
  max-width: 600px;
  margin: 0 auto;
}

.add-card {
  margin-bottom: 24px;
}

.input-group {
  display: flex;
  gap: 12px;
}

.options-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  margin-bottom: 12px;
  padding: 0 4px;
}

.shopping-item {
  display: flex;
  align-items: center;
  background: white;
  padding: 12px 16px;
  border-radius: 12px;
  margin-bottom: 8px;
  box-shadow: var(--shadow-sm);
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.shopping-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.shopping-item.is-checked {
  background: #f8fafc;
  opacity: 0.8;
}

.shopping-item.is-checked .item-name {
  text-decoration: line-through;
  color: var(--color-text-light);
}

.checkbox {
  cursor: pointer;
  margin-right: 16px;
}

.check-circle {
  width: 24px;
  height: 24px;
  border: 2px solid #cbd5e1;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  transition: all 0.2s;
}

.shopping-item.is-checked .check-circle {
  background-color: var(--color-primary);
  border-color: var(--color-primary);
}

.item-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.item-name {
  font-weight: 500;
  font-size: 1.1rem;
}

.item-amount {
  background: #e2e8f0;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.8rem;
  color: var(--color-text-secondary);
}

.delete-btn {
  opacity: 0;
  transition: opacity 0.2s;
}

.shopping-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  color: var(--color-accent);
  background: #fee2e2;
}

.empty-state {
  text-align: center;
  padding: 60px 0;
  color: var(--color-text-light);
}

.empty-state h3 {
  margin-top: 16px;
  color: var(--color-text-secondary);
  font-size: 1.25rem;
}

/* List Transitions */
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}
</style>
