const defaultApiBaseUrl = '/api'

export const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() || defaultApiBaseUrl

export const AUTH_API_URL = `${API_BASE_URL}/auth`
