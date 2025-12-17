<template>
  <div class="meal-plan">
    <el-row :gutter="20">
      <!-- 左侧：参数设置 -->
      <el-col :span="8">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <el-icon><Setting /></el-icon>
              <span>配餐参数</span>
            </div>
          </template>

          <el-form :model="form" label-position="top">
            <el-form-item label="健康目标">
              <el-select v-model="form.health_goal" style="width: 100%">
                <el-option label="健康饮食" value="healthy" />
                <el-option label="减脂瘦身" value="lose_weight" />
                <el-option label="增肌塑形" value="gain_muscle" />
                <el-option label="维持体重" value="maintain" />
              </el-select>
            </el-form-item>

            <el-divider>营养目标</el-divider>

            <el-form-item label="目标卡路里 (kcal)">
              <el-slider v-model="form.target_calories" :min="1200" :max="3500" :step="100" show-input />
            </el-form-item>

            <el-form-item label="目标蛋白质 (g)">
              <el-slider v-model="form.target_protein" :min="50" :max="200" :step="10" show-input />
            </el-form-item>

            <el-form-item label="目标碳水 (g)">
              <el-slider v-model="form.target_carbs" :min="100" :max="400" :step="25" show-input />
            </el-form-item>

            <el-form-item label="目标脂肪 (g)">
              <el-slider v-model="form.target_fat" :min="30" :max="150" :step="10" show-input />
            </el-form-item>

            <el-divider>预算限制</el-divider>

            <el-form-item label="最大预算 (元)">
              <el-slider v-model="form.max_budget" :min="20" :max="150" :step="5" show-input />
            </el-form-item>

            <el-button 
              type="primary" 
              size="large" 
              style="width: 100%; margin-top: 20px"
              :loading="loading"
              @click="generatePlan"
            >
              <el-icon><MagicStick /></el-icon>
              生成配餐方案
            </el-button>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右侧：配餐结果 -->
      <el-col :span="16">
        <el-card v-if="!mealPlan" class="result-card empty">
          <el-empty description="设置参数后点击生成配餐方案">
            <template #image>
              <div style="font-size: 80px">🍽️</div>
            </template>
          </el-empty>
        </el-card>

        <template v-else>
          <!-- 三餐展示 -->
          <el-row :gutter="16" class="meals-row">
            <el-col :span="8" v-for="meal in mealPlan.meals" :key="meal.meal_type">
              <el-card class="meal-card" :class="meal.meal_type">
                <template #header>
                  <div class="meal-header">
                    <span class="meal-icon">{{ getMealIcon(meal.meal_type) }}</span>
                    <span>{{ getMealName(meal.meal_type) }}</span>
                  </div>
                </template>
                <h3>{{ meal.recipe_name }}</h3>
                <div class="meal-info">
                  <el-tag size="small">{{ meal.calories }} kcal</el-tag>
                  <el-tag size="small" type="success">蛋白质 {{ meal.protein }}g</el-tag>
                  <el-tag size="small" type="warning">¥{{ meal.price }}</el-tag>
                </div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 营养汇总 -->
          <el-card class="nutrition-card">
            <template #header>
              <div class="card-header">
                <el-icon><DataAnalysis /></el-icon>
                <span>营养达成分析</span>
              </div>
            </template>

            <el-row :gutter="20">
              <el-col :span="6">
                <div class="stat-item">
                  <el-progress 
                    type="dashboard" 
                    :percentage="Math.min(mealPlan.nutrition.calories_achievement, 100)"
                    :color="getProgressColor(mealPlan.nutrition.calories_achievement)"
                  />
                  <div class="stat-label">卡路里</div>
                  <div class="stat-value">{{ mealPlan.nutrition.total_calories.toFixed(0) }} / {{ form.target_calories }} kcal</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="stat-item">
                  <el-progress 
                    type="dashboard" 
                    :percentage="Math.min(mealPlan.nutrition.protein_achievement, 100)"
                    :color="getProgressColor(mealPlan.nutrition.protein_achievement)"
                  />
                  <div class="stat-label">蛋白质</div>
                  <div class="stat-value">{{ mealPlan.nutrition.total_protein.toFixed(1) }} / {{ form.target_protein }} g</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="stat-item">
                  <el-progress 
                    type="dashboard" 
                    :percentage="Math.min(mealPlan.nutrition.budget_usage, 100)"
                    :color="getBudgetColor(mealPlan.nutrition.budget_usage)"
                  />
                  <div class="stat-label">预算使用</div>
                  <div class="stat-value">¥{{ mealPlan.nutrition.total_price.toFixed(1) }} / ¥{{ form.max_budget }}</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="stat-item score">
                  <div class="score-value">{{ mealPlan.score.toFixed(1) }}</div>
                  <div class="stat-label">AI 评分</div>
                  <el-rate :model-value="mealPlan.score / 10" disabled />
                </div>
              </el-col>
            </el-row>
          </el-card>
        </template>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Setting, MagicStick, DataAnalysis } from '@element-plus/icons-vue'
