import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 类型定义
export interface Recipe {
  id: number
  name: string
  category: string
  calories: number
  protein: number
  carbs: number
  fat: number
  price: number
  tags: string[]
  meal_type: string[]
  cooking_time: number
  description?: string
}

export interface MealItem {
  meal_type: string
  recipe_id: number
  recipe_name: string
  calories: number
  protein: number
  carbs: number
  fat: number
  price: number
}

export interface NutritionSummary {
  total_calories: number
  total_protein: number
  total_carbs: number
  total_fat: number
  total_price: number
  calories_achievement: number
  protein_achievement: number
  budget_usage: number
}

export interface UserPreferences {
  health_goal: string
  target_calories: number
  target_protein: number
  target_carbs: number
  target_fat: number
  max_budget: number
  disliked_foods: string[]
  preferred_tags: string[]
}

export interface MealPlan {
  id: string
  created_at: string
  meals: MealItem[]
  nutrition: NutritionSummary
  target: UserPreferences
  score: number
}

// API 方法
export const recipeApi = {
  getList: (params?: Record<string, any>) => 
    api.get<{ total: number; items: Recipe[] }>('/recipes', { params }),
  
  getById: (id: number) => 
    api.get<Recipe>(`/recipes/${id}`),
  
  getCategories: () => 
    api.get<string[]>('/recipes/categories'),
  
  getTags: () => 
    api.get<string[]>('/recipes/tags')
}

export const mealPlanApi = {
  create: (preferences: Partial<UserPreferences>) => 
    api.post<MealPlan>('/meal-plans', { preferences }),
  
  quickPlan: (healthGoal: string, budget: number) => 
    api.post<MealPlan>(`/meal-plans/quick?health_goal=${healthGoal}&budget=${budget}`),
  
  getHistory: (limit = 10) => 
    api.get<MealPlan[]>('/meal-plans', { params: { limit } }),
  
  getById: (id: string) => 
    api.get<MealPlan>(`/meal-plans/${id}`)
}

export default api