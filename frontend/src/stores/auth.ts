import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import router from '@/router'

// API base
const API_URL = 'http://localhost:8000/api/auth'

export const useAuthStore = defineStore('auth', () => {
    const token = ref<string | null>(localStorage.getItem('token'))
    const user = ref<any>(null)
    const isAuthenticated = ref(!!token.value)

    async function login(username: string, password: string) {
        const formData = new FormData()
        formData.append('username', username)
        formData.append('password', password)

        try {
            const { data } = await axios.post(`${API_URL}/token`, formData)
            token.value = data.access_token
            localStorage.setItem('token', data.access_token)
            isAuthenticated.value = true

            // Load user profile
            await fetchUser()

            router.push('/')
            return true
        } catch (error) {
            console.error('Login failed', error)
            return false
        }
    }

    async function register(payload: any) {
        try {
            await axios.post(`${API_URL}/register`, payload)
            return true
        } catch (error) {
            console.error('Registration failed', error)
            return false
        }
    }

    async function fetchUser() {
        if (!token.value) return
        try {
            const { data } = await axios.get(`${API_URL}/me`, {
                headers: { Authorization: `Bearer ${token.value}` }
            })
            user.value = data
        } catch (e) {
            logout()
        }
    }

    function logout() {
        token.value = null
        user.value = null
        isAuthenticated.value = false
        localStorage.removeItem('token')
        router.push('/login')
    }

    return {
        token,
        user,
        isAuthenticated,
        login,
        register,
        logout,
        fetchUser
    }
})
