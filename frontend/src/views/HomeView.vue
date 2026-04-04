<template>
  <div class="home-page">
    <section class="hero-card">
      <div class="hero-copy">
        <p class="eyebrow">{{ $t('dashboard.welcome') }}</p>
        <h1>{{ $t('dashboard.hello') }}, {{ profile.username || $t('dashboard.guest') }}</h1>
        <p class="subtitle">{{ $t('dashboard.ready_msg') }}</p>
      </div>

      <div class="hero-actions">
        <router-link to="/meal-plan">
          <el-button type="primary" size="large">{{ $t('dashboard.start_planning') }}</el-button>
        </router-link>
        <router-link to="/profile">
          <el-button plain size="large">{{ $t('dashboard.complete_profile') }}</el-button>
        </router-link>
      </div>
    </section>

    <section class="home-grid">
      <article class="primary-panel">
        <p class="panel-eyebrow">{{ $t('dashboard.primary_label') }}</p>
        <h2>{{ $t('dashboard.generate_plan') }}</h2>
        <p>{{ $t('dashboard.generate_desc') }}</p>
        <div class="primary-actions">
          <router-link to="/meal-plan">
            <el-button type="primary" size="large">{{ $t('dashboard.launch_chat') }}</el-button>
          </router-link>
          <router-link to="/history">
            <el-button plain size="large">{{ $t('dashboard.review_history') }}</el-button>
          </router-link>
        </div>
      </article>

      <aside class="side-stack">
        <article class="status-card">
          <div class="status-head">
            <div>
              <p class="panel-eyebrow">{{ $t('dashboard.profile_complete') }}</p>
              <h3>{{ profileCompletionPercent }}%</h3>
            </div>
            <span>{{ profileCompletionCompleted }}/{{ profileCompletionTotal }}</span>
          </div>

          <p class="status-copy">
            {{
              missingProfileFields.length
                ? $t('dashboard.profile_missing_detail', { count: missingProfileFields.length })
                : $t('dashboard.profile_ready')
            }}
          </p>

          <ul v-if="missingProfileFields.length" class="missing-list">
            <li v-for="field in missingProfileFields" :key="field">
              {{ $t(`profile.field_labels.${field}`) }}
            </li>
          </ul>

          <router-link to="/profile?onboarding=1">
            <el-button plain>{{ $t('dashboard.complete_profile') }}</el-button>
          </router-link>
        </article>

        <article class="secondary-card">
          <h3>{{ $t('history.title') }}</h3>
          <p>{{ $t('dashboard.history_cta') }}</p>
          <router-link to="/history">
            <el-button text type="primary">{{ $t('dashboard.review_history') }}</el-button>
          </router-link>
        </article>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'

import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const {
  profile,
  missingProfileFields,
  profileCompletionCompleted,
  profileCompletionPercent,
  profileCompletionTotal
} = storeToRefs(userStore)
</script>

<style scoped>
.home-page {
  display: grid;
  gap: 24px;
}

.hero-card {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding: clamp(24px, 4vw, 36px);
  border-radius: 28px;
  background:
    radial-gradient(circle at top right, rgba(34, 197, 94, 0.22), transparent 32%),
    linear-gradient(135deg, #f6fff7, #ffffff 58%, #eef8f0);
  border: 1px solid rgba(34, 197, 94, 0.14);
}

.eyebrow,
.panel-eyebrow {
  margin: 0 0 10px;
  color: var(--color-primary-dark);
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.hero-copy {
  max-width: 680px;
}

.hero-copy h1 {
  margin: 0;
  color: var(--color-secondary);
  font-size: clamp(2rem, 3.8vw, 3rem);
  line-height: 1.05;
}

.subtitle,
.primary-panel p,
.secondary-card p,
.status-copy {
  color: var(--color-text-secondary);
  line-height: 1.7;
}

.subtitle {
  margin: 14px 0 0;
}

.hero-actions,
.primary-actions,
.side-stack,
.missing-list {
  display: grid;
  gap: 12px;
}

.hero-actions {
  align-content: center;
}

.home-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(280px, 0.9fr);
  gap: 20px;
}

.primary-panel,
.status-card,
.secondary-card {
  display: grid;
  gap: 14px;
  padding: 24px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 16px 32px rgba(15, 23, 42, 0.06);
}

.primary-panel {
  background: linear-gradient(145deg, #10251a, #173728 60%, #1f5137);
}

.primary-panel h2,
.secondary-card h3,
.status-card h3 {
  margin: 0;
}

.primary-panel h2,
.primary-panel p,
.primary-panel .panel-eyebrow {
  color: #effff5;
}

.primary-panel p {
  margin: 0;
  max-width: 560px;
}

.primary-actions {
  grid-auto-flow: column;
  justify-content: start;
}

.status-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.status-head h3 {
  color: var(--color-secondary);
  font-size: 2rem;
}

.status-head span {
  color: var(--color-text-light);
}

.missing-list {
  padding-left: 18px;
  color: var(--color-text-secondary);
}

@media (max-width: 960px) {
  .hero-card,
  .home-grid {
    grid-template-columns: 1fr;
    display: grid;
  }

  .hero-actions {
    justify-items: start;
  }
}

@media (max-width: 640px) {
  .hero-actions :deep(.el-button),
  .primary-actions :deep(.el-button),
  .status-card :deep(.el-button) {
    width: 100%;
    min-height: 44px;
  }

  .primary-actions {
    grid-auto-flow: row;
  }
}
</style>
