<template>
  <el-config-provider :locale="locale === 'zh' ? zhCn : en" >
    <div class="layout">
      <!-- Top Navigation Bar -->
      <nav class="navbar" v-if="showNavbar">
        <div class="container navbar-content">
          <div class="brand">
            <div class="logo-icon">
              <el-icon :size="24" color="white"><Food /></el-icon>
            </div>
            <span class="brand-text">FitPlan AI</span>
          </div>

          <div class="nav-links">
            <router-link to="/" class="nav-item" active-class="active">
              <el-icon><ODOMETER /></el-icon>
              <span>{{ $t('nav.dashboard') }}</span>
            </router-link>
            <router-link to="/meal-plan" class="nav-item" active-class="active">
              <el-icon><MagicStick /></el-icon>
              <span>{{ $t('nav.planner') }}</span>
            </router-link>
            <router-link to="/shopping-list" class="nav-item" active-class="active">
              <el-icon><ShoppingCart /></el-icon>
              <span>{{ $t('nav.shopping') }}</span>
            </router-link>
            <router-link to="/recipes" class="nav-item" active-class="active">
              <el-icon><Dish /></el-icon>
              <span>{{ $t('nav.recipes') }}</span>
            </router-link>
             <router-link to="/profile" class="nav-item" active-class="active">
              <el-icon><User /></el-icon>
              <span>{{ $t('nav.profile') }}</span>
            </router-link>
            <a href="#" class="nav-item" @click.prevent="handleLogout">
              <el-icon><SwitchButton /></el-icon>
              <span>{{ $t('nav.exit') }}</span>
            </a>
            <el-dropdown @command="handleCommand">
              <span class="el-dropdown-link nav-item">
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
          </div>
        </div>
      </nav>

      <!-- Main Content Area -->
      <main class="main-content">
        <div class="container">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </main>

      <!-- Footer -->
      <footer class="footer">
        <div class="container">
          <p>© 2024 Intelligent Meal Planner. Powered by Multi-Agent AI.</p>
        </div>
      </footer>
    </div>
  </el-config-provider>
</template>

<script setup lang="ts">
import { Food, Odometer, MagicStick, ShoppingCart, Dish, User, SwitchButton, ArrowDown } from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import en from 'element-plus/dist/locale/en.mjs'
import { useAuthStore } from '@/stores/auth'
import { useRouter, useRoute } from 'vue-router'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const handleLogout = () => {
  auth.logout()
}

const handleCommand = (command: string) => {
  locale.value = command
}

// Hide navbar on auth pages
const showNavbar = computed(() => !['login', 'register'].includes(route.name as string))
</script>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--color-background);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  width: 100%;
}

/* Navbar Styling */
.navbar {
  height: var(--header-height);
  background-color: var(--color-surface);
  border-bottom: 1px solid #e2e8f0;
  position: sticky;
  top: 0;
  z-index: 50;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(8px);
}

.navbar-content {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 6px -1px rgba(74, 222, 128, 0.3);
}

.brand-text {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-secondary);
  letter-spacing: -0.025em;
}

.nav-links {
  display: flex;
  gap: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-weight: 500;
  font-size: 0.9rem;
  transition: all 0.2s ease;
}

.nav-item:hover {
  background-color: #f1f5f9;
  color: var(--color-secondary);
}

.nav-item.active {
  background-color: #f0fdf4;
  color: var(--color-primary-dark);
}

/* Main Content */
.main-content {
  flex: 1;
  padding: 32px 0;
}

/* Footer */
.footer {
  padding: 24px 0;
  border-top: 1px solid #e2e8f0;
  color: var(--color-text-light);
  font-size: 0.875rem;
  text-align: center;
  background-color: var(--color-surface);
}
</style>