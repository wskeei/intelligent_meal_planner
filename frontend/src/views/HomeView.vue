<template>
  <div class="dashboard">
    <!-- Welcome Section -->
    <div class="header-section">
      <div class="greeting">
        <h1>{{ $t('dashboard.hello') }}, {{ profile.name }}! 👋</h1>
        <p class="subtitle">{{ $t('dashboard.ready_msg') }}</p>
      </div>
      <router-link to="/profile">
        <el-button plain round>
          <el-icon style="margin-right: 6px"><Setting /></el-icon>
          {{ $t('dashboard.edit_profile') }}
        </el-button>
      </router-link>
    </div>

    <!-- Stats Overview -->
    <el-row :gutter="20" class="stats-row">
      <!-- Calorie Target -->
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card primary">
          <div class="stat-content">
            <div class="icon-wrap"><el-icon><Odometer /></el-icon></div>
            <div>
              <div class="label">{{ $t('dashboard.daily_target') }}</div>
              <div class="value">{{ targetCalories }} <span class="unit">kcal</span></div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <!-- Current Goal -->
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
           <div class="stat-content">
            <div class="icon-wrap blue"><el-icon><Aim /></el-icon></div>
            <div>
              <div class="label">{{ $t('dashboard.current_goal') }}</div>
              <div class="value text-cap">{{ profile.goal.replace('_', ' ') }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- Streak (Mock) -->
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
           <div class="stat-content">
            <div class="icon-wrap orange"><el-icon><Trophy /></el-icon></div>
            <div>
              <div class="label">{{ $t('dashboard.planning_streak') }}</div>
              <div class="value">3 <span class="unit">{{ $t('dashboard.days') }}</span></div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Main Actions -->
    <div class="action-grid">
      <el-card class="action-card main-action" shadow="hover" @click="$router.push('/meal-plan')">
        <div class="action-content">
          <img src="https://cdn-icons-png.flaticon.com/512/706/706195.png" alt="Meal" class="action-img" />
          <div class="action-text">
            <h2>{{ $t('dashboard.generate_plan') }}</h2>
            <p>{{ $t('dashboard.generate_desc') }}</p>
            <el-button type="primary" round>{{ $t('dashboard.start_planning') }}</el-button>
          </div>
        </div>
      </el-card>

      <div class="sub-actions">
        <el-card class="action-card sub" shadow="hover" @click="$router.push('/recipes')">
          <div class="sub-content">
             <el-icon :size="32" color="#10b981"><Dish /></el-icon>
             <h3>{{ $t('dashboard.browse_recipes') }}</h3>
          </div>
        </el-card>
        
        <el-card class="action-card sub" shadow="hover" @click="$router.push('/shopping-list')">
           <div class="sub-content">
             <el-icon :size="32" color="#3b82f6"><ShoppingCart /></el-icon>
             <h3>{{ $t('dashboard.shopping_list') }}</h3>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useUserStore } from '@/stores/user'
import { storeToRefs } from 'pinia'
import { Setting, Odometer, Aim, Trophy, Dish, ShoppingCart } from '@element-plus/icons-vue'

const userStore = useUserStore()
const { profile, targetCalories } = storeToRefs(userStore)
</script>

<style scoped>
.dashboard {
  max-width: 1000px;
  margin: 0 auto;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.greeting h1 {
  font-size: 2.5rem;
  color: var(--color-secondary);
  font-weight: 800;
  margin-bottom: 4px;
}

.subtitle {
  color: var(--color-text-secondary);
  font-size: 1.1rem;
}

/* Stats Row */
.stats-row {
  margin-bottom: 40px;
}

.stat-card {
  height: 100%;
  border: none;
  background: white;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-4px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.icon-wrap {
  width: 48px;
  height: 48px;
  background: #ecfdf5;
  color: var(--color-primary-dark);
  border-radius: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 24px;
}

.icon-wrap.blue { background: #eff6ff; color: #3b82f6; }
.icon-wrap.orange { background: #fff7ed; color: #f97316; }

.label {
  font-size: 0.85rem;
  color: var(--color-text-light);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.value {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--color-secondary);
}

.text-cap {
  text-transform: capitalize;
}

.unit {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--color-text-secondary);
}

/* Action Grid */
.action-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}

@media (max-width: 768px) {
  .action-grid {
    grid-template-columns: 1fr;
  }
}

.action-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
}

.action-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.main-action {
  background: linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%);
  border: 2px solid transparent;
}

.main-action:hover {
  border-color: var(--color-primary);
}

.action-content {
  display: flex;
  align-items: center;
  gap: 32px;
  padding: 16px;
}

.action-img {
  width: 120px;
  filter: drop-shadow(0 10px 15px rgba(0,0,0,0.1));
}

.action-text h2 {
  font-size: 1.5rem;
  color: var(--color-secondary);
  margin-bottom: 8px;
}

.action-text p {
  color: var(--color-text-secondary);
  margin-bottom: 20px;
  line-height: 1.4;
}

.sub-actions {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.sub-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 20px;
  gap: 12px;
}

.sub-content h3 {
  color: var(--color-text-main);
  font-weight: 600;
}
</style>