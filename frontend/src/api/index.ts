import axios from 'axios'

import { API_BASE_URL } from './config'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers = config.headers ?? {}
    ;(config.headers as Record<string, string>).Authorization = `Bearer ${token}`
  }
  return config
})

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
  ingredients?: string[]
  instructions?: string[]
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

export interface ChatMessage {
  role: 'assistant' | 'user'
  content: string
  created_at?: string
}

export interface CrewTraceEvent {
  agent: string
  status: 'completed' | 'running' | 'blocked' | string
  message: string
  payload?: Record<string, unknown>
}

export type MealChatPhase = 'discovering' | 'negotiating' | 'planning' | 'planning_ready' | 'finalized'

export interface MealChatFollowUpPlan {
  questions: string[]
  assistant_message: string
}

export interface MealChatNegotiationOption {
  key: string
  title: string
  rationale: string
  budget: number
  preferred_tags: string[]
}

export interface NegotiatedMealPlanAlternative {
  option_key: string
  title: string
  rationale: string
  meal_plan: MealPlan
}

export interface NegotiatedMealPlan {
  primary: MealPlan
  alternatives: NegotiatedMealPlanAlternative[]
}

export interface MealChatSession {
  session_id: string
  status: MealChatPhase
  messages: ChatMessage[]
  meal_plan: MealPlan | NegotiatedMealPlan | null
  crew_trace: CrewTraceEvent[]
  profile_snapshot?: Record<string, unknown>
  preferences_snapshot?: Record<string, unknown>
  known_facts?: Record<string, unknown>
  open_questions?: string[]
  follow_up_plan?: MealChatFollowUpPlan | null
  negotiation_options?: MealChatNegotiationOption[]
}

export interface UserProfilePatch {
  age?: number | null
  gender?: 'male' | 'female' | null
  height?: number | null
  weight?: number | null
  activity_level?: 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active' | null
  health_goal?: 'lose_weight' | 'gain_muscle' | 'maintain' | 'healthy'
}

export interface FeasibilityResult {
  budget: number
  max_calories: number
  max_protein: number
  max_carbs: number
  max_fat: number
  calories_feasibility: number
  protein_feasibility: number
  carbs_feasibility: number
  fat_feasibility: number
  has_warning: boolean
  warning_message: string
}

export const recipeApi = {
  getList: (params?: Record<string, any>) =>
    api.get<{ total: number; items: Recipe[] }>('/recipes', { params }),

  getById: (id: number) => api.get<Recipe>(`/recipes/${id}`),

  getCategories: () => api.get<string[]>('/recipes/categories'),

  getTags: () => api.get<string[]>('/recipes/tags')
}

export const authApi = {
  me: () => api.get('/auth/me'),
  updateProfile: (payload: UserProfilePatch) => api.patch('/auth/me/profile', payload)
}

export const mealPlanApi = {
  create: (preferences: Partial<UserPreferences>, use_agent = false, user_message = '') =>
    api.post<MealPlan>('/meal-plans', { preferences, use_agent, user_message }),

  quickPlan: (healthGoal: string, budget: number) =>
    api.post<MealPlan>(`/meal-plans/quick?health_goal=${healthGoal}&budget=${budget}`),

  getHistory: (limit = 10) => api.get<MealPlan[]>('/meal-plans', { params: { limit } }),

  getById: (id: string) => api.get<MealPlan>(`/meal-plans/${id}`)
}

export const mealChatApi = {
  createSession: () => api.post<MealChatSession>('/meal-chat/sessions'),
  getSession: (sessionId: string) => api.get<MealChatSession>(`/meal-chat/sessions/${sessionId}`),
  sendMessage: (sessionId: string, content: string) =>
    api.post<MealChatSession>(`/meal-chat/sessions/${sessionId}/messages`, { content })
}

export const feasibilityApi = {
  check: (params: {
    budget: number
    target_calories: number
    target_protein: number
    target_carbs: number
    target_fat: number
  }) => api.get<FeasibilityResult>('/meal-plans/feasibility', { params })
}

export default api
