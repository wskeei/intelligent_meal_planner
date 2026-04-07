import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const srcDir = dirname(fileURLToPath(import.meta.url))

function readSource(relativePath: string) {
  return readFileSync(resolve(srcDir, relativePath), 'utf8')
}

describe('frontend audit regressions', () => {
  it('keeps dark-mode emphasis text readable on dark emphasis surfaces', () => {
    const tokens = readSource('./assets/main.css')

    expect(tokens).not.toMatch(/@media \(prefers-color-scheme: dark\)[\s\S]*--color-text-emphasis:\s*var\(--color-text-inverse\)/)
    expect(tokens).not.toMatch(/@media \(prefers-color-scheme: dark\)[\s\S]*--color-text-emphasis-muted:\s*color-mix\(in srgb, var\(--color-text-inverse\)/)
  })

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

  it('uses touch-safe secondary navigation and responsive recipe dialog sizing', () => {
    const appView = readSource('./App.vue')
    const recipesView = readSource('./views/RecipesView.vue')

    expect(appView).toContain('<el-dropdown trigger="click" @command="handleMoreCommand">')
    expect(appView).toContain('void router.push(command)')
    expect(recipesView).not.toContain('window.innerWidth')
    expect(recipesView).toContain("const dialogWidth = 'min(680px, calc(100vw - 24px))'")
  })

  it('moves residual overlay and banner surfaces onto semantic tokens', () => {
    const registerView = readSource('./views/RegisterView.vue')
    const profileView = readSource('./views/ProfileView.vue')
    const generationOverlay = readSource('./components/meal-chat/MealChatGenerationOverlay.vue')
    const resultOverlay = readSource('./components/meal-chat/MealChatResultOverlay.vue')

    expect(registerView).toContain('background: var(--color-surface-muted);')
    expect(registerView).not.toContain('background: #f7faf8;')

    expect(profileView).toContain("const progressColor = ref('var(--color-accent)')")
    expect(profileView).not.toContain("#8ba284")

    expect(generationOverlay).toContain('background: var(--gradient-overlay-backdrop);')
    expect(generationOverlay).toContain('background: var(--color-overlay-surface);')
    expect(generationOverlay).not.toMatch(/#f7faf8|rgba\(126, 216, 139|rgba\(245, 247, 242|rgba\(47, 143, 81/)

    expect(resultOverlay).toContain('linear-gradient(180deg, var(--color-backdrop-scrim)')
    expect(resultOverlay).not.toContain('rgba(11, 16, 14, 0.28)')
  })
})
