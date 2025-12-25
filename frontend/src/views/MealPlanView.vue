<template>
  <div class="meal-plan-page">
    <div class="page-header">
      <h1>Meal Planner</h1>
      <p class="subtitle">AI-powered nutrition catering to your goals.</p>
    </div>

    <el-row :gutter="24">
      <!-- Left: Configuration -->
      <el-col :span="24" :lg="8">
        <el-card class="config-card" shadow="hover">
          <template #header>
            <div class="card-title">
              <el-icon><Operation /></el-icon>
              <span>Configuration</span>
            </div>
          </template>

          <transition name="fade">

            <div v-if="loading" class="loading-overlay">
              <div class="breathing-container">
                <div class="breath-core">
                  <div class="ripple"></div>
                  <div class="ripple"></div>
                  <div class="core-circle"></div>
                </div>
                <div class="status-text">
                  {{ loadingText }}
                </div>
                <!-- <p class="status-sub">Designing your perfect healthy menu...</p> -->
              </div>
            </div>
          </transition>

          <el-tabs v-model="activeTab" class="config-tabs">
            <el-tab-pane label="Preferences" name="manual">
            <el-form label-position="top" size="large">
            <el-form-item label="Health Goal">
               <el-select v-model="form.health_goal" @change="applyPreset">
                <el-option label="Healthy Eating" value="healthy" />
                <el-option label="Weight Loss" value="lose_weight" />
                <el-option label="Muscle Gain" value="gain_muscle" />
                <el-option label="Maintenance" value="maintain" />
              </el-select>
            </el-form-item>

            <div class="slider-group">
              <div class="slider-label">
                <span>Calories</span>
                <span class="val">{{ form.target_calories }} kcal</span>
              </div>
              <el-slider v-model="form.target_calories" :min="1200" :max="4000" :step="50" :show-tooltip="false" />
            </div>

            <div class="slider-group">
              <div class="slider-label">
                <span>Protein</span>
                <span class="val">{{ form.target_protein }} g</span>
              </div>
              <el-slider v-model="form.target_protein" :min="30" :max="250" :step="5" :show-tooltip="false" />
            </div>

            <div class="slider-group">
              <div class="slider-label">
                <span>Carbs</span>
                <span class="val">{{ form.target_carbs }} g</span>
              </div>
              <el-slider v-model="form.target_carbs" :min="20" :max="500" :step="10" :show-tooltip="false" />
            </div>

            <div class="slider-group">
              <div class="slider-label">
                <span>Fat</span>
                <span class="val">{{ form.target_fat }} g</span>
              </div>
              <el-slider v-model="form.target_fat" :min="10" :max="150" :step="5" :show-tooltip="false" />
            </div>

            <el-divider />
            
            <div class="slider-group">
              <div class="slider-label">
                <span>Budget Limit</span>
                <span class="val">¥{{ form.max_budget }}</span>
              </div>
              <el-slider v-model="form.max_budget" :min="20" :max="200" :step="5" :show-tooltip="false" />
            </div>

            <el-button 
              type="primary" 
              class="generate-btn" 
              :loading="loading"
              @click="generatePlan"
            >
              <el-icon style="margin-right: 8px"><MagicStick /></el-icon>
              Generate Plan
            </el-button>
            </el-form> <!-- Close form here -->
            </el-tab-pane>

            <el-tab-pane label="AI Assistant" name="ai">
              <div class="ai-intro">
                <p>Chat with our AI Nutritionist Team to get a personalized meal plan.</p>
                <div class="ai-examples">
                  <el-tag size="small" @click="useExample('I want a high protein diet for muscle gain, budget 100.')">Muscle Gain</el-tag>
                  <el-tag size="small" @click="useExample('Vegetarian diet for weight loss, around 1500 cals.')">Vegetarian</el-tag>
                </div>
              </div>
              
              <el-input
                v-model="aiMessage"
                type="textarea"
                :rows="6"
                placeholder="Ex: I want to lose weight, I don't like carrots, and my budget is 50."
                class="ai-input"
              />
              
              <el-button 
                type="primary" 
                class="generate-btn ai-btn" 
                :loading="loading"
                @click="generatePlan"
              >
                <el-icon style="margin-right: 8px"><ChatLineRound /></el-icon>
                Ask AI Chef
              </el-button>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>

      <!-- Right: Results -->
      <el-col :span="24" :lg="16">
        <transition name="fade" mode="out-in">
          <!-- Empty State -->
          <div v-if="!mealPlan" class="empty-state">
            <div class="illustration">🍽️</div>
            <h3>Ready to Cook?</h3>
            <p>Adjust your preferences and click "Generate Plan" to get started.</p>
          </div>

          <!-- Results -->
          <div v-else class="results-container">
            <!-- Nutrition Summary -->
             <div class="summary-grid">
               <div class="summary-card">
                 <div class="lbl">Calories</div>
                 <div class="val">{{ mealPlan.nutrition.total_calories.toFixed(0) }}</div>
                 <el-progress 
                    :percentage="Math.min(mealPlan.nutrition.calories_achievement, 100)" 
                    :show-text="false" 
                    :color="getColor(mealPlan.nutrition.calories_achievement)"
                    :stroke-width="6"
                 />
               </div>
               <div class="summary-card">
                 <div class="lbl">Protein</div>
                 <div class="val">{{ mealPlan.nutrition.total_protein.toFixed(0) }}g</div>
                 <el-progress 
                    :percentage="Math.min(mealPlan.nutrition.protein_achievement, 100)" 
                    :show-text="false" 
                    :color="getColor(mealPlan.nutrition.protein_achievement)"
                    :stroke-width="6"
                 />
               </div>
               <div class="summary-card">
                 <div class="lbl">Cost</div>
                 <div class="val">¥{{ mealPlan.nutrition.total_price.toFixed(1) }}</div>
                  <el-progress 
                    :percentage="Math.min(mealPlan.nutrition.budget_usage, 100)" 
                    :show-text="false" 
                    :color="getBudgetColor(mealPlan.nutrition.budget_usage)"
                    :stroke-width="6"
                 />
               </div>
               <div class="summary-card highlight">
                 <div class="lbl">AI Score</div>
                 <div class="val">{{ mealPlan.score.toFixed(1) }}</div>
               </div>
             </div>

             <!-- Meal Cards -->
             <div class="meals-list">
               <div 
                  v-for="meal in mealPlan.meals" 
                  :key="meal.meal_type" 
                  class="meal-card"
               >
                 <div class="meal-icon-side" :class="meal.meal_type">
                   {{ getMealIcon(meal.meal_type) }}
                 </div>
                 
                 <div class="meal-details">
                   <div class="meal-type">{{ getMealName(meal.meal_type) }}</div>
                   <h3 class="meal-name">{{ meal.recipe_name }}</h3>
                   <div class="meal-tags">
                     <span class="tag">{{ meal.calories.toFixed(0) }} kcal</span>
                     <span class="tag">Prot: {{ meal.protein.toFixed(0) }}g</span>
                     <span class="tag">¥{{ meal.price }}</span>
                   </div>
                 </div>

                 <div class="meal-actions">
                   <el-button circle plain @click="addToShopping(meal)">
                     <el-icon><ShoppingCart /></el-icon>
                   </el-button>
                   <el-button circle plain @click="showDetails(meal)">
                     <el-icon><More /></el-icon>
                   </el-button>
                 </div>
               </div>
             </div>
          </div>
        </transition>
      </el-col>
    </el-row>

    <!-- Details Dialog -->
    <el-dialog v-model="detailsVisible" title="Meal Details" width="400px" center>
      <div v-if="selectedMeal" class="dialog-content">
        <div class="dialog-icon">{{ getMealIcon(selectedMeal.meal_type) }}</div>
        <h2>{{ selectedMeal.recipe_name }}</h2>
        <div class="dialog-stats">
          <div class="d-stat">
            <span class="d-val">{{ selectedMeal.calories }}</span>
            <span class="d-lbl">kcal</span>
          </div>
          <div class="d-stat">
             <span class="d-val">{{ selectedMeal.protein }}g</span>
             <span class="d-lbl">Protein</span>
          </div>
           <div class="d-stat">
             <span class="d-val">{{ selectedMeal.fat }}g</span>
             <span class="d-lbl">Fat</span>
          </div>
           <div class="d-stat">
             <span class="d-val">{{ selectedMeal.carbs }}g</span>
             <span class="d-lbl">Carbs</span>
          </div>
        </div>
        <p class="dialog-desc">Estimated cost: ¥{{ selectedMeal.price }}</p>
      </div>
       <template #footer>
        <span class="dialog-footer">
          <el-button @click="detailsVisible = false">Close</el-button>
          <el-button type="primary" @click="addAndClose">
            Add to List
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useShoppingStore } from '@/stores/shopping'
import { mealPlanApi, type MealPlan, type MealItem } from '@/api'
import { ElMessage } from 'element-plus'
import { Operation, MagicStick, ShoppingCart, More, ChatLineRound } from '@element-plus/icons-vue'

const route = useRoute()
const userStore = useUserStore()
const shoppingStore = useShoppingStore()

// State
const loading = ref(false)
const mealPlan = ref<MealPlan | null>(null)
const detailsVisible = ref(false)
const selectedMeal = ref<MealItem | null>(null)
const activeTab = ref('manual')
const aiMessage = ref('')

// Form
const form = reactive({
  health_goal: userStore.profile.goal || 'healthy',
  target_calories: 2000, // Will sync with store on mount
  target_protein: 100,
  target_carbs: 250,
  target_fat: 60,
  max_budget: 50
})

// Logic
onMounted(() => {
  // Sync with user store if available, or query params
  const goalQuery = route.query.goal as string
  if (goalQuery) form.health_goal = goalQuery as any
  
  // Apply logic to set initial values
  applyPreset()
})

const presets = {
  lose_weight: { target_calories: 1500, target_protein: 140, target_carbs: 100, target_fat: 50 },
  gain_muscle: { target_calories: 2800, target_protein: 180, target_carbs: 350, target_fat: 80 },
  maintain: { target_calories: 2200, target_protein: 130, target_carbs: 250, target_fat: 70 },
  healthy: { target_calories: 2000, target_protein: 100, target_carbs: 220, target_fat: 60 }
}

function applyPreset() {
  const p = presets[form.health_goal] || presets['healthy']
  // If user store has specific calories, maybe prefer that? 
  // For now let's stick to presets or what the user sees in Profile
  if (userStore.targetCalories > 0) {
     form.target_calories = userStore.targetCalories
     form.target_protein = userStore.targetMacros.protein
     form.target_carbs = userStore.targetMacros.carbs
     form.target_fat = userStore.targetMacros.fat
  } else {
     Object.assign(form, p)
  }
}

