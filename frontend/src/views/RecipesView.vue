<template>
  <div class="recipes">
    <el-card class="filter-card">
      <el-row :gutter="20" align="middle">
        <el-col :span="6">
          <el-input v-model="search" placeholder="搜索菜品..." clearable>
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.meal_type" placeholder="餐次" clearable style="width: 100%">
            <el-option label="早餐" value="breakfast" />
            <el-option label="午餐" value="lunch" />
            <el-option label="晚餐" value="dinner" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.category" placeholder="分类" clearable style="width: 100%">
            <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <span style="margin-right: 8px">价格:</span>
          <el-slider 
            v-model="priceRange" 
            range 
            :min="0" 
            :max="50" 
            :format-tooltip="(val: number) => `¥${val}`"
            style="width: 150px; display: inline-block"
          />
        </el-col>
        <el-col :span="4">
          <el-button @click="resetFilters">重置筛选</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-row :gutter="16" class="recipes-grid">
      <el-col :span="6" v-for="recipe in filteredRecipes" :key="recipe.id">
        <el-card class="recipe-card" shadow="hover" @click="showDetail(recipe)">
          <div class="recipe-category">{{ recipe.category }}</div>
          <h3>{{ recipe.name }}</h3>
          <div class="recipe-tags">
            <el-tag 
              v-for="tag in recipe.tags.slice(0, 3)" 
              :key="tag" 
              size="small" 
              type="info"
            >{{ tag }}</el-tag>
          </div>
          <el-divider />
          <div class="recipe-stats">
            <div class="stat">
              <span class="label">热量</span>
              <span class="value">{{ recipe.calories }} kcal</span>
            </div>
            <div class="stat">
              <span class="label">蛋白质</span>
              <span class="value">{{ recipe.protein }}g</span>
            </div>
            <div class="stat">
              <span class="label">价格</span>
              <span class="value price">¥{{ recipe.price }}</span>
            </div>
          </div>
          <div class="recipe-meals">
            <el-tag v-if="recipe.meal_type.includes('breakfast')" size="small" type="warning">早餐</el-tag>
            <el-tag v-if="recipe.meal_type.includes('lunch')" size="small">午餐</el-tag>
            <el-tag v-if="recipe.meal_type.includes('dinner')" size="small" type="success">晚餐</el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="filteredRecipes.length === 0" description="没有找到符合条件的菜品" />

    <!-- 详情弹窗 -->
    <el-dialog v-model="dialogVisible" :title="selectedRecipe?.name" width="500px">
      <template v-if="selectedRecipe">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="分类">{{ selectedRecipe.category }}</el-descriptions-item>
          <el-descriptions-item label="价格">¥{{ selectedRecipe.price }}</el-descriptions-item>
          <el-descriptions-item label="热量">{{ selectedRecipe.calories }} kcal</el-descriptions-item>
          <el-descriptions-item label="蛋白质">{{ selectedRecipe.protein }}g</el-descriptions-item>
          <el-descriptions-item label="碳水">{{ selectedRecipe.carbs }}g</el-descriptions-item>
          <el-descriptions-item label="脂肪">{{ selectedRecipe.fat }}g</el-descriptions-item>
          <el-descriptions-item label="烹饪时间">{{ selectedRecipe.cooking_time }} 分钟</el-descriptions-item>
          <el-descriptions-item label="适合餐次">
            {{ selectedRecipe.meal_type.map((t: string) => ({ breakfast: '早餐', lunch: '午餐', dinner: '晚餐' }[t])).join('、') }}
          </el-descriptions-item>
        </el-descriptions>
        <div style="margin-top: 16px">
          <strong>标签：</strong>
          <el-tag v-for="tag in selectedRecipe.tags" :key="tag" style="margin: 4px">{{ tag }}</el-tag>
        </div>
        <div v-if="selectedRecipe.description" style="margin-top: 16px">
          <strong>描述：</strong>
          <p>{{ selectedRecipe.description }}</p>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { recipeApi, type Recipe } from '@/api'

const recipes = ref<Recipe[]>([])
const categories = ref<string[]>([])
const search = ref('')
const priceRange = ref([0, 50])
const dialogVisible = ref(false)
const selectedRecipe = ref<Recipe | null>(null)

const filters = reactive({
  meal_type: '',
  category: ''
})

onMounted(async () => {
  try {
    const [recipesRes, categoriesRes] = await Promise.all([
      recipeApi.getList({ limit: 100 }),
      recipeApi.getCategories()
    ])
    recipes.value = recipesRes.data.items
    categories.value = categoriesRes.data
  } catch (error) {
    console.error('加载数据失败', error)
  }
})

const filteredRecipes = computed(() => {
  return recipes.value.filter(r => {
    if (search.value && !r.name.includes(search.value)) return false
    if (filters.meal_type && !r.meal_type.includes(filters.meal_type)) return false
    if (filters.category && r.category !== filters.category) return false
    if (r.price < priceRange.value[0] || r.price > priceRange.value[1]) return false
    return true
  })
})

const resetFilters = () => {
  search.value = ''
  filters.meal_type = ''
  filters.category = ''
  priceRange.value = [0, 50]
}

const showDetail = (recipe: Recipe) => {
  selectedRecipe.value = recipe
  dialogVisible.value = true
}
</script>

<style scoped>
.recipes {
  max-width: 1400px;
  margin: 0 auto;
}

.filter-card {
  margin-bottom: 20px;
}

.recipes-grid {
  margin-top: 20px;
}

.recipe-card {
  margin-bottom: 16px;
  cursor: pointer;
  transition: transform 0.2s;
}

.recipe-card:hover {
  transform: translateY(-4px);
}

.recipe-category {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.recipe-card h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #303133;
}

.recipe-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.recipe-stats {
  display: flex;
  justify-content: space-between;
}

.recipe-stats .stat {
  text-align: center;
}

.recipe-stats .label {
  display: block;
  font-size: 12px;
  color: #909399;
}

.recipe-stats .value {
  font-weight: bold;
  color: #303133;
}

.recipe-stats .value.price {
  color: #E6A23C;
}

.recipe-meals {
  margin-top: 12px;
  display: flex;
  gap: 4px;
  justify-content: center;
}
</style>