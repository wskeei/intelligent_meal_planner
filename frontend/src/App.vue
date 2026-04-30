<template>
  <el-config-provider :locale="locale === 'zh' ? zhCn : en">
    <div class="layout">
      <header class="topbar">
        <div class="container topbar-inner">
          <!-- Brand -->
          <router-link to="/" class="brand">
            <div class="logo-icon">
              <el-icon :size="22" class="brand-icon"><Food /></el-icon>
            </div>
            <div>
              <span class="brand-text">{{ $t('app.brand') }}</span>
              <p class="brand-subtitle">{{ $t('app.tagline') }}</p>
            </div>
          </router-link>

          <!-- Primary nav (inline, visible on auth pages only) -->
          <nav v-if="showPrimaryNav" class="primary-nav">
            <router-link to="/meal-plan" class="nav-item" active-class="active">
              <el-icon><MagicStick /></el-icon>
              <span>{{ $t('nav.planner') }}</span>
            </router-link>
            <router-link to="/weekly-plan" class="nav-item" active-class="active">
              <el-icon><Calendar /></el-icon>
              <span>{{ $t('nav.weekly_plan') }}</span>
            </router-link>
            <router-link to="/recipes" class="nav-item" active-class="active">
              <el-icon><Food /></el-icon>
              <span>{{ $t('nav.recipes') }}</span>
            </router-link>
            <router-link to="/history" class="nav-item" active-class="active">
              <el-icon><Clock /></el-icon>
              <span>{{ $t('nav.history') }}</span>
            </router-link>
            <router-link to="/profile" class="nav-item" active-class="active">
              <el-icon><User /></el-icon>
              <span>{{ $t('nav.profile') }}</span>
            </router-link>
          </nav>

          <!-- Utility nav -->
          <div class="utility-nav">
            <!-- Shopping cart with badge -->
            <template v-if="showPrimaryNav">
              <router-link to="/shopping-list" class="utility-link cart-link" :aria-label="$t('nav.shopping_cart')">
                <el-badge :value="shoppingListCount" :hidden="shoppingListCount === 0" :max="9">
                  <el-icon :size="20"><ShoppingCart /></el-icon>
                </el-badge>
              </router-link>
            </template>

            <!-- Language switcher -->
            <el-dropdown @command="handleCommand">
              <span class="utility-link">
                {{ locale === 'zh' ? '中文' : 'English' }}
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="zh">中文</el-dropdown-item>
                  <el-dropdown-item command="en">English</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>

            <!-- Logout -->
            <button v-if="showPrimaryNav" class="utility-link" type="button" @click="handleLogout">
              {{ $t('nav.exit') }}
            </button>
          </div>
        </div>
      </header>

      <main class="main-content" :class="{ 'with-mobile-nav': showPrimaryNav }">
        <div class="container">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </main>

      <footer class="footer">
        <div class="container footer-inner">
          <p>{{ $t('app.footer') }}</p>
        </div>
      </footer>

      <nav v-if="showPrimaryNav" class="mobile-nav">
        <router-link to="/meal-plan" class="mobile-nav-item" active-class="active">
          <el-icon><MagicStick /></el-icon>
          <span>{{ $t('nav.planner') }}</span>
        </router-link>
        <router-link to="/weekly-plan" class="mobile-nav-item" active-class="active">
          <el-icon><Calendar /></el-icon>
          <span>{{ $t('nav.weekly_plan') }}</span>
        </router-link>
        <router-link to="/recipes" class="mobile-nav-item" active-class="active">
          <el-icon><Food /></el-icon>
          <span>{{ $t('nav.recipes') }}</span>
        </router-link>
        <router-link to="/history" class="mobile-nav-item" active-class="active">
          <el-icon><Clock /></el-icon>
          <span>{{ $t('nav.history') }}</span>
        </router-link>
        <router-link to="/profile" class="mobile-nav-item" active-class="active">
          <el-icon><User /></el-icon>
          <span>{{ $t('nav.profile') }}</span>
        </router-link>
      </nav>
    </div>
  </el-config-provider>
</template>

<script setup lang="ts">
import { ArrowDown, Calendar, Clock, Food, MagicStick, ShoppingCart, User } from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import en from 'element-plus/dist/locale/en.mjs'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { useShoppingStore } from '@/stores/shopping'

