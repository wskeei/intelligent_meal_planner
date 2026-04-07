import axios from 'axios'
import { defineStore } from 'pinia'
import { ref } from 'vue'

import { authApi } from '@/api'
import { AUTH_API_URL } from '@/api/config'
import router from '@/router'
import { useUserStore } from '@/stores/user'
import { safeStorageGet, safeStorageRemove, safeStorageSet } from '@/utils/resilience'

function decodeJwtPayload(token: string) {
  const parts = token.split('.')
  if (parts.length !== 3) return null

  try {
    const normalizedPayload = parts[1].replace(/-/g, '+').replace(/_/g, '/')
    const padding = '='.repeat((4 - (normalizedPayload.length % 4 || 4)) % 4)
    const decodedPayload = globalThis.atob(`${normalizedPayload}${padding}`)
    return JSON.parse(decodedPayload) as { exp?: number }
  } catch {
    return null
  }
}

function readStoredToken() {
  const storedToken = safeStorageGet('token')
  if (!storedToken) return null

  const payload = decodeJwtPayload(storedToken)
  if (!payload || typeof payload.exp !== 'number' || payload.exp * 1000 <= Date.now()) {
    safeStorageRemove('token')
    return null
  }

  return storedToken
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(readStoredToken())
  const user = ref<any>(null)
  const isAuthenticated = ref(Boolean(token.value))

  async function requestCurrentUser() {
    if (!token.value) {
      throw new Error('missing_token')
    }

    const { data } = await authApi.me()
    user.value = data
    useUserStore().hydrateFromAuthUser(data)
    return data
  }

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
      safeStorageSet('token', data.access_token)
      isAuthenticated.value = true

      await requestCurrentUser()
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
      await requestCurrentUser()
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        logout()
        return
      }
      throw error
    }
  }

  function logout() {
    token.value = null
    user.value = null
    isAuthenticated.value = false
    safeStorageRemove('token')
    useUserStore().resetProfile()
    router.push('/login')
  }

  if (token.value) {
    void fetchUser().catch((error) => {
      console.error('Fetch current user failed', error)
    })
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
