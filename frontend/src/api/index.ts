import axios from 'axios'

import { API_BASE_URL } from './config'
import { safeStorageGet } from '@/utils/resilience'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000
})

// Longer timeout for LLM-powered endpoints (CrewAI flow runs 3 sequential crews)
const longApi = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000
})

for (const instance of [api, longApi]) {
  instance.interceptors.request.use((config) => {
    const token = safeStorageGet('token')
    const locale = safeStorageGet('locale') || 'zh'
    if (token) {
      config.headers = config.headers ?? {}
      ;(config.headers as Record<string, string>).Authorization = `Bearer ${token}`
    }
    config.headers = config.headers ?? {}
    ;(config.headers as Record<string, string>)['Accept-Language'] = locale
    return config
  })
}

export function isUnauthorizedError(error: unknown) {
  return axios.isAxiosError(error) && error.response?.status === 401
}

export function getApiErrorDetail(error: unknown) {
  if (!axios.isAxiosError(error)) return ''
  const detail = error.response?.data?.detail
  return typeof detail === 'string' ? detail : ''
}

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
  ingredients?: Array<string | { name?: string; amount?: string; quantity?: string }>
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
  source_session_id?: string | null
}

export interface WeeklyPlanDay {
  id: number
  plan_date: string
  source_session_id?: string | null
  meal_plan_snapshot: MealPlan
  nutrition_snapshot: NutritionSummary
  completed: boolean
  completed_at?: string
}

export interface WeeklyPlanSummary {
  id: number
  name: string
  notes?: string | null
  created_at?: string
  updated_at?: string
  day_count: number
}

export interface WeeklyPlanAttachPayload {
  plan_date: string
  meal_plan_id: string
  source_session_id: string
}

export interface WeeklyPlan {
  id: number
  name: string
  notes?: string | null
  days: WeeklyPlanDay[]
  created_at?: string
  updated_at?: string
}

export interface ShoppingListSource {
  plan_date: string
  meal_type: string
  recipe_name: string
}

export interface ShoppingListItem {
  id: number
  ingredient_name: string
  display_amount: string
  checked: boolean
  category?: string | null
  source_kind: 'weekly-plan' | 'manual'
  sources: ShoppingListSource[]
}

export interface ShoppingListSummary {
  id: number
  name: string
  weekly_plan_id: number
  status: string
  created_at: string
  updated_at: string
  item_count: number
}

export interface ShoppingList {
  id: number
  name: string
  weekly_plan_id: number
  status: string
  created_at: string
  updated_at: string
  items: ShoppingListItem[]
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

export interface MealChatPresentation {
  phase: MealChatPhase | string
  overlay_state?: 'hidden' | 'result' | null
  can_generate?: boolean
  has_result_overlay?: boolean
}

export interface MealChatPresentationUpdate {
  overlay_state: 'hidden' | 'result'
}

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
  presentation?: MealChatPresentation | null
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

export const weeklyPlanApi = {
  list: () => api.get<WeeklyPlanSummary[]>('/weekly-plans'),
  create: (payload: { name: string; notes?: string }) => api.post<WeeklyPlan>('/weekly-plans', payload),
  getById: (id: number) => api.get<WeeklyPlan>(`/weekly-plans/${id}`),
  update: (id: number, payload: { name?: string; notes?: string }) =>
    api.patch<WeeklyPlan>(`/weekly-plans/${id}`, payload),
  delete: (id: number) => api.delete<{ success: boolean }>(`/weekly-plans/${id}`),
  attachDay: (id: number, payload: WeeklyPlanAttachPayload) =>
    api.post<WeeklyPlan>(`/weekly-plans/${id}/days`, payload),
  removeDay: (id: number, dayId: number) => api.delete<WeeklyPlan>(`/weekly-plans/${id}/days/${dayId}`),
  confirmDay: (id: number, date: string) =>
    api.post<{ synced_count: number; records: IntakeRecord[] }>(`/weekly-plans/${id}/days/${date}/confirm`),
  cancelConfirm: (id: number, date: string) =>
    api.post<{ success: boolean }>(`/weekly-plans/${id}/days/${date}/cancel-confirm`),
}

export const shoppingListApi = {
  list: () => api.get<ShoppingListSummary[]>('/shopping-lists'),
  generate: (payload: { weekly_plan_id: number; name?: string }) =>
    api.post<ShoppingList>('/shopping-lists/generate', payload),
  getById: (id: number) => api.get<ShoppingList>(`/shopping-lists/${id}`),
  addItem: (id: number, payload: { ingredient_name: string; display_amount?: string }) =>
    api.post<ShoppingList>(`/shopping-lists/${id}/items`, payload),
  updateItem: (id: number, itemId: number, payload: { checked?: boolean; display_amount?: string }) =>
    api.patch<ShoppingList>(`/shopping-lists/${id}/items/${itemId}`, payload),
  deleteItem: (id: number, itemId: number) => api.delete<ShoppingList>(`/shopping-lists/${id}/items/${itemId}`)
}

export const mealChatApi = {
  createSession: () => api.post<MealChatSession>('/meal-chat/sessions'),
  getSession: (sessionId: string) => api.get<MealChatSession>(`/meal-chat/sessions/${sessionId}`),
  generateSession: (sessionId: string) =>
    longApi.post<MealChatSession>(`/meal-chat/sessions/${sessionId}/generate`),
  updatePresentation: (sessionId: string, overlayState: 'hidden' | 'result') =>
    api.post<MealChatSession>(`/meal-chat/sessions/${sessionId}/presentation`, {
      overlay_state: overlayState
    }),
  sendMessage: (sessionId: string, content: string) =>
    longApi.post<MealChatSession>(`/meal-chat/sessions/${sessionId}/messages`, { content })
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

// ============ Intake Tracking ============

export interface IntakeRecord {
  id: number
  date: string
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  recipe_id?: number | null
  recipe_name?: string | null
  custom_food_name?: string | null
  actual_calories: number
  actual_protein: number
  actual_carbs: number
  actual_fat: number
  portion_size: number
  source: 'manual' | 'plan' | 'auto'
  source_plan_day_id?: number | null
  rating?: number | null
  note?: string | null
  created_at: string
}

export interface DailyIntakeSummary {
  date: string
  total_calories: number
  total_protein: number
  total_carbs: number
  total_fat: number
  meal_count: number
  records: IntakeRecord[]
}

export interface NutritionTarget {
  calories: number
  protein: number
  carbs: number
  fat: number
}

export interface DailyDashboard {
  date: string
  target: NutritionTarget
  actual: NutritionTarget
  remaining: NutritionTarget
  meals_logged: number
  completion_rate: number
}

export interface WeeklySummaryDay {
  date: string
  calories: number
  protein: number
  carbs: number
  fat: number
  meal_count: number
  on_target: boolean
}

export interface WeeklyDashboard {
  days: WeeklySummaryDay[]
  avg_calories: number
  avg_protein: number
  target_adherence_rate: number
}

export interface WeightLog {
  id: number
  date: string
  weight: number
  body_fat_pct?: number | null
  note?: string | null
}

export interface Reminder {
  id: number
  type: string
  title: string
  message: string
  severity: 'info' | 'warning' | 'critical'
  is_read: boolean
  created_at: string
}

export interface TrendPoint {
  period: string
  avg_calories: number
  avg_protein: number
  avg_carbs: number
  avg_fat: number
  adherence_rate: number
}

export interface ReportResponse {
  report_type: string
  html: string
  generated_at: string
}

export interface InsightResponse {
  insight: string
  generated_at: string
}

export const intakeApi = {
  logMeal: (payload: {
    date: string
    meal_type: string
    recipe_id?: number
    custom_food_name?: string
    actual_calories?: number
    actual_protein?: number
    actual_carbs?: number
    actual_fat?: number
    portion_size?: number
    rating?: number
  }) => api.post<IntakeRecord>('/intake/records', payload),

  quickLog: (payload: { date: string; recipe_id: number; portion_size?: number; meal_type?: string }) =>
    api.post<IntakeRecord>('/intake/quick-log', payload),

  getDaily: (recordDate: string) =>
    api.get<DailyIntakeSummary>(`/intake/records/${recordDate}`),

  updateRecord: (id: number, payload: { portion_size?: number; rating?: number; note?: string }) =>
    api.patch<IntakeRecord>(`/intake/records/${id}`, payload),

  deleteRecord: (id: number) =>
    api.delete(`/intake/records/${id}`)
}

export const dashboardApi = {
  getDaily: (summaryDate: string) =>
    api.get<DailyDashboard>(`/dashboard/daily/${summaryDate}`),

  getWeekly: () =>
    api.get<WeeklyDashboard>('/dashboard/weekly'),

  getTrends: (months?: number) =>
    api.get<TrendPoint[]>('/dashboard/trends', { params: { months } }),

  logWeight: (payload: { date: string; weight: number; body_fat_pct?: number }) =>
    api.post<WeightLog>('/dashboard/weight', payload),

  getWeight: () =>
    api.get<WeightLog[]>('/dashboard/weight'),

  getReminders: () =>
    api.get<Reminder[]>('/dashboard/reminders'),

  dismissReminder: (id: number) =>
    api.patch(`/dashboard/reminders/${id}/dismiss`),

  getInsights: () =>
    api.get<InsightResponse>('/dashboard/insights'),

  generateReport: (payload: { report_type: string; start_date?: string }) =>
    api.post<ReportResponse>('/dashboard/report', payload)
}

export default api
