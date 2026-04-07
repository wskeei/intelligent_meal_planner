<template>
  <div class="recipes-page">
    <header class="page-header">
      <div>
        <h1>{{ $t('recipes.title') }}</h1>
        <p class="subtitle">{{ $t('recipes.subtitle') }}</p>
      </div>
      <el-button text @click="resetFilters">{{ $t('recipes.reset') }}</el-button>
    </header>

    <div class="recipes-layout">
      <aside class="filters-sidebar">
        <el-card class="filter-panel" shadow="never">
          <template #header>
            <div class="filter-header">
              <span>{{ $t('recipes.filters') }}</span>
            </div>
          </template>

          <el-form label-position="top" class="filters-form">
            <el-form-item :label="$t('recipes.meal_type')">
              <el-radio-group v-model="filters.meal_type" class="meal-type-group">
                <el-radio-button value="">{{ $t('recipes.all_meals') }}</el-radio-button>
                <el-radio-button value="breakfast">{{ $t('recipes.breakfast') }}</el-radio-button>
                <el-radio-button value="lunch">{{ $t('recipes.lunch') }}</el-radio-button>
                <el-radio-button value="dinner">{{ $t('recipes.dinner') }}</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-form-item :label="`${$t('meal_plan.calories')} (kcal)`">
              <el-slider v-model="filters.calories" range :min="0" :max="1500" :step="50" />
            </el-form-item>

            <el-form-item :label="`${$t('meal_plan.cost')} (¥)`">
              <el-slider v-model="filters.price" range :min="0" :max="100" />
            </el-form-item>
          </el-form>
        </el-card>
      </aside>

      <main class="recipes-main">
        <div class="search-bar">
          <el-input
            v-model="filters.search"
            :placeholder="$t('recipes.search_placeholder')"
            size="large"
            clearable
            @input="debounceSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>

        <div v-loading="loading" class="results-shell">
          <AppEmptyState
            v-if="error"
            :icon="WarningFilled"
            :eyebrow="$t('recipes.error_eyebrow')"
            :title="$t('recipes.error_title')"
            :description="$t('recipes.error_desc')"
          >
            <template #actions>
              <el-button type="primary" @click="fetchRecipes">{{ $t('common.retry') }}</el-button>
            </template>
          </AppEmptyState>

          <AppEmptyState
            v-else-if="!recipes.length"
            :icon="Search"
            :eyebrow="$t('recipes.empty_eyebrow')"
            :title="$t('recipes.empty_title')"
            :description="$t('recipes.no_recipes')"
          >
            <template #actions>
              <el-button @click="resetFilters">{{ $t('recipes.reset') }}</el-button>
            </template>
          </AppEmptyState>

          <template v-else>
            <div class="results-header">
              <p>{{ $t('recipes.results_title', { count: recipes.length }) }}</p>
            </div>

            <div class="recipes-grid">
              <el-card
                v-for="recipe in recipes"
                :key="recipe.id"
                class="recipe-card"
                shadow="hover"
                role="button"
                tabindex="0"
                :aria-label="$t('recipes.open_details_for', { name: recipe.name })"
                @click="openDetails(recipe)"
                @keydown="onRecipeCardKeydown($event, recipe)"
              >
                <div class="card-image-placeholder">
                  <span class="emoji">{{ getEmoji(recipe.category) }}</span>
                </div>

                <div class="card-body">
                  <div class="card-meta">
                    <span class="category">{{ recipe.category }}</span>
                    <span class="price">¥{{ recipe.price }}</span>
                  </div>
                  <h3 class="title">{{ recipe.name }}</h3>

                  <div class="macros">
                    <div class="macro">
                      <span class="val">{{ recipe.calories }}</span>
                      <span class="lbl">{{ $t('meal_plan.calories') }}</span>
                    </div>
                    <div class="macro">
                      <span class="val">{{ recipe.protein }}g</span>
                      <span class="lbl">{{ $t('meal_plan.protein') }}</span>
                    </div>
                    <div class="macro">
                      <span class="val">{{ recipe.carbs }}g</span>
                      <span class="lbl">{{ $t('meal_plan.carbs') }}</span>
                    </div>
                  </div>

                  <div class="tags">
                    <el-tag v-for="tag in (recipe.tags || []).slice(0, 2)" :key="tag" size="small" effect="plain">
                      {{ tag }}
                    </el-tag>
                  </div>
                </div>
              </el-card>
            </div>
          </template>
        </div>
      </main>
    </div>

    <el-dialog v-model="detailVisible" :width="dialogWidth" class="recipe-modal">
      <template v-if="selected">
        <div class="modal-header">
          <div class="modal-icon">{{ getEmoji(selected.category) }}</div>
          <h2>{{ selected.name }}</h2>
          <div class="modal-tags">
            <el-tag v-for="tag in selected.tags" :key="tag">{{ tag }}</el-tag>
          </div>
        </div>

        <div class="nutrition-panel">
          <div class="n-item">
            <span class="n-val">{{ selected.calories }}</span>
            <span class="n-lbl">{{ $t('meal_plan.calories') }}</span>
          </div>
          <div class="n-item">
            <span class="n-val">{{ selected.protein }}g</span>
            <span class="n-lbl">{{ $t('meal_plan.protein') }}</span>
          </div>
          <div class="n-item">
            <span class="n-val">{{ selected.fat }}g</span>
            <span class="n-lbl">{{ $t('meal_plan.fat') }}</span>
          </div>
          <div class="n-item">
            <span class="n-val">{{ selected.carbs }}g</span>
            <span class="n-lbl">{{ $t('meal_plan.carbs') }}</span>
          </div>
        </div>

        <div class="modal-section">
          <h3>{{ $t('recipes.ingredients') }}</h3>
          <ul v-if="selected.ingredients?.length">
            <li v-for="(ingredient, index) in selected.ingredients" :key="`${selected.id}-ingredient-${index}`">
              {{ ingredient }}
            </li>
          </ul>
          <p v-else>{{ $t('recipes.details_pending') }}</p>
        </div>

        <div class="modal-section">
          <h3>{{ $t('recipes.instructions') }}</h3>
          <ol v-if="selected.instructions?.length">
            <li v-for="(step, index) in selected.instructions" :key="`${selected.id}-step-${index}`">
              {{ step }}
            </li>
          </ol>
          <p v-else>{{ $t('recipes.details_pending') }}</p>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Search, WarningFilled } from '@element-plus/icons-vue'

