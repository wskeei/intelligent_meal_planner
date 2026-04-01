import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { authApi } from '@/api'

export interface UserProfile {
  username: string
  age: number | null
  gender: 'male' | 'female' | null
  height: number | null
  weight: number | null
  activityLevel: 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active' | null
  goal: 'lose_weight' | 'gain_muscle' | 'maintain' | 'healthy'
}

const emptyProfile = (): UserProfile => ({
  username: '',
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

  function hydrateFromAuthUser(user: any) {
    if (!user) return
    profile.value = {
      username: user.username ?? '',
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
    hydrateFromAuthUser,
    saveProfile,
    resetProfile
  }
})