const { locale } = useI18n()
const auth = useAuthStore()
const route = useRoute()

const authPageNames = ['login', 'register']
const showPrimaryNav = computed(() => !authPageNames.includes(route.name as string))

const shoppingStore = useShoppingStore()
const shoppingListCount = computed(() => shoppingStore.listCount)

onMounted(() => {
  if (showPrimaryNav.value) {
    shoppingStore.loadLists()
  }
})

function handleLogout() {
  auth.logout()
}

function handleCommand(command: string) {
  locale.value = command
  localStorage.setItem('locale', command)
}
</script>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--color-background);
}

.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.topbar,
.footer {
  background: var(--color-bg-elevated);
  backdrop-filter: blur(8px);
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 40;
  border-bottom: 1px solid var(--color-border-soft);
}

.topbar-inner {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  min-height: 72px;
}

.footer-inner {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  border-radius: 16px;
  transition:
    transform 180ms ease,
    opacity 180ms ease;
}

.logo-icon {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--color-primary-dark), var(--color-primary));
  box-shadow: inset 0 1px 0 color-mix(in srgb, var(--color-accent-contrast) 22%, transparent);
}

.brand-icon {
  color: var(--color-accent-contrast);
}

.brand-text {
  display: block;
  color: var(--color-secondary);
  font-size: 1.08rem;
  font-weight: 800;
  line-height: 1.1;
}

.brand-subtitle,
.footer p {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 0.86rem;
}

.primary-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
  flex: 1;
  justify-content: center;
}

.utility-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.nav-item,
.utility-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  padding: 10px 14px;
  border-radius: 14px;
  color: var(--color-text-secondary);
  font-weight: 600;
  transition:
    background-color 180ms ease,
    color 180ms ease,
    transform 180ms ease;
}

.brand:hover,
.brand:focus-visible,
.nav-item:hover,
.utility-link:hover,
.mobile-nav-item:hover {
  transform: translateY(-1px);
}

.nav-item:hover,
.utility-link:hover,
.mobile-nav-item:hover {
  background: color-mix(in srgb, var(--color-accent-soft) 70%, transparent);
  color: var(--color-secondary);
}

.brand:focus-visible,
.nav-item:focus-visible,
.utility-link:focus-visible,
.mobile-nav-item:focus-visible {
  box-shadow: var(--focus-ring);
}

.nav-item.active,
.mobile-nav-item.active {
  background: var(--color-accent-soft);
  color: var(--color-primary-dark);
}

.cart-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  padding: 0;
  border-radius: 12px;
  color: var(--color-text-secondary);
  transition: background-color 180ms ease, color 180ms ease;
}

.cart-link:hover {
  background: color-mix(in srgb, var(--color-accent-soft) 70%, transparent);
  color: var(--color-secondary);
}

.main-content {
  flex: 1;
  padding: 28px 0;
}

.footer {
  padding: 20px 0;
  border-top: 1px solid var(--color-border-soft);
}

.mobile-nav {
  position: sticky;
  bottom: 0;
  z-index: 45;
  display: none;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 6px;
  padding: 10px 12px calc(10px + env(safe-area-inset-bottom));
  background: color-mix(in srgb, var(--color-surface-raised) 94%, transparent);
  border-top: 1px solid var(--color-border-soft);
  backdrop-filter: blur(10px);
}

.mobile-nav-item {
  display: grid;
  justify-items: center;
  gap: 4px;
  min-height: 52px;
  padding: 8px 10px;
  border-radius: 14px;
  color: var(--color-text-secondary);
  font-size: 0.78rem;
  font-weight: 600;
  transition:
    background-color 180ms ease,
    color 180ms ease,
    transform 180ms ease;
}

@media (max-width: 720px) {
  .primary-nav {
    display: none;
  }

  .brand-subtitle {
    display: none;
  }

  .main-content.with-mobile-nav {
    padding-bottom: 92px;
  }

  .mobile-nav {
    display: grid;
  }
}

@media (max-width: 560px) {
  .topbar-inner {
    align-items: flex-start;
    padding-top: 14px;
    padding-bottom: 14px;
  }

  .topbar-inner,
  .utility-nav {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
