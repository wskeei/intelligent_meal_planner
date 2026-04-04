<template>
  <div class="shopping-page">
    <header class="page-header">
      <h1>{{ $t('shopping.title') }}</h1>
      <p class="subtitle">{{ $t('shopping.subtitle') }}</p>
    </header>

    <div class="shopping-container">
      <el-card class="add-card" shadow="never">
        <div class="input-group">
          <el-input
            v-model="newItemName"
            :placeholder="$t('shopping.add_placeholder')"
            size="large"
            @keyup.enter="handleAddItem"
          >
            <template #prefix>
              <el-icon><Plus /></el-icon>
            </template>
          </el-input>
          <el-button type="primary" size="large" @click="handleAddItem" :disabled="!newItemName.trim()">
            {{ $t('shopping.add_btn') }}
          </el-button>
        </div>
      </el-card>

      <div v-if="items.length" class="list-area">
        <div class="options-bar">
          <span>{{ $t('shopping.items_count', { total: items.length, checked: checkedCount }) }}</span>
          <div class="actions">
            <el-button v-if="checkedCount > 0" text type="danger" @click="shoppingStore.clearChecked">
              {{ $t('shopping.clear_bought') }}
            </el-button>
            <el-button text type="danger" @click="shoppingStore.clearAll">
              {{ $t('shopping.clear_all') }}
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
            <button class="check-button" type="button" @click="toggleItem(item.id)">
              <span class="check-circle">
                <el-icon v-if="item.checked"><Check /></el-icon>
              </span>
            </button>

            <div class="item-content">
              <div class="item-copy">
                <span class="item-name">{{ item.name }}</span>
                <span v-if="item.amount" class="item-amount">{{ item.amount }}</span>
              </div>
              <span class="source-pill" :class="item.source">
                {{ item.source === 'meal-plan' ? $t('shopping.from_plan') : $t('shopping.manual_item') }}
              </span>
            </div>

            <el-button class="delete-btn" circle text @click="removeItem(item.id)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </transition-group>
      </div>

      <AppEmptyState
        v-else
        :icon="ShoppingCart"
        :eyebrow="$t('shopping.empty_eyebrow')"
        :title="$t('shopping.empty_title')"
        :description="$t('shopping.empty_desc')"
      >
        <template #actions>
          <el-button type="primary" @click="$router.push('/meal-plan')">
            {{ $t('shopping.go_plan') }}
          </el-button>
        </template>
      </AppEmptyState>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { Check, Delete, Plus, ShoppingCart } from '@element-plus/icons-vue'

import AppEmptyState from '@/components/common/AppEmptyState.vue'
import { useShoppingStore } from '@/stores/shopping'

const shoppingStore = useShoppingStore()
const { items } = storeToRefs(shoppingStore)

const newItemName = ref('')

const checkedCount = computed(() => items.value.filter((item) => item.checked).length)

function handleAddItem() {
  const name = newItemName.value.trim()
  if (!name) return

  shoppingStore.addItem(name)
  newItemName.value = ''
}

function toggleItem(id: string) {
  shoppingStore.toggleItem(id)
}

function removeItem(id: string) {
  shoppingStore.removeItem(id)
}
</script>

<style scoped>
.shopping-page {
  display: grid;
  gap: 24px;
}

.page-header h1 {
  margin: 0;
  color: var(--color-secondary);
  font-size: clamp(2rem, 4vw, 2.6rem);
}

.subtitle {
  margin: 8px 0 0;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.shopping-container {
  display: grid;
  gap: 18px;
  max-width: 760px;
}

.add-card {
  border-radius: 22px;
}

.input-group,
.options-bar,
.actions,
.shopping-item,
.item-copy {
  display: flex;
  gap: 12px;
}

.input-group,
.options-bar,
.shopping-item {
  align-items: center;
}

.input-group {
  flex-wrap: wrap;
}

.input-group :deep(.el-input) {
  flex: 1;
  min-width: 220px;
}

.options-bar {
  justify-content: space-between;
  flex-wrap: wrap;
  color: var(--color-text-secondary);
}

.item-list {
  display: grid;
  gap: 10px;
}

.shopping-item {
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
}

.shopping-item.is-checked {
  background: #f7faf8;
}

.check-button,
.delete-btn {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  padding: 0;
  border-radius: 14px;
}

.check-button {
  background: transparent;
}

.check-circle {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border: 2px solid #cbd5e1;
  border-radius: 50%;
  color: white;
}

.shopping-item.is-checked .check-circle {
  background: var(--color-primary-dark);
  border-color: var(--color-primary-dark);
}

.item-content {
  display: grid;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.item-copy {
  flex-wrap: wrap;
  align-items: center;
}

.item-name {
  font-weight: 700;
  color: var(--color-secondary);
  overflow-wrap: break-word;
}

.shopping-item.is-checked .item-name {
  text-decoration: line-through;
  color: var(--color-text-light);
}

.item-amount {
  color: var(--color-text-secondary);
  font-size: 0.88rem;
}

.source-pill {
  width: fit-content;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 0.76rem;
  font-weight: 700;
}

.source-pill.manual {
  background: rgba(15, 23, 42, 0.07);
  color: var(--color-text-secondary);
}

.source-pill.meal-plan {
  background: rgba(34, 197, 94, 0.14);
  color: var(--color-primary-dark);
}

.delete-btn {
  color: var(--color-text-secondary);
}

.delete-btn:hover {
  color: #b91c1c;
  background: rgba(248, 113, 113, 0.12);
}

.list-enter-active,
.list-leave-active {
  transition: all 0.24s ease;
}

.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

@media (max-width: 640px) {
  .shopping-item {
    align-items: flex-start;
  }

  .actions {
    width: 100%;
  }

  .actions :deep(.el-button) {
    min-height: 44px;
  }
}
</style>
