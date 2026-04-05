import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const routerPush = vi.fn()
const authMe = vi.fn()
const hydrateFromAuthUser = vi.fn()
const resetProfile = vi.fn()

vi.mock('@/router', () => ({
  default: {
    push: routerPush
  }
}))

vi.mock('@/api', () => ({
  authApi: {
    me: authMe
  }
}))

vi.mock('@/api/config', () => ({
  AUTH_API_URL: '/api/auth'
}))

vi.mock('@/stores/user', () => ({
  useUserStore: () => ({
    hydrateFromAuthUser,
    resetProfile
  })
}))

type StorageShape = {
  getItem: (key: string) => string | null
  setItem: (key: string, value: string) => void
  removeItem: (key: string) => void
  clear: () => void
}

function createStorage(): StorageShape {
  const store = new Map<string, string>()

  return {
    getItem: (key) => store.get(key) ?? null,
    setItem: (key, value) => {
      store.set(key, value)
    },
    removeItem: (key) => {
      store.delete(key)
    },
    clear: () => {
      store.clear()
    }
  }
}

function createJwt(exp: number) {
  const payload = Buffer.from(JSON.stringify({ exp }), 'utf8').toString('base64url')
  return `header.${payload}.signature`
}

describe('useAuthStore', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
    setActivePinia(createPinia())

    const storage = createStorage()
    vi.stubGlobal('localStorage', storage)
  })

  it('clears an expired cached token before requesting the current user', async () => {
    const expiredToken = createJwt(Math.floor(Date.now() / 1000) - 60)
    localStorage.setItem('token', expiredToken)

    const { useAuthStore } = await import('./auth')
    const store = useAuthStore()

    await Promise.resolve()

    expect(store.token).toBeNull()
    expect(store.isAuthenticated).toBe(false)
    expect(localStorage.getItem('token')).toBeNull()
    expect(authMe).not.toHaveBeenCalled()
  })
})
