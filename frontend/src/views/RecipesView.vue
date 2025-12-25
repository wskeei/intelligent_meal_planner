<template>
  <div class="recipes-page">
    <div class="page-header">
      <h1>{{ $t('recipes.title') }}</h1>
      <p class="subtitle">{{ $t('recipes.subtitle') }}</p>
    </div>

    <div class="recipes-layout">
      <!-- Sidebar Filters -->
      <aside class="filters-sidebar">
        <el-card shadow="never" class="filter-panel">
          <template #header>
             <div class="filter-header">
               <el-icon><Filter /></el-icon>
               <span>{{ $t('recipes.filters') }}</span>
               <el-button link type="primary" size="small" @click="resetFilters">{{ $t('recipes.reset') }}</el-button>
             </div>
          </template>

          <el-form label-position="top">
            <el-form-item :label="$t('recipes.meal_type')">
              <el-checkbox-group v-model="filters.meal_type">
                <el-checkbox label="breakfast">{{ $t('recipes.breakfast') }}</el-checkbox>
                <el-checkbox label="lunch">{{ $t('recipes.lunch') }}</el-checkbox>
                <el-checkbox label="dinner">{{ $t('recipes.dinner') }}</el-checkbox>
              </el-checkbox-group>
            </el-form-item>

            <el-divider />

            <el-form-item :label="$t('meal_plan.calories') + ' (kcal)'">
               <el-slider v-model="filters.calories" range :min="0" :max="1500" :step="50" />
            </el-form-item>

            <el-divider />
            
            <el-form-item :label="$t('meal_plan.cost') + ' (¥)'">
               <el-slider v-model="filters.price" range :min="0" :max="100" />
            </el-form-item>
          </el-form>
        </el-card>
      </aside>

      <!-- Main Content -->
      <main class="recipes-main">
        <!-- Search Bar -->
        <div class="search-bar">
          <el-input 
            v-model="filters.search" 
            :placeholder="$t('recipes.search_placeholder')" 
            size="large"
            clearable
            @input="debounceSearch"
          >
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </div>

        <!-- Recipe Grid -->
        <div v-loading="loading">
          <div v-if="recipes.length > 0" class="recipes-grid">
            <el-card 
              v-for="recipe in recipes" 
              :key="recipe.id" 
              class="recipe-card" 
              shadow="hover"
              @click="openDetails(recipe)"
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
                   <el-tag 
                     v-for="tag in (recipe.tags || []).slice(0, 2)" 
                     :key="tag" 
                     size="small" 
                     effect="plain"
                    >
                     {{ tag }}
                   </el-tag>
                 </div>
              </div>
            </el-card>
          </div>
          
          <el-empty v-else :description="$t('recipes.no_recipes')" />
        </div>
      </main>
    </div>

    <!-- Detail Dialog -->
    <el-dialog v-model="detailVisible" width="600px" custom-class="recipe-modal">
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
           <ul>
             <li v-for="(ing, idx) in selected.ingredients" :key="idx">{{ ing }}</li>
           </ul>
         </div>
         
         <div class="modal-section">
           <h3>{{ $t('recipes.instructions') }}</h3>
           <ol>
             <li v-for="(step, idx) in selected.instructions" :key="idx">{{ step }}</li>
           </ol>
         </div>
       </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { Filter, Search } from '@element-plus/icons-vue'
import axios from 'axios'
import _ from 'lodash' // Assuming lodash might be useful, or implement simple debounce

// Setup State
const recipes = ref<any[]>([])
const loading = ref(false)
const detailVisible = ref(false)
const selected = ref<any>(null)

const filters = reactive({
  search: '',
  meal_type: [] as string[],
  calories: [0, 1500],
  price: [0, 100]
})

// Fetch Data
const fetchRecipes = async () => {
  loading.value = true
  try {
    const params: any = {
      search: filters.search || undefined,
      min_price: filters.price[0],
      max_price: filters.price[1],
      min_calories: filters.calories[0],
      max_calories: filters.calories[1]
    }
    
    // Simple handling for meal_type array to single query - backend refactor might be needed for multi-select
    // For now taking the first selected or none
    if (filters.meal_type.length > 0) {
      params.meal_type = filters.meal_type[0] 
    }

    const { data } = await axios.get('http://localhost:8000/api/recipes', { params })
    recipes.value = data.items
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

// Debounce Search
let timeout: any
const debounceSearch = () => {
  clearTimeout(timeout)
  timeout = setTimeout(fetchRecipes, 500)
}

// Watch Filters
watch(() => [filters.calories, filters.price, filters.meal_type], () => {
  fetchRecipes()
}, { deep: true })

onMounted(fetchRecipes)

const resetFilters = () => {
  filters.search = ''
  filters.meal_type = []
  filters.calories = [0, 1500]
  filters.price = [0, 100]
  fetchRecipes()
}

const openDetails = (recipe: any) => {
  selected.value = recipe
  detailVisible.value = true
}

const getEmoji = (category: string) => {
  if (!category) return '🥘'
  if (category.includes('Chicken')) return '🍗'
  if (category.includes('Salad')) return '🥗'
  if (category.includes('Fish')) return '🐟'
  if (category.includes('Beef')) return '🥩'
  if (category.includes('Breakfast')) return '🍳'
  return '🥘'
}
</script>

<style scoped>
.recipes-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 32px;
}

.page-header h1 {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-secondary);
}

.recipes-layout {
  display: grid;
  grid-template-columns: 250px 1fr;
  gap: 32px;
}

@media (max-width: 768px) {
  .recipes-layout {
    grid-template-columns: 1fr;
  }
  .filters-sidebar {
    display: none; /* Mobile filters TODO */
  }
}

.filter-panel {
  position: sticky;
  top: 80px;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.search-bar {
  margin-bottom: 24px;
}

.recipes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 20px;
}

.recipe-card {
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  background: white;
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.recipe-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
}

.card-image-placeholder {
  height: 120px;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
}

.emoji {
  font-size: 48px;
}

.card-body {
  padding: 16px;
}

.card-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}

.price {
  color: var(--color-primary-dark);
  font-weight: 600;
}

.title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-text-main);
  margin-bottom: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.macros {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  background: #f8fafc;
  padding: 8px;
  border-radius: 8px;
}

.macro {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.macro .val {
  font-weight: 700;
  font-size: 0.9rem;
  color: var(--color-secondary);
}

.macro .lbl {
  font-size: 0.7rem;
  color: var(--color-text-light);
}

.tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

/* Modal */
.modal-header {
  text-align: center;
  margin-bottom: 24px;
}

.modal-icon {
  font-size: 64px;
}

.nutrition-panel {
  display: flex;
  justify-content: space-around;
  background: #f0fdf4;
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 24px;
}

.n-item {
  text-align: center;
}

.n-val {
  display: block;
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-primary-dark);
}

.n-lbl {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
}

.modal-section {
  margin-bottom: 20px;
}

.modal-section h3 {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--color-secondary);
}

.modal-section ul, .modal-section ol {
  padding-left: 20px;
  color: var(--color-text-main);
  line-height: 1.6;
}
</style>