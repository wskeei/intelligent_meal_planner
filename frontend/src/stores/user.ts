import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { authApi } from '@/api'

export interface UserProfile {
  username: string
  name: string
  age: number | null
  gender: 'male' | 'female' | null
  height: number | null
  weight: number | null
  activityLevel: 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active' | null
  goal: 'lose_weight' | 'gain_muscle' | 'maintain' | 'healthy'
}

const emptyProfile = (): UserProfile => ({
  username: '',
  name: '',
  age: null,
  gender: null,
  height: null,
  weight: null,
  activityLevel: null,
  goal: 'healthy'
})

export const useUserStore = defineStore('user', () => {
  const profile = ref<UserProfile>(emptyProfile())

  const profileComplete = computed(() =>
    Boolean(
      profile.value.gender &&
        profile.value.age &&
        profile.value.height &&
        profile.value.weight &&
        profile.value.activityLevel
    )
  )

  const targetCalories = computed(() => {
    const { weight, height, age, gender, activityLevel, goal } = profile.value
    if (!weight || !height || !age || !gender || !activityLevel) return 0

    const base = 10 * weight + 6.25 * height - 5 * age
    const bmr = gender === 'male' ? base + 5 : base - 161
    const multiplierMap: Record<NonNullable<UserProfile['activityLevel']>, number> = {
      sedentary: 1.2,
      light: 1.375,
      moderate: 1.55,
      active: 1.725,
      very_active: 1.9
    }
    const tdee = Math.round(bmr * multiplierMap[activityLevel])

    switch (goal) {
      case 'lose_weight':
        return tdee - 500
      case 'gain_muscle':
        return tdee + 300
      default:
        return tdee
    }
  })

  const targetMacros = computed(() => {
    const calories = targetCalories.value
    if (!calories) {
      return { protein: 0, carbs: 0, fat: 0 }
    }

    return {
      protein: Math.round((calories * 0.3) / 4),
      carbs: Math.round((calories * 0.4) / 4),
      fat: Math.round((calories * 0.3) / 9)
    }
  })

  function hydrateFromAuthUser(user: any) {
    if (!user) return
    profile.value = {
      username: user.username ?? '',
      name: user.username ?? '',
      age: user.age ?? null,
      gender: user.gender ?? null,
      height: user.height ?? null,
      weight: user.weight ?? null,
      activityLevel: user.activity_level ?? null,
      goal: user.health_goal ?? 'healthy'
    }
  }

  async function saveProfile(patch: Partial<UserProfile>) {
    const payload = {
      age: patch.age,
      gender: patch.gender,
      height: patch.height,
      weight: patch.weight,
      activity_level: patch.activityLevel,
      health_goal: patch.goal
    }
    const { data } = await authApi.updateProfile(payload)
    hydrateFromAuthUser(data)
    return data
  }

  function resetProfile() {
    profile.value = emptyProfile()
  }

  return {
    profile,
    profileComplete,
    targetCalories,
    targetMacros,
    hydrateFromAuthUser,
    saveProfile,
    resetProfile
  }
})
