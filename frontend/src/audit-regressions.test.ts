import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const srcDir = dirname(fileURLToPath(import.meta.url))

function readSource(relativePath: string) {
  return readFileSync(resolve(srcDir, relativePath), 'utf8')
}

describe('frontend audit regressions', () => {
  it('uses token-driven, neutral-first hero and status surfaces on key pages', () => {
    const homeView = readSource('./views/HomeView.vue')
    const profileView = readSource('./views/ProfileView.vue')
    const statusPanel = readSource('./components/meal-chat/MealChatStatusPanel.vue')

    expect(homeView).toContain('var(--gradient-hero)')
    expect(homeView).toContain('var(--gradient-feature)')
    expect(homeView).not.toMatch(/#10251a|#173728|#1f5137|#f6fff7|#eef8f0/)
    expect(homeView).not.toContain('rgba(34, 197, 94')

    expect(profileView).toContain('var(--gradient-emphasis)')
    expect(profileView).toContain('--color-accent')
    expect(profileView).not.toContain('color="#4ade80"')
    expect(profileView).not.toMatch(/#10251a|#173728|#214c35|#f0fff5/)

    expect(statusPanel).toContain('var(--gradient-surface)')
    expect(statusPanel).toContain('var(--gradient-emphasis)')
    expect(statusPanel).not.toMatch(/#ffffff|#f6faf7|#166534|#effff5/)
    expect(statusPanel).not.toContain('rgba(34, 197, 94')
  })

  it('keeps meal chat status actions at or above the 44px touch target', () => {
    const statusPanel = readSource('./components/meal-chat/MealChatStatusPanel.vue')

    expect(statusPanel).toContain('.status-primary-action :deep(.el-button)')
    expect(statusPanel).toContain('min-height: 44px;')
    expect(statusPanel).not.toContain('min-height: 42px;')
  })
})
