import { describe, expect, it } from 'vitest'

import {
  compactList,
  formatCurrencyAmount,
  formatDisplayDate,
  formatNumberValue,
  safeStorageGet,
  safeStorageRemove,
  safeStorageSet,
  splitAndTrimList
} from './resilience'

function createStorage(overrides?: Partial<Storage>) {
  const store = new Map<string, string>()

  return {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => {
      store.set(key, value)
    },
    removeItem: (key: string) => {
      store.delete(key)
    },
    ...overrides
  } satisfies Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>
}

describe('resilience utilities', () => {
  it('returns null instead of throwing when storage reads are blocked', () => {
    const storage = createStorage({
      getItem: () => {
        throw new Error('storage blocked')
      }
    })

    expect(safeStorageGet('token', storage)).toBeNull()
  })

  it('returns false instead of throwing when storage writes are blocked', () => {
    const storage = createStorage({
      setItem: () => {
        throw new Error('storage blocked')
      },
      removeItem: () => {
        throw new Error('storage blocked')
      }
    })

    expect(safeStorageSet('token', 'abc', storage)).toBe(false)
    expect(safeStorageRemove('token', storage)).toBe(false)
  })

  it('formats invalid dates with a fallback placeholder', () => {
    expect(formatDisplayDate('not-a-date', 'en')).toBe('--')
  })

  it('formats invalid currency values with a fallback placeholder', () => {
    expect(formatCurrencyAmount(undefined, 'zh')).toBe('--')
    expect(formatCurrencyAmount('oops', 'en')).toBe('--')
  })

  it('formats finite numeric values safely', () => {
    expect(formatNumberValue('1234.56', 'en', 0)).toBe('1,235')
    expect(formatCurrencyAmount(18.5, 'zh')).toMatch(/18\.5/)
  })

  it('splits comma-separated query values and removes empty fragments', () => {
    expect(splitAndTrimList(' eggs,  ,milk , tofu ')).toEqual(['eggs', 'milk', 'tofu'])
  })

  it('compacts long labels while preserving the visible prefix', () => {
    expect(
      compactList(['早餐燕麦碗', '午餐鸡胸肉沙拉', '晚餐番茄意面', '夜宵酸奶'], {
        limit: 3,
        separator: ' / ',
        overflowLabel: (count) => `+${count}`
      })
    ).toBe('早餐燕麦碗 / 午餐鸡胸肉沙拉 / 晚餐番茄意面 +1')
  })
})