const loadingText = ref('Connecting to your personal chef...')
let loadingInterval: any = null

const breathingMessages = [
  'Analyzing your unique profile...',
  'Checking nutritional database...',
  'Balancing calories and macros...',
  'Selecting fresh ingredients...',
  'Crafting your perfect meal plan...'
]

function startLoading() {
  loading.value = true
  let i = 0
  loadingText.value = breathingMessages[0]
  loadingInterval = setInterval(() => {
    i = (i + 1) % breathingMessages.length
    loadingText.value = breathingMessages[i]
  }, 2500)
}

function stopLoading() {
  loading.value = false
  if (loadingInterval) clearInterval(loadingInterval)
}

async function generatePlan() {
  startLoading()
  try {
    const isAI = activeTab.value === 'ai'
    
    if (isAI && !aiMessage.value.trim()) {
      ElMessage.warning('Please enter your request.')
      stopLoading()
      return
    }

    const { data } = await mealPlanApi.create({
      health_goal: form.health_goal,
      target_calories: form.target_calories,
      target_protein: form.target_protein,
      target_carbs: form.target_carbs,
      target_fat: form.target_fat,
      max_budget: form.max_budget
    }, isAI, aiMessage.value)
    
    // Artificial delay to show off the animation if response is too fast
    if (!isAI) {
        setTimeout(() => {
            mealPlan.value = data
            stopLoading()
            ElMessage.success('Menu generated successfully!')
        }, 1500)
    } else {
        mealPlan.value = data
        stopLoading()
        ElMessage.success('Menu generated successfully!')
    }

  } catch (error: any) {
    console.error('Meal Plan Generation Error:', error)
    if (error.response) {
      console.error('Response Data:', error.response.data)
      console.error('Response Status:', error.response.status)
      ElMessage.error(`Error: ${error.response.data?.detail || error.message}`)
    } else if (error.request) {
      console.error('No response received:', error.request)
      ElMessage.error('Network Error: No response from server. Please check your connection.')
    } else {
      console.error('Error Message:', error.message)
      ElMessage.error(`Client Error: ${error.message}`)
    }
    stopLoading()
  }
}

