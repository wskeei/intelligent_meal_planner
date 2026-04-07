export type SafeStorage = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>

function resolveStorage(storage?: SafeStorage | null) {
  if (storage) return storage

  if (typeof globalThis === 'undefined' || !('localStorage' in globalThis)) {
    return null
  }

  return globalThis.localStorage
}

function toFiniteNumber(value: unknown) {
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : null
  }

  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
  }

  return null
}

export function resolveIntlLocale(locale: string) {
  if (locale === 'zh') return 'zh-CN'
  if (locale === 'en') return 'en-US'
  return locale
}

export function safeStorageGet(key: string, storage?: SafeStorage | null) {
  const target = resolveStorage(storage)
  if (!target) return null

  try {
    return target.getItem(key)
  } catch {
    return null
  }
}

export function safeStorageSet(key: string, value: string, storage?: SafeStorage | null) {
  const target = resolveStorage(storage)
  if (!target) return false

  try {
    target.setItem(key, value)
    return true
  } catch {
    return false
  }
}

export function safeStorageRemove(key: string, storage?: SafeStorage | null) {
  const target = resolveStorage(storage)
  if (!target) return false

  try {
    target.removeItem(key)
    return true
  } catch {
    return false
  }
}

export function formatNumberValue(
  value: unknown,
  locale: string,
  fractionDigits = 0,
  fallback = '--'
) {
  const parsed = toFiniteNumber(value)
  if (parsed === null) return fallback

  try {
    return new Intl.NumberFormat(resolveIntlLocale(locale), {
      minimumFractionDigits: fractionDigits,
      maximumFractionDigits: fractionDigits
    }).format(parsed)
  } catch {
    return fallback
  }
}

export function formatCurrencyAmount(
  value: unknown,
  locale: string,
  fractionDigits = 1,
  fallback = '--'
) {
  const parsed = toFiniteNumber(value)
  if (parsed === null) return fallback

  try {
    return new Intl.NumberFormat(resolveIntlLocale(locale), {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: fractionDigits,
      maximumFractionDigits: fractionDigits
    }).format(parsed)
  } catch {
    return fallback
  }
}

export function formatDisplayDate(
  value: string | number | Date | null | undefined,
  locale: string,
  fallback = '--'
) {
  if (value === null || value === undefined || value === '') return fallback

  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return fallback

  try {
    return new Intl.DateTimeFormat(resolveIntlLocale(locale), {
      dateStyle: 'medium'
    }).format(date)
  } catch {
    return fallback
  }
}

export function splitAndTrimList(raw: string, separator = ',') {
  if (!raw.trim()) return []

  return raw
    .split(separator)
    .map((item) => item.trim())
    .filter(Boolean)
}

export function compactList(
  items: string[],
  options?: {
    limit?: number
    separator?: string
    overflowLabel?: (count: number) => string
  }
) {
  const normalized = items.map((item) => item.trim()).filter(Boolean)
  if (!normalized.length) return ''

  const limit = options?.limit ?? normalized.length
  const separator = options?.separator ?? ', '
  const visibleItems = normalized.slice(0, limit)
  const overflowCount = normalized.length - visibleItems.length

  if (overflowCount <= 0) {
    return visibleItems.join(separator)
  }

  const overflow = options?.overflowLabel?.(overflowCount) ?? `+${overflowCount}`
  return `${visibleItems.join(separator)} ${overflow}`.trim()
}
