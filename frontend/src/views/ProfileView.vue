<template>
  <div class="profile-page">
    <header class="page-header">
      <h1>{{ $t('profile.title') }}</h1>
      <p class="subtitle">
        {{ onboardingMode ? $t('profile.onboarding_subtitle') : $t('profile.subtitle') }}
      </p>
    </header>

    <div class="profile-grid">
      <el-card class="settings-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>{{ $t('profile.details') }}</span>
          </div>
        </template>

        <el-form label-position="top" size="large">
          <el-alert
            v-if="saveError"
            :title="saveError"
            type="error"
            show-icon
            :closable="false"
            class="inline-alert"
          />

          <el-form-item :label="$t('auth.username')">
            <el-input :model-value="profile.username" disabled />
          </el-form-item>

          <el-form-item :label="$t('auth.gender')">
              <el-radio-group v-model="localProfile.gender">
                <el-radio value="male">{{ $t('auth.male') }}</el-radio>
                <el-radio value="female">{{ $t('auth.female') }}</el-radio>
            </el-radio-group>
            <p class="field-hint">{{ $t('profile.field_reasons.gender') }}</p>
          </el-form-item>

          <div class="grid-two">
            <el-form-item :label="$t('auth.age')">
              <el-input-number v-model="localProfile.age" :min="10" :max="100" class="full-width" />
              <p class="field-hint">{{ $t('profile.field_reasons.age') }}</p>
            </el-form-item>

            <el-form-item :label="$t('auth.activity_level')">
              <el-select v-model="localProfile.activityLevel" class="full-width">
                <el-option :label="$t('auth.activity.sedentary')" value="sedentary" />
                <el-option :label="$t('auth.activity.light')" value="light" />
                <el-option :label="$t('auth.activity.moderate')" value="moderate" />
                <el-option :label="$t('auth.activity.active')" value="active" />
                <el-option :label="$t('auth.activity.very_active')" value="very_active" />
              </el-select>
              <p class="field-hint">{{ $t('profile.field_reasons.activityLevel') }}</p>
            </el-form-item>
          </div>

          <div class="grid-two">
            <el-form-item :label="$t('auth.height')">
              <el-input-number v-model="localProfile.height" :min="100" :max="250" class="full-width" />
              <p class="field-hint">{{ $t('profile.field_reasons.height') }}</p>
            </el-form-item>

            <el-form-item :label="$t('auth.weight')">
              <el-input-number v-model="localProfile.weight" :min="30" :max="250" :step="0.5" class="full-width" />
              <p class="field-hint">{{ $t('profile.field_reasons.weight') }}</p>
            </el-form-item>
          </div>

          <el-form-item :label="$t('auth.goal')">
            <el-select v-model="localProfile.goal" class="full-width">
              <el-option :label="$t('meal_plan.goals.lose_weight')" value="lose_weight" />
              <el-option :label="$t('meal_plan.goals.maintain')" value="maintain" />
              <el-option :label="$t('meal_plan.goals.gain_muscle')" value="gain_muscle" />
              <el-option :label="$t('meal_plan.goals.healthy')" value="healthy" />
            </el-select>
            <p class="field-hint">{{ $t('profile.goal_reason') }}</p>
          </el-form-item>

          <div class="actions">
            <el-button type="primary" :loading="saving" @click="save">
              {{ $t('common.save') }}
            </el-button>
            <el-button plain tag="router-link" to="/meal-plan">
              {{ $t('profile.open_chat') }}
            </el-button>
          </div>
        </el-form>
      </el-card>

      <div class="side-stack">
        <el-card class="status-card" shadow="hover">
          <p class="eyebrow">{{ $t('profile.sync_title') }}</p>
          <div class="progress-head">
            <div>
              <h2>{{ profileCompletionPercent }}%</h2>
              <p>{{ $t('profile.progress_label', { completed: profileCompletionCompleted, total: profileCompletionTotal }) }}</p>
            </div>
            <el-progress
              type="circle"
              :percentage="profileCompletionPercent"
              :width="96"
              :stroke-width="10"
              :show-text="false"
              :color="progressColor"
            />
          </div>

          <p class="status-copy">
            {{
              missingProfileFields.length
                ? $t('profile.profile_missing_detail', { count: missingProfileFields.length })
                : $t('profile.profile_ready')
            }}
          </p>

          <div v-if="missingProfileFields.length" class="missing-block">
            <article v-for="field in missingProfileFields" :key="field" class="missing-item">
              <strong>{{ $t(`profile.field_labels.${field}`) }}</strong>
              <p>{{ $t(`profile.field_reasons.${field}`) }}</p>
            </article>
          </div>
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
import { onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'

import { useUserStore, type UserProfile } from '@/stores/user'

const { t } = useI18n()
const route = useRoute()
const userStore = useUserStore()
const {
  profile,
  missingProfileFields,
  profileCompletionCompleted,
  profileCompletionPercent,
  profileCompletionTotal
} = storeToRefs(userStore)

const saving = ref(false)
const saveError = ref('')
const onboardingMode = route.query.onboarding === '1'
const progressColor = ref('var(--color-accent)')
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

let colorSchemeQuery: MediaQueryList | null = null
let onColorSchemeChange: ((event: MediaQueryListEvent) => void) | null = null

function syncProgressColor() {
  if (typeof window === 'undefined') return
  const color = getComputedStyle(document.documentElement).getPropertyValue('--color-accent').trim()
  progressColor.value = color || 'var(--color-accent)'
}

async function save() {
  saving.value = true
  saveError.value = ''
  try {
    await userStore.saveProfile(localProfile)
    ElMessage.success(t('profile.saved'))
  } catch (error) {
    console.error(error)
    saveError.value = t('profile.save_inline_error')
    ElMessage.error(t('profile.save_failed'))
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  syncProgressColor()
  colorSchemeQuery = window.matchMedia('(prefers-color-scheme: dark)')
  onColorSchemeChange = () => {
    syncProgressColor()
  }
  colorSchemeQuery.addEventListener('change', onColorSchemeChange)
})

onBeforeUnmount(() => {
  if (colorSchemeQuery && onColorSchemeChange) {
    colorSchemeQuery.removeEventListener('change', onColorSchemeChange)
  }
})
</script>

<style scoped>
.profile-page {
  display: grid;
  gap: 24px;
}

.page-header h1 {
  margin: 0;
  color: var(--color-secondary);
  font-size: clamp(2rem, 4vw, 2.6rem);
}

.subtitle {
  margin: 8px 0 0;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.profile-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(320px, 0.95fr);
  gap: 24px;
  align-items: start;
}

.settings-card,
.status-card {
  border: none;
  border-radius: 24px;
  box-shadow: var(--shadow-md);
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

.field-hint {
  margin: 8px 0 0;
  color: var(--color-text-light);
  font-size: 0.84rem;
  line-height: 1.5;
}

.inline-alert {
  margin-bottom: 16px;
}

.actions,
.side-stack,
.missing-block {
  display: grid;
  gap: 14px;
}

.actions {
  grid-auto-flow: column;
  justify-content: start;
  margin-top: 8px;
}

.status-card {
  background: var(--gradient-emphasis);
  color: var(--color-text-emphasis);
  border: 1px solid var(--color-border-accent);
}

.eyebrow {
  margin: 0 0 8px;
  color: var(--color-text-emphasis-muted);
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.progress-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.progress-head h2 {
  margin: 0;
  font-size: 2rem;
}

.progress-head p,
.status-copy,
.missing-item p {
  margin: 6px 0 0;
  color: var(--color-text-emphasis-muted);
  line-height: 1.6;
}

.missing-item {
  padding: 12px 14px;
  border-radius: 16px;
  background: color-mix(in srgb, var(--color-surface-raised) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-border-soft) 72%, transparent);
}

.missing-item strong {
  color: var(--color-text-emphasis);
}

@media (max-width: 960px) {
  .profile-grid,
  .grid-two {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .actions {
    grid-auto-flow: row;
  }

  .actions :deep(.el-button) {
    width: 100%;
    min-height: 44px;
  }
}
</style>