// Helpers
const getMealIcon = (type: string) => ({ breakfast: '🥯', lunch: '🍱', dinner: '🍲' }[type] || '🍽️')
const getMealName = (type: string) => type.charAt(0).toUpperCase() + type.slice(1)

const getColor = (pct: number) => {
  if (pct >= 90 && pct <= 110) return '#4ade80' // success
  if (pct >= 70 && pct <= 130) return '#facc15' // warning
  return '#ef4444' // danger
}
const getBudgetColor = (pct: number) => pct <= 100 ? '#4ade80' : '#ef4444'

// Actions
function addToShopping(meal: MealItem) {
  shoppingStore.addItem(meal.recipe_name, '1 serving', meal.meal_type)
  ElMessage.success(`Added ${meal.recipe_name} to List`)
}

function showDetails(meal: MealItem) {
  selectedMeal.value = meal
  detailsVisible.value = true
}

function addAndClose() {
  if (selectedMeal.value) {
    addToShopping(selectedMeal.value)
    detailsVisible.value = false
  }
}

function useExample(msg: string) {
  aiMessage.value = msg
}

</script>




<style scoped>
/* Loading Overlay - Health Breathing Style */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(255, 255, 255, 0.92); /* White clean background */
  backdrop-filter: blur(20px);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}

.breathing-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
}

