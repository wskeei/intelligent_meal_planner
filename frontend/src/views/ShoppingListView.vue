<template>
  <div class="shopping-page">
    <header class="page-header">
      <div>
        <h1>{{ $t('shopping.title') }}</h1>
        <p class="subtitle">{{ $t('shopping.subtitle') }}</p>
      </div>
      <el-button type="primary" tag="router-link" to="/weekly-plan">
        {{ $t('shopping.go_weekly_plan') }}
      </el-button>
    </header>

    <AppEmptyState
      v-if="!activeList && !loading"
      :icon="ShoppingCart"
      :eyebrow="$t('shopping.empty_eyebrow')"
      :title="$t('shopping.empty_title')"
      :description="$t('shopping.empty_desc')"
    >
      <template #actions>
        <el-button type="primary" tag="router-link" to="/weekly-plan">
          {{ $t('shopping.go_weekly_plan') }}
        </el-button>
      </template>
    </AppEmptyState>

    <template v-else-if="activeList">
      <el-card class="control-card" shadow="never">
        <div class="control-grid">
          <el-select v-model="selectedListId" class="list-select" @change="handleListChange">
            <el-option
              v-for="list in lists"
              :key="list.id"
              :label="list.name"
              :value="list.id"
            />
          </el-select>

          <el-radio-group v-model="viewMode" size="large">
            <el-radio-button label="ingredients">{{ $t('shopping.ingredients_view') }}</el-radio-button>
            <el-radio-button label="sources">{{ $t('shopping.sources_view') }}</el-radio-button>
          </el-radio-group>
        </div>
      </el-card>

      <el-card class="add-card" shadow="never">
        <div class="add-grid">
          <el-input
            v-model="newItemName"
            :placeholder="$t('shopping.add_placeholder')"
            size="large"
            @keyup.enter="handleAddItem"
          />
          <el-input
            v-model="newItemAmount"
            :placeholder="$t('shopping.amount_placeholder')"
            size="large"
            @keyup.enter="handleAddItem"
          />
          <el-button type="primary" size="large" :disabled="!newItemName.trim()" @click="handleAddItem">
            {{ $t('shopping.add_btn') }}
          </el-button>
        </div>
      </el-card>

      <section class="list-area">
        <div class="options-bar">
          <span>{{ $t('shopping.items_count', { total: activeList.items.length, checked: checkedCount }) }}</span>
          <span class="muted-copy">{{ activeList.name }}</span>
        </div>

        <div v-if="viewMode === 'ingredients'" class="item-list">
          <article
            v-for="item in activeList.items"
            :key="item.id"
            class="shopping-item"
            :class="{ 'is-checked': item.checked }"
          >
            <button
              class="check-button"
              type="button"
              :aria-label="$t('shopping.actions.toggle_item', { item: item.ingredient_name })"
              @click="toggleItem(item.id, !item.checked)"
            >
              <span class="check-circle">
                <el-icon v-if="item.checked"><Check /></el-icon>
              </span>
            </button>

            <div class="item-content">
              <div class="item-copy">
                <span class="item-name">{{ item.ingredient_name }}</span>
                <span v-if="item.display_amount" class="item-amount">{{ item.display_amount }}</span>
              </div>
              <div class="item-meta">
                <span class="source-pill" :class="item.source_kind">
                  {{
                    item.source_kind === 'manual'
                      ? $t('shopping.manual_item')
                      : $t('shopping.from_plan')
                  }}
                </span>
                <span class="trace-count">
                  {{ $t('shopping.source_count', { count: item.sources.length }) }}
                </span>
              </div>
            </div>

            <el-button
              class="delete-btn"
              circle
              text
              :aria-label="$t('shopping.actions.remove_item', { item: item.ingredient_name })"
              @click="removeItem(item.id)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </article>
        </div>

        <div v-else class="source-list">
          <article v-for="item in activeList.items" :key="item.id" class="source-card">
            <div class="source-card-head">
              <div>
                <h3>{{ item.ingredient_name }}</h3>
                <p>{{ item.display_amount || $t('shopping.no_amount') }}</p>
              </div>
              <el-tag :type="item.checked ? 'success' : 'info'">
                {{ item.checked ? $t('shopping.checked') : $t('shopping.pending') }}
              </el-tag>
            </div>

            <ul v-if="item.sources.length" class="source-trace-list">
              <li
                v-for="source in item.sources"
                :key="`${item.id}-${source.plan_date}-${source.recipe_name}-${source.meal_type}`"
              >
                {{ source.plan_date }} / {{ source.meal_type }} / {{ source.recipe_name }}
              </li>
            </ul>
            <p v-else class="muted-copy">{{ $t('shopping.manual_trace_empty') }}</p>
          </article>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { Check, Delete, ShoppingCart } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'

import { getApiErrorDetail } from '@/api'
import AppEmptyState from '@/components/common/AppEmptyState.vue'
import { useShoppingStore } from '@/stores/shopping'

const route = useRoute()
const { t } = useI18n()
const shoppingStore = useShoppingStore()
const { activeList, lists, loading, viewMode } = storeToRefs(shoppingStore)

