<template>
  <div class="profile-page">
    <div class="page-header">
      <h1>{{ $t('profile.title') }}</h1>
      <p class="subtitle">{{ $t('profile.subtitle') }}</p>
    </div>

    <div class="profile-grid">
      <el-card class="settings-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>{{ $t('profile.details') }}</span>
          </div>
        </template>

        <el-form label-position="top" size="large">
          <el-form-item :label="$t('auth.username')">
            <el-input :model-value="profile.username" disabled />
          </el-form-item>

          <el-form-item :label="$t('auth.gender')">
            <el-radio-group v-model="localProfile.gender">
              <el-radio label="male">{{ $t('auth.male') }}</el-radio>
              <el-radio label="female">{{ $t('auth.female') }}</el-radio>
            </el-radio-group>
          </el-form-item>

          <div class="grid-two">
            <el-form-item :label="$t('auth.age')">
              <el-input-number v-model="localProfile.age" :min="10" :max="100" class="full-width" />
            </el-form-item>

            <el-form-item :label="$t('auth.activity_level')">
              <el-select v-model="localProfile.activityLevel" class="full-width">
                <el-option :label="$t('auth.activity.sedentary')" value="sedentary" />
                <el-option :label="$t('auth.activity.light')" value="light" />
                <el-option :label="$t('auth.activity.moderate')" value="moderate" />
                <el-option :label="$t('auth.activity.active')" value="active" />
                <el-option :label="$t('auth.activity.very_active')" value="very_active" />
              </el-select>
            </el-form-item>
          </div>

          <div class="grid-two">
            <el-form-item :label="$t('auth.height')">
              <el-input-number v-model="localProfile.height" :min="100" :max="250" class="full-width" />
            </el-form-item>

            <el-form-item :label="$t('auth.weight')">
              <el-input-number v-model="localProfile.weight" :min="30" :max="250" :step="0.5" class="full-width" />
            </el-form-item>
          </div>

          <el-form-item :label="$t('auth.goal')">
            <el-select v-model="localProfile.goal" class="full-width">
              <el-option :label="$t('meal_plan.goals.lose_weight')" value="lose_weight" />
              <el-option :label="$t('meal_plan.goals.maintain')" value="maintain" />
              <el-option :label="$t('meal_plan.goals.gain_muscle')" value="gain_muscle" />
              <el-option :label="$t('meal_plan.goals.healthy')" value="healthy" />
            </el-select>
          </el-form-item>

          <div class="actions">
            <el-button type="primary" :loading="saving" @click="save">
              {{ $t('common.save') }}
            </el-button>
          </div>
        </el-form>
      </el-card>

      <div class="side-stack">
        <el-card class="status-card" shadow="hover">
          <p class="eyebrow">{{ $t('profile.sync_title') }}</p>
          <h2>{{ profileComplete ? $t('profile.profile_ready') : $t('profile.profile_missing') }}</h2>
          <p>{{ $t('profile.sync_hint') }}</p>

          <router-link to="/meal-plan">
            <el-button type="primary" plain>{{ $t('profile.open_chat') }}</el-button>
          </router-link>
        </el-card>

        <el-alert
          :title="$t('profile.chat_sync_title')"
          :description="$t('profile.chat_sync_desc')"
          type="info"
          show-icon
          :closable="false"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

import { useUserStore, type UserProfile } from '@/stores/user'

const { t } = useI18n()
const userStore = useUserStore()
const { profile, profileComplete } = storeToRefs(userStore)

const saving = ref(false)
const localProfile = reactive<UserProfile>({
  username: '',
  age: null,
  gender: null,
  height: null,
  weight: null,
  activityLevel: null,
  goal: 'healthy'
})

watch(
  profile,
  (value) => {
    Object.assign(localProfile, value)
  },
  { immediate: true, deep: true }
)

async function save() {
  saving.value = true
  try {
    await userStore.saveProfile(localProfile)
    ElMessage.success(t('profile.saved'))
  } catch (error) {
    console.error(error)
    ElMessage.error(t('profile.save_failed'))
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.profile-page {
  display: grid;
  gap: 24px;
}

.page-header h1 {
  margin: 0;
  color: var(--color-secondary);
  font-size: 2rem;
}

.subtitle {
  margin: 8px 0 0;
  color: var(--color-text-secondary);
}

.profile-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(280px, 0.9fr);
  gap: 24px;
  align-items: start;
}

.settings-card,
.status-card {
  border: none;
  border-radius: 24px;
  box-shadow: 0 16px 32px rgba(15, 23, 42, 0.08);
}

.card-header {
  color: var(--color-secondary);
  font-weight: 700;
}

.grid-two {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.full-width {
  width: 100%;
}

.actions {
  margin-top: 8px;
}

.side-stack {
  display: grid;
  gap: 16px;
}

.status-card {
  background: linear-gradient(155deg, #10251a, #173728 62%, #214c35);
  color: #f0fff5;
}

.eyebrow {
  margin: 0 0 8px;
  color: rgba(240, 255, 245, 0.72);
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.status-card h2 {
  margin: 0 0 12px;
  font-size: 1.5rem;
}

.status-card p {
  margin: 0 0 16px;
  color: rgba(240, 255, 245, 0.78);
  line-height: 1.7;
}

@media (max-width: 900px) {
  .profile-grid,
  .grid-two {
    grid-template-columns: 1fr;
  }
}
</style>
