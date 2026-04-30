<template>
  <div class="home-page">
    <section class="hero">
      <p class="hero-eyebrow">{{ $t('dashboard.welcome') }}</p>
      <h1>{{ $t('dashboard.hello') }}, {{ profile.username || $t('dashboard.guest') }}</h1>
      <p class="hero-sub">{{ $t('dashboard.ready_msg') }}</p>
      <el-button type="primary" size="large" tag="router-link" to="/meal-plan" class="hero-cta">
        {{ $t('dashboard.start_planning') }}
      </el-button>
    </section>

    <section v-if="missingProfileFields.length" class="profile-banner">
      <div class="banner-text">
        <span class="banner-label">{{ $t('dashboard.profile_complete') }} · {{ profileCompletionPercent }}%</span>
        <span class="banner-detail">{{ $t('dashboard.profile_missing_detail', { count: missingProfileFields.length }) }}</span>
      </div>
      <el-button text type="primary" tag="router-link" to="/profile?onboarding=1">
        {{ $t('dashboard.complete_profile') }}
      </el-button>
    </section>

    <section class="quick-links">
      <router-link to="/weekly-plan" class="quick-link">
        <el-icon :size="20"><Calendar /></el-icon>
        <span>{{ $t('weekly_plan.title') }}</span>
      </router-link>
      <router-link to="/recipes" class="quick-link">
        <el-icon :size="20"><Food /></el-icon>
        <span>{{ $t('nav.recipes') }}</span>
      </router-link>
      <router-link to="/history" class="quick-link">
        <el-icon :size="20"><Clock /></el-icon>
        <span>{{ $t('history.title') }}</span>
      </router-link>
      <router-link to="/shopping-list" class="quick-link">
        <el-icon :size="20"><ShoppingCart /></el-icon>
        <span>{{ $t('nav.shopping_cart') }}</span>
      </router-link>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Calendar, Clock, Food, ShoppingCart } from '@element-plus/icons-vue'
import { storeToRefs } from 'pinia'

import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const {
  profile,
  missingProfileFields,
  profileCompletionPercent
} = storeToRefs(userStore)
</script>

<style scoped>
.home-page {
  display: grid;
  gap: 28px;
  max-width: 640px;
}

.hero {
  display: grid;
  gap: 10px;
}

.hero-eyebrow {
  margin: 0;
  color: var(--color-accent-strong);
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
}

.hero h1 {
  margin: 0;
  color: var(--color-secondary);
  font-size: var(--text-4xl);
  font-weight: var(--weight-bold);
  line-height: var(--leading-tight);
  letter-spacing: var(--tracking-tight);
}

.hero-sub {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
  max-width: 48ch;
}

.hero-cta {
  margin-top: 8px;
  justify-self: start;
}

.profile-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 14px 18px;
  border-radius: 12px;
  background: var(--color-accent-soft);
  border: 1px solid var(--color-border-accent);
}

.banner-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.banner-label {
  font-size: var(--text-sm);
  font-weight: var(--weight-bold);
  color: var(--color-accent-strong);
}

.banner-detail {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.quick-links {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.quick-link {
  display: grid;
  justify-items: center;
  gap: 8px;
  padding: 20px 16px;
  border-radius: 12px;
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-soft);
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  transition: border-color 160ms ease, color 160ms ease;
}

.quick-link:hover {
  border-color: var(--color-accent);
  color: var(--color-accent-strong);
}

@media (max-width: 640px) {
  .quick-links {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .hero-cta {
    width: 100%;
  }

  .profile-banner {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