const newItemName = ref('')
const newItemAmount = ref('')
const selectedListId = ref<number | null>(null)

const checkedCount = computed(() => activeList.value?.items.filter((item) => item.checked).length ?? 0)

watch(
  activeList,
  (value) => {
    selectedListId.value = value?.id ?? null
  },
  { immediate: true }
)

async function initializeList() {
  try {
    await shoppingStore.loadLists()

    const requestedListId = Number(route.query.list)
    if (Number.isFinite(requestedListId) && requestedListId > 0) {
      await shoppingStore.openList(requestedListId)
      return
    }

    if (!activeList.value && lists.value.length) {
      await shoppingStore.openList(lists.value[0].id)
    }
  } catch (error) {
    const detail = getApiErrorDetail(error)
    if (detail === 'Shopping list not found') {
      ElMessage.error(t('shopping.errors.resource_missing'))
      return
    }
    ElMessage.error(t('shopping.errors.load_failed'))
  }
}

async function handleListChange(value: number) {
  try {
    await shoppingStore.openList(value)
  } catch (error) {
    const detail = getApiErrorDetail(error)
    if (detail === 'Shopping list not found') {
      ElMessage.error(t('shopping.errors.resource_missing'))
      return
    }
    ElMessage.error(t('shopping.errors.load_failed'))
  }
}

async function handleAddItem() {
  if (!activeList.value || !newItemName.value.trim()) return

  try {
    await shoppingStore.addItem(activeList.value.id, {
      ingredient_name: newItemName.value.trim(),
      display_amount: newItemAmount.value.trim()
    })
    newItemName.value = ''
    newItemAmount.value = ''
    ElMessage.success(t('shopping.add_success'))
  } catch (error) {
    ElMessage.error(t('shopping.errors.add_failed'))
  }
}

async function toggleItem(itemId: number, checked: boolean) {
  try {
    await shoppingStore.toggleItem(itemId, checked)
  } catch (error) {
    const detail = getApiErrorDetail(error)
    if (detail === 'Shopping list not found' || detail === 'Shopping list item not found') {
      ElMessage.error(t('shopping.errors.resource_missing'))
      return
    }
    ElMessage.error(t('shopping.errors.update_failed'))
  }
}

async function removeItem(itemId: number) {
  try {
    await shoppingStore.deleteItem(itemId)
    ElMessage.success(t('shopping.remove_success'))
  } catch (error) {
    const detail = getApiErrorDetail(error)
    if (detail === 'Shopping list not found' || detail === 'Shopping list item not found') {
      ElMessage.error(t('shopping.errors.resource_missing'))
      return
    }
    ElMessage.error(t('shopping.errors.delete_failed'))
  }
}

onMounted(async () => {
  await initializeList()
})
</script>

<style scoped>
.shopping-page {
  display: grid;
  gap: 24px;
}

.page-header,
.control-grid,
.add-grid,
.options-bar,
.shopping-item,
.item-copy,
.item-meta,
.source-card-head {
  display: flex;
  gap: 12px;
}

.page-header,
.options-bar,
.shopping-item,
.source-card-head {
  justify-content: space-between;
  align-items: center;
}

.page-header {
  flex-wrap: wrap;
}

.page-header h1,
.source-card h3,
.item-name {
  margin: 0;
  color: var(--color-secondary);
}

.subtitle,
.muted-copy,
.source-card p,
.item-amount,
.trace-count {
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.subtitle,
.source-card p {
  margin: 8px 0 0;
}

.control-grid,
.add-grid,
.options-bar {
  flex-wrap: wrap;
}

.list-select {
  width: min(320px, 100%);
}

.add-grid :deep(.el-input) {
  flex: 1;
  min-width: 180px;
}

.list-area,
.item-list,
.source-list {
  display: grid;
  gap: 14px;
}

.shopping-item,
.source-card {
  padding: 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(15, 23, 42, 0.08);
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

.check-button:focus-visible,
.delete-btn:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--color-primary-dark) 70%, white);
  outline-offset: 2px;
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

.item-copy,
.item-meta {
  flex-wrap: wrap;
  align-items: center;
}

.item-name {
  font-weight: 700;
  overflow-wrap: break-word;
}

.shopping-item.is-checked .item-name {
  text-decoration: line-through;
  color: var(--color-text-light);
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

.source-pill.weekly-plan {
  background: rgba(34, 197, 94, 0.14);
  color: var(--color-primary-dark);
}

.source-card {
  display: grid;
  gap: 14px;
}

.source-trace-list {
  margin: 0;
  padding-left: 18px;
  color: var(--color-text-secondary);
  display: grid;
  gap: 8px;
}

.delete-btn {
  color: var(--color-text-secondary);
}

.delete-btn:hover {
  color: #b91c1c;
  background: rgba(248, 113, 113, 0.12);
}

@media (max-width: 640px) {
  .page-header,
  .control-grid,
  .add-grid,
  .options-bar,
  .shopping-item,
  .source-card-head {
    flex-direction: column;
    align-items: stretch;
  }

  .page-header :deep(.el-button),
  .add-grid :deep(.el-button) {
    width: 100%;
    min-height: 44px;
  }
}
</style>
