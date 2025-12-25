<template>
  <div class="profile-page">
    <div class="page-header">
      <h1>{{ $t('profile.title') }}</h1>
      <p class="subtitle">{{ $t('profile.subtitle') }}</p>
    </div>

    <div class="profile-content">
      <!-- Left Column: Form -->
      <el-card class="settings-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><Edit /></el-icon>
            <span>{{ $t('profile.details') }}</span>
          </div>
        </template>
        
        <el-form label-position="top" size="large">
          <el-row :gutter="20">
            <el-col :span="12">
               <el-form-item :label="$t('profile.name')">
                <el-input v-model="profile.name" :placeholder="$t('profile.name_placeholder')" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="$t('auth.gender')">
                <el-radio-group v-model="profile.gender">
                  <el-radio label="male">{{ $t('auth.male') }}</el-radio>
                  <el-radio label="female">{{ $t('auth.female') }}</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item :label="$t('auth.age')">
                <el-input-number v-model="profile.age" :min="10" :max="100" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item :label="$t('auth.height')">
                <el-input-number v-model="profile.height" :min="100" :max="250" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item :label="$t('auth.weight')">
                <el-input-number v-model="profile.weight" :min="30" :max="200" :step="0.5" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item :label="$t('auth.activity_level')">
            <el-select v-model="profile.activityLevel" class="full-width">
              <el-option :label="$t('auth.activity.sedentary')" value="sedentary" />
              <el-option :label="$t('auth.activity.light')" value="light" />
              <el-option :label="$t('auth.activity.moderate')" value="moderate" />
              <el-option :label="$t('auth.activity.active')" value="active" />
              <el-option :label="$t('auth.activity.very_active')" value="very_active" />
            </el-select>
          </el-form-item>

           <el-form-item :label="$t('auth.goal')">
            <el-select v-model="profile.goal" class="full-width">
              <el-option :label="$t('meal_plan.goals.lose_weight')" value="lose_weight" />
              <el-option :label="$t('meal_plan.goals.maintain')" value="maintain" />
              <el-option :label="$t('meal_plan.goals.gain_muscle')" value="gain_muscle" />
              <el-option :label="$t('meal_plan.goals.healthy')" value="healthy" />
            </el-select>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- Right Column: Stats -->
      <div class="stats-column">
        <el-card class="stats-card user-card" shadow="hover">
          <div class="avatar-area">
             <div class="avatar">
               {{ profile.name.charAt(0).toUpperCase() }}
             </div>
             <div>
               <h3>{{ profile.name }}</h3>
               <p>{{ profile.goal.replace('_', ' ').toUpperCase() }}</p>
             </div>
          </div>
        </el-card>

        <el-card class="stats-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><TrendCharts /></el-icon>
              <span>{{ $t('profile.daily_targets') }}</span>
            </div>
          </template>
          
          <div class="metric-big">
            <div class="value">{{ targetCalories }}</div>
            <div class="label">kcal / {{ $t('dashboard.days').toLowerCase() }}</div>
          </div>

          <el-divider />

          <div class="macros-grid">
            <div class="macro-item">
              <span class="macro-val">{{ targetMacros.protein }}g</span>
              <span class="macro-lbl">{{ $t('meal_plan.protein') }}</span>
              <div class="bar protein"></div>
            </div>
            <div class="macro-item">
              <span class="macro-val">{{ targetMacros.carbs }}g</span>
              <span class="macro-lbl">{{ $t('meal_plan.carbs') }}</span>
              <div class="bar carbs"></div>
            </div>
             <div class="macro-item">
              <span class="macro-val">{{ targetMacros.fat }}g</span>
              <span class="macro-lbl">{{ $t('meal_plan.fat') }}</span>
              <div class="bar fat"></div>
            </div>
          </div>
        </el-card>
        
        <el-alert
          :title="$t('profile.auto_save')"
          type="success"
          :description="$t('profile.auto_save_desc')"
          show-icon
          :closable="false"
          class="save-alert"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useUserStore } from '@/stores/user'
import { storeToRefs } from 'pinia'
import { Edit, TrendCharts } from '@element-plus/icons-vue'

const userStore = useUserStore()
const { profile, targetCalories, targetMacros } = storeToRefs(userStore)
</script>

<style scoped>
.page-header {
  margin-bottom: 32px;
}

.page-header h1 {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-secondary);
  margin-bottom: 8px;
}

.subtitle {
  color: var(--color-text-secondary);
}

.profile-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}

@media (max-width: 768px) {
  .profile-content {
    grid-template-columns: 1fr;
  }
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: var(--color-secondary);
}

.full-width {
  width: 100%;
}

.stats-card {
  margin-bottom: 24px;
}

.user-card {
  background: linear-gradient(135deg, var(--color-primary-dark) 0%, var(--color-primary) 100%);
  color: white;
  border: none;
}

.avatar-area {
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar {
  width: 64px;
  height: 64px;
  background: rgba(255,255,255,0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: bold;
}

.metric-big {
  text-align: center;
  padding: 16px 0;
}

.metric-big .value {
  font-size: 3rem;
  font-weight: 800;
  color: var(--color-secondary);
  line-height: 1;
}

.metric-big .label {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  margin-top: 4px;
}

.macros-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  text-align: center;
}

.macro-val {
  display: block;
  font-weight: 700;
  color: var(--color-secondary);
  font-size: 1.1rem;
}

.macro-lbl {
  font-size: 0.8rem;
  color: var(--color-text-light);
}

.bar {
  height: 4px;
  border-radius: 2px;
  margin-top: 8px;
}

.protein { background-color: #3b82f6; } /* Blue */
.carbs { background-color: #eab308; } /* Yellow */
.fat { background-color: #ef4444; } /* Red */
</style>
