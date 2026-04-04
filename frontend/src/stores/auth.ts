import axios from 'axios'
import { defineStore } from 'pinia'
import { ref } from 'vue'

import { authApi } from '@/api'
import { AUTH_API_URL } from '@/api/config'
import router from '@/router'
import { useUserStore } from '@/stores/user'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<any>(null)
  const isAuthenticated = ref(Boolean(token.value))

  async function login(
    username: string,
    password: string,
    options?: {
      redirectTo?: string
    }
  ) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)

    try {
      const { data } = await axios.post(`${AUTH_API_URL}/token`, formData)
      token.value = data.access_token
      localStorage.setItem('token', data.access_token)
      isAuthenticated.value = true

      await fetchUser()
      router.push(options?.redirectTo ?? '/')
      return { ok: true as const, reason: null }
    } catch (error) {
      console.error('Login failed', error)
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        return { ok: false as const, reason: 'invalid_credentials' as const }
      }
      return { ok: false as const, reason: 'request_failed' as const }
    }
  }

  async function register(payload: any) {
    try {
      await axios.post(`${AUTH_API_URL}/register`, payload)
      return true
    } catch (error) {
      console.error('Registration failed', error)
      return false
    }
  }

  async function fetchUser() {
    if (!token.value) return

    try {
      const { data } = await authApi.me()
      user.value = data
      useUserStore().hydrateFromAuthUser(data)
    } catch (_error) {
      logout()
    }
  }

  function logout() {
    token.value = null
    user.value = null
    isAuthenticated.value = false
    localStorage.removeItem('token')
    useUserStore().resetProfile()
    router.push('/login')
  }

  if (token.value) {
    void fetchUser()
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