import { recipeApi, type Recipe } from '@/api'
import AppEmptyState from '@/components/common/AppEmptyState.vue'

const recipes = ref<Recipe[]>([])
const loading = ref(false)
const error = ref(false)
const detailVisible = ref(false)
const selected = ref<Recipe | null>(null)

const filters = reactive({
  search: '',
  meal_type: '',
  calories: [0, 1500] as [number, number],
  price: [0, 100] as [number, number]
})

const dialogWidth = computed(() => (window.innerWidth < 640 ? 'calc(100vw - 24px)' : '680px'))

async function fetchRecipes() {
  loading.value = true
  error.value = false

  try {
    const { data } = await recipeApi.getList({
      search: filters.search || undefined,
      meal_type: filters.meal_type || undefined,
      min_price: filters.price[0],
      max_price: filters.price[1],
      min_calories: filters.calories[0],
      max_calories: filters.calories[1]
    })

    recipes.value = data.items
  } catch (fetchError) {
    console.error(fetchError)
    error.value = true
  } finally {
    loading.value = false
  }
}

let timeoutId: number | undefined

function debounceSearch() {
  window.clearTimeout(timeoutId)
  timeoutId = window.setTimeout(fetchRecipes, 300)
}

watch(
  () => [filters.calories, filters.price, filters.meal_type],
  () => {
    void fetchRecipes()
  },
  { deep: true }
)

function resetFilters() {
  filters.search = ''
  filters.meal_type = ''
  filters.calories = [0, 1500]
  filters.price = [0, 100]
  void fetchRecipes()
}