import { mealPlanApi, type MealPlan } from '@/api'

const route = useRoute()
const loading = ref(false)
const mealPlan = ref<MealPlan | null>(null)

const form = reactive({
  health_goal: 'healthy',
  target_calories: 2000,
  target_protein: 100,
  target_carbs: 250,
  target_fat: 60,
  max_budget: 50
})

// 根据健康目标设置预设值
const presets: Record<string, typeof form> = {
  lose_weight: { health_goal: 'lose_weight', target_calories: 1500, target_protein: 120, target_carbs: 150, target_fat: 45, max_budget: 50 },
  gain_muscle: { health_goal: 'gain_muscle', target_calories: 2500, target_protein: 150, target_carbs: 300, target_fat: 80, max_budget: 60 },
  maintain: { health_goal: 'maintain', target_calories: 2000, target_protein: 100, target_carbs: 250, target_fat: 65, max_budget: 50 },
  healthy: { health_goal: 'healthy', target_calories: 1800, target_protein: 90, target_carbs: 220, target_fat: 55, max_budget: 45 }
}

onMounted(() => {
  const goal = route.query.goal as string
  if (goal && presets[goal]) {
    Object.assign(form, presets[goal])
  }
})

const generatePlan = async () => {
  loading.value = true
  try {
    const { data } = await mealPlanApi.create({
      health_goal: form.health_goal,
      target_calories: form.target_calories,
      target_protein: form.target_protein,
      target_carbs: form.target_carbs,
      target_fat: form.target_fat,
      max_budget: form.max_budget
    })
    mealPlan.value = data
    ElMessage.success('配餐方案生成成功！')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '生成失败，请重试')
  } finally {
    loading.value = false
  }
}

const getMealIcon = (type: string) => {
  const icons: Record<string, string> = { breakfast: '🌅', lunch: '☀️', dinner: '🌙' }
  return icons[type] || '🍽️'
}

const getMealName = (type: string) => {
  const names: Record<string, string> = { breakfast: '早餐', lunch: '午餐', dinner: '晚餐' }
  return names[type] || type
}

const getProgressColor = (pct: number) => {
  if (pct >= 90 && pct <= 110) return '#67C23A'
  if (pct >= 70 && pct <= 130) return '#E6A23C'
  return '#F56C6C'
}

const getBudgetColor = (pct: number) => {
  if (pct <= 80) return '#67C23A'
  if (pct <= 100) return '#E6A23C'
  return '#F56C6C'
}
</script>

<style scoped>
.meal-plan {
  max-width: 1400px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
}

.settings-card {
  position: sticky;
  top: 20px;
}

.result-card.empty {
  min-height: 500px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.meals-row {
  margin-bottom: 20px;
}

.meal-card {
  text-align: center;
}

.meal-card.breakfast { border-top: 3px solid #E6A23C; }
.meal-card.lunch { border-top: 3px solid #409EFF; }
.meal-card.dinner { border-top: 3px solid #764ba2; }

.meal-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: bold;
}

.meal-icon {
  font-size: 24px;
}

.meal-card h3 {
  margin: 12px 0;
  color: #303133;
}

.meal-info {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.nutrition-card {
  margin-top: 20px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.stat-value {
  font-size: 12px;
  color: #606266;
}

.stat-item.score {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.score-value {
  font-size: 48px;
  font-weight: bold;
  color: #409EFF;
}
</style>