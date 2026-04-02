<template>
  <div class="dashboard">
    <section class="hero-card">
      <div class="hero-copy">
        <p class="eyebrow">{{ $t('dashboard.welcome') }}</p>
        <h1>{{ $t('dashboard.hello') }}, {{ profile.username || $t('dashboard.guest') }}</h1>
        <p class="subtitle">{{ $t('dashboard.ready_msg') }}</p>
      </div>

      <div class="hero-actions">
        <router-link to="/profile">
          <el-button plain>{{ $t('dashboard.edit_profile') }}</el-button>
        </router-link>
        <router-link to="/meal-plan">
          <el-button type="primary">{{ $t('dashboard.start_planning') }}</el-button>
        </router-link>
      </div>
    </section>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="24" :md="12">
        <el-card shadow="hover" class="stat-card">
          <div class="label">{{ $t('dashboard.current_goal') }}</div>
          <div class="value text-cap">{{ $t(`meal_plan.goals.${profile.goal}`) }}</div>
        </el-card>
      </el-col>

      <el-col :span="24" :md="12">
        <el-card shadow="hover" class="stat-card">
          <div class="label">{{ $t('dashboard.profile_complete') }}</div>
          <div class="value">
            {{ profileComplete ? '100%' : $t('dashboard.profile_missing') }}
          </div>
        </el-card>
      </el-col>
    </el-row>

    <section class="action-grid">
      <el-card class="action-card primary-card" shadow="hover" @click="$router.push('/meal-plan')">
        <p class="eyebrow">{{ $t('meal_plan.nutritionist') }}</p>
        <h2>{{ $t('dashboard.generate_plan') }}</h2>
        <p>{{ $t('dashboard.generate_desc') }}</p>
        <el-button type="primary">{{ $t('dashboard.launch_chat') }}</el-button>
      </el-card>

      <div class="side-actions">
        <el-card class="action-card" shadow="hover" @click="$router.push('/profile')">
          <h3>{{ $t('dashboard.edit_profile') }}</h3>
          <p>{{ $t('dashboard.profile_cta') }}</p>
        </el-card>

        <el-card class="action-card" shadow="hover" @click="$router.push('/history')">
          <h3>{{ $t('history.title') }}</h3>
          <p>{{ $t('dashboard.history_cta') }}</p>
        </el-card>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'

import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const { profile, profileComplete } = storeToRefs(userStore)
</script>

<style scoped>
.dashboard {
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
    radial-gradient(circle at top right, rgba(34, 197, 94, 0.24), transparent 32%),
    linear-gradient(135deg, #f6fff7, #ffffff 58%, #eef8f0);
  border: 1px solid rgba(34, 197, 94, 0.14);
}

.hero-copy {
  max-width: 680px;
}

.eyebrow {
  margin: 0 0 10px;
  color: var(--color-primary-dark);
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.hero-copy h1 {
  margin: 0;
  color: var(--color-secondary);
  font-size: clamp(2rem, 3.8vw, 3rem);
  line-height: 1.05;
}

.subtitle {
  margin: 14px 0 0;
  color: var(--color-text-secondary);
  font-size: 1rem;
  line-height: 1.7;
}

.hero-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: center;
  gap: 12px;
}

.stats-row {
  margin: 0;
}

.stat-card,
.action-card {
  border: none;
  border-radius: 24px;
  box-shadow: 0 16px 32px rgba(15, 23, 42, 0.08);
}

.stat-card .label {
  color: var(--color-text-light);
  font-size: 0.84rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.stat-card .value {
  margin-top: 10px;
  color: var(--color-secondary);
  font-size: 1.8rem;
  font-weight: 800;
}

.text-cap {
  text-transform: capitalize;
}

.action-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(280px, 0.9fr);
  gap: 20px;
}

.primary-card {
  display: grid;
  gap: 14px;
  padding: 30px;
  background: linear-gradient(145deg, #10251a, #173728 60%, #1f5137);
  color: #f0fff5;
  cursor: pointer;
}

.primary-card h2,
.side-actions h3 {
  margin: 0;
}

.primary-card p {
  margin: 0;
  max-width: 560px;
  color: rgba(240, 255, 245, 0.78);
  line-height: 1.7;
}

.side-actions {
  display: grid;
  gap: 20px;
}

.side-actions .action-card {
  cursor: pointer;
}

.side-actions p {
  margin: 8px 0 0;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

@media (max-width: 960px) {
  .hero-card,
  .action-grid {
    grid-template-columns: 1fr;
    display: grid;
  }

  .hero-actions {
    align-items: flex-start;
  }
}

@media (max-width: 640px) {
  .hero-actions {
    width: 100%;
  }

  .hero-actions :deep(.el-button) {
    width: 100%;
  }
}
</style>