function openDetails(recipe: Recipe) {
  selected.value = recipe
  detailVisible.value = true
}

function onRecipeCardKeydown(event: KeyboardEvent, recipe: Recipe) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    openDetails(recipe)
  }
}

function getEmoji(category: string) {
  if (!category) return '🥘'
  if (category.includes('Chicken')) return '🍗'
  if (category.includes('Salad')) return '🥗'
  if (category.includes('Fish')) return '🐟'
  if (category.includes('Beef')) return '🥩'
  if (category.includes('Breakfast')) return '🍳'
  return '🥘'
}

onMounted(() => {
  void fetchRecipes()
})
</script>

<style scoped>
.recipes-page {
  display: grid;
  gap: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-end;
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

.recipes-layout {
  display: grid;
  grid-template-columns: minmax(0, 280px) minmax(0, 1fr);
  gap: 24px;
  align-items: start;
}

.filter-panel {
  position: sticky;
  top: 88px;
  border-radius: 22px;
}

.filters-form {
  display: grid;
  gap: 10px;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 700;
  color: var(--color-secondary);
}

.meal-type-group {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.meal-type-group :deep(.el-radio-button__inner) {
  width: 100%;
}

.recipes-main {
  min-width: 0;
}

.search-bar {
  margin-bottom: 20px;
}

.results-shell {
  min-height: 260px;
}

.results-header {
  margin-bottom: 16px;
  color: var(--color-text-secondary);
}

.recipes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 18px;
}

.recipe-card {
  cursor: pointer;
  border: none;
  border-radius: 22px;
  overflow: hidden;
  transition:
    box-shadow 180ms ease,
    transform 180ms ease;
}

.recipe-card:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--color-primary-dark) 70%, white);
  outline-offset: 2px;
  transform: translateY(-1px);
}

.card-image-placeholder {
  display: grid;
  place-items: center;
  height: 132px;
  background: #f1f6f1;
}

.emoji {
  font-size: 52px;
}

.card-body {
  display: grid;
  gap: 12px;
  padding: 18px;
}

.card-meta,
.macros {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.card-meta {
  color: var(--color-text-secondary);
  font-size: 0.82rem;
}

.price {
  color: var(--color-primary-dark);
  font-weight: 700;
}

.title {
  margin: 0;
  color: var(--color-secondary);
  font-size: 1.08rem;
  line-height: 1.4;
  overflow-wrap: break-word;
}

.macros {
  padding: 10px 12px;
  border-radius: 14px;
  background: #f7faf8;
}

.macro {
  display: grid;
  justify-items: center;
  gap: 4px;
}

.macro .val {
  font-weight: 700;
  color: var(--color-secondary);
}

.macro .lbl {
  color: var(--color-text-light);
  font-size: 0.72rem;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.modal-header {
  display: grid;
  justify-items: center;
  gap: 10px;
  text-align: center;
  margin-bottom: 20px;
}

.modal-header h2 {
  margin: 0;
  color: var(--color-secondary);
}

.modal-icon {
  font-size: 64px;
}

.modal-tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}

.nutrition-panel {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 20px;
}

.n-item {
  display: grid;
  justify-items: center;
  gap: 4px;
  padding: 14px;
  border-radius: 16px;
  background: #f7faf8;
}

.n-val {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--color-secondary);
}

.n-lbl {
  color: var(--color-text-secondary);
  font-size: 0.8rem;
}

.modal-section {
  margin-bottom: 18px;
}

.modal-section h3 {
  margin: 0 0 10px;
  color: var(--color-secondary);
}

.modal-section p,
.modal-section li {
  color: var(--color-text-secondary);
  line-height: 1.6;
}

@media (max-width: 900px) {
  .recipes-layout {
    grid-template-columns: 1fr;
  }

  .filter-panel {
    position: static;
  }
}

@media (max-width: 640px) {
  .page-header,
  .card-meta {
    flex-direction: column;
    align-items: flex-start;
  }

  .meal-type-group,
  .nutrition-panel {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
