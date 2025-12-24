import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

export interface UserProfile {
    name: string
    age: number
    gender: 'male' | 'female'
    height: number // cm
    weight: number // kg
    activityLevel: 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active'
    goal: 'lose_weight' | 'gain_muscle' | 'maintain' | 'healthy'
    dietaryRestrictions: string[]
}

export const useUserStore = defineStore('user', () => {
    // Default State
    const profile = ref<UserProfile>({
        name: 'User',
        age: 25,
        gender: 'male',
        height: 175,
        weight: 70,
        activityLevel: 'moderate',
        goal: 'maintain',
        dietaryRestrictions: []
    })

    // Load from LocalStorage
    if (localStorage.getItem('userProfile')) {
        try {
            profile.value = JSON.parse(localStorage.getItem('userProfile')!)
        } catch (e) {
            console.error('Failed to load profile', e)
        }
    }

    // Auto-save to LocalStorage
    watch(profile, (newVal) => {
        localStorage.setItem('userProfile', JSON.stringify(newVal))
    }, { deep: true })

    // Computed: BMR (Basal Metabolic Rate) - Mifflin-St Jeor Equation
    const bmr = computed(() => {
        const { weight, height, age, gender } = profile.value
        let base = (10 * weight) + (6.25 * height) - (5 * age)
        return gender === 'male' ? base + 5 : base - 161
    })

    // Computed: TDEE (Total Daily Energy Expenditure)
    const tdee = computed(() => {
        const multipliers: Record<string, number> = {
            sedentary: 1.2,
            light: 1.375,
            moderate: 1.55,
            active: 1.725,
            very_active: 1.9
        }
        return Math.round(bmr.value * (multipliers[profile.value.activityLevel] || 1.2))
    })

    // Computed: Target Calories based on Goal
    const targetCalories = computed(() => {
        const t = tdee.value
        switch (profile.value.goal) {
            case 'lose_weight': return t - 500
            case 'gain_muscle': return t + 300
            case 'healthy': return t
            default: return t
        }
    })

    // Computed: Macros Targets
    const targetMacros = computed(() => {
        const cals = targetCalories.value
        // Simple breakdown: Protein 30%, Fat 30%, Carbs 40% (approx)
        return {
            protein: Math.round((cals * 0.3) / 4),
            fat: Math.round((cals * 0.3) / 9),
            carbs: Math.round((cals * 0.4) / 4)
        }
    })

    function updateProfile(newProfile: Partial<UserProfile>) {
        profile.value = { ...profile.value, ...newProfile }
    }

    return {
        profile,
        bmr,
        tdee,
        targetCalories,
        targetMacros,
        updateProfile
    }
})