/* Breathing Core Animation */
.breath-core {
  position: relative;
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.core-circle {
  width: 60px;
  height: 60px;
  background: #4ade80; /* Health Green */
  border-radius: 50%;
  box-shadow: 0 0 20px rgba(74, 222, 128, 0.4);
  animation: breathe 4s ease-in-out infinite;
  z-index: 10;
}

.ripple {
  position: absolute;
  border-radius: 50%;
  background: rgba(74, 222, 128, 0.2);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: ripple 4s cubic-bezier(0, 0.2, 0.8, 1) infinite;
}

.ripple:nth-child(2) { animation-delay: 1s; }
.ripple:nth-child(3) { animation-delay: 2s; }

/* Status Text */
.status-text {
  font-size: 1.1rem;
  font-weight: 500;
  color: #374151; /* Soft Gray */
  letter-spacing: 0.5px;
  text-align: center;
  animation: fadeText 2s ease-in-out infinite alternate;
}

.status-sub {
  font-size: 0.9rem;
  color: #9ca3af;
  margin-top: 8px;
}

/* Animations */
@keyframes breathe {
  0%, 100% { transform: scale(0.95); opacity: 0.9; }
  50% { transform: scale(1.1); opacity: 1; box-shadow: 0 0 40px rgba(74, 222, 128, 0.6); }
}

@keyframes ripple {
  0% { width: 60px; height: 60px; opacity: 0.8; }
  100% { width: 200px; height: 200px; opacity: 0; }
}

@keyframes fadeText {
  0% { opacity: 0.7; }
  100% { opacity: 1; }
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.term-title { margin-left: 10px; color: #666; font-size: 0.8rem; }

.terminal-content {
  height: 120px; /* Fixed height to prevent jump */
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: flex-end; /* Show latest logs */
}

.log-line {
  color: #00ff9d; /* Matrix green */
  margin-bottom: 4px;
  font-family: 'Courier New', monospace;
}

.typing {
  animation: blink 1s infinite;
}

@keyframes blink { 50% { opacity: 0; } }

</style>

<style scoped>
/* Original Styles */
.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-secondary);
}

.subtitle {
  color: var(--color-text-secondary);
}

.config-card {
  border: none;
  background: white;
  border-radius: var(--radius-lg);
  margin-bottom: 24px;
  position: relative; /* For loading overlay */
  overflow: hidden;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: var(--color-secondary);
}

.slider-group {
  margin-bottom: 20px;
}

.slider-label {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  color: var(--color-text-main);
  margin-bottom: 4px;
}

.slider-label .val {
  font-weight: 600;
  color: var(--color-primary-dark);
}

.generate-btn {
  width: 100%;
  margin-top: 16px;
  font-weight: 600;
  padding: 20px;
  border-radius: var(--radius-md);
  font-size: 1rem;
}

/* Results Area */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: var(--radius-lg);
  color: var(--color-text-secondary);
}

.illustration {
  font-size: 64px;
  margin-bottom: 16px;
}

.results-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

@media (max-width: 600px) {
  .summary-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.summary-card {
  background: white;
  padding: 16px;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  text-align: center;
}

.summary-card .lbl {
  font-size: 0.8rem;
  color: var(--color-text-light);
  margin-bottom: 4px;
}

.summary-card .val {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-secondary);
  margin-bottom: 8px;
}

.summary-card.highlight {
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  color: var(--color-primary-dark);
}

.summary-card.highlight .val {
  color: var(--color-primary-dark);
}

/* Meal List */
.meals-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.meal-card {
  background: white;
  border-radius: var(--radius-lg);
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: var(--shadow-sm);
  transition: all 0.2s;
}

.meal-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.meal-icon-side {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  border-radius: 12px;
  background: #f8fafc;
}

.meal-icon-side.breakfast { background: #fff7ed; }
.meal-icon-side.lunch { background: #f0f9ff; }
.meal-icon-side.dinner { background: #fdf2f8; }

.meal-details {
  flex: 1;
}

.meal-type {
  font-size: 0.8rem;
  color: var(--color-text-light);
  text-transform: uppercase;
  font-weight: 600;
  letter-spacing: 0.05em;
}

.meal-name {
  font-size: 1.1rem;
  color: var(--color-text-main);
  margin: 4px 0 8px;
}

.meal-tags {
  display: flex;
  gap: 8px;
}

.tag {
  background: #f1f5f9;
  color: var(--color-text-secondary);
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
}

.meal-actions {
  display: flex;
  gap: 8px;
}

/* Dialog */
.dialog-content {
  text-align: center;
}

.dialog-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.dialog-stats {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin: 24px 0;
}

.d-stat {
  display: flex;
  flex-direction: column;
}

.d-val {
  font-weight: 700;
  font-size: 1.1rem;
  color: var(--color-secondary);
}

.d-lbl {
  font-size: 0.8rem;
  color: var(--color-text-light);
}

.ai-intro {
  margin-bottom: 16px;
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}

.ai-examples {
  margin-top: 8px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.ai-examples .el-tag {
  cursor: pointer;
}

.ai-input textarea {
  font-family: inherit;
}

.ai-btn {
  background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
  border: none;
}

.ai-btn:hover {
  opacity: 0.9;
}
</style>