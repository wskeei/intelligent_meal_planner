<template>
  <div class="profile-page">
    <!-- Header -->
    <header class="page-header">
      <h1>{{ $t('profile.title') }}</h1>
      <p class="subtitle">
        {{ onboardingMode ? $t('profile.onboarding_subtitle') : $t('profile.subtitle') }}
      </p>
    </header>

    <!-- Missing fields bar -->
    <section v-if="missingProfileFields.length" class="missing-bar">
      <button class="missing-bar__toggle" type="button" :aria-expanded="showMissingExpanded" aria-controls="missing-bar-list" @click="showMissing = !showMissing">
        <span>{{ $t('profile.missing_bar', { count: missingProfileFields.length }) }}</span>
        <el-icon class="missing-bar__chevron" :class="{ 'is-open': showMissing }"><ArrowDown /></el-icon>
      </button>
      <div v-if="showMissing" id="missing-bar-list" class="missing-bar__list">
        <div v-for="field in missingProfileFields" :key="field" class="missing-bar__item">
          <strong>{{ $t(`profile.field_labels.${field}`) }}</strong>
          <span>{{ $t(`profile.field_reasons.${field}`) }}</span>
        </div>
      </div>
    </section>

    <!-- Basic info section -->
    <section class="form-section">
      <h2 class="section-heading">{{ $t('profile.section_basic') }}</h2>
      <div class="section-divider" />

      <div class="username-row">
        <span class="username-label">{{ $t('auth.username') }}</span>
        <span class="username-value">{{ profile.username || '--' }}</span>
      </div>

      <div class="field">
        <label for="profile-gender" class="field__label">{{ $t('auth.gender') }}</label>
        <el-radio-group id="profile-gender" v-model="localProfile.gender">
          <el-radio-button value="male">{{ $t('auth.male') }}</el-radio-button>
          <el-radio-button value="female">{{ $t('auth.female') }}</el-radio-button>
        </el-radio-group>
        <p class="field__hint">{{ $t('profile.field_reasons.gender') }}</p>
      </div>

      <div class="field-grid">
        <div class="field">
          <label for="profile-age" class="field__label">{{ $t('auth.age') }}</label>
          <el-input-number id="profile-age" v-model="localProfile.age" :min="10" :max="100" controls-position="right" />
          <p class="field__hint">{{ $t('profile.field_reasons.age') }}</p>
        </div>
        <div class="field">
          <label for="profile-activity" class="field__label">{{ $t('auth.activity_level') }}</label>
          <el-select id="profile-activity" v-model="localProfile.activityLevel" :placeholder="$t('auth.activity_level')">
            <el-option :label="$t('auth.activity.sedentary')" value="sedentary" />
            <el-option :label="$t('auth.activity.light')" value="light" />
            <el-option :label="$t('auth.activity.moderate')" value="moderate" />
            <el-option :label="$t('auth.activity.active')" value="active" />
            <el-option :label="$t('auth.activity.very_active')" value="very_active" />
          </el-select>
          <p class="field__hint">{{ $t('profile.field_reasons.activityLevel') }}</p>
        </div>
      </div>

      <div class="field-grid">
        <div class="field">
          <label for="profile-height" class="field__label">{{ $t('auth.height') }}</label>
          <el-input-number id="profile-height" v-model="localProfile.height" :min="100" :max="250" controls-position="right" />
          <p class="field__hint">{{ $t('profile.field_reasons.height') }}</p>
        </div>
        <div class="field">
          <label for="profile-weight" class="field__label">{{ $t('auth.weight') }}</label>
          <el-input-number id="profile-weight" v-model="localProfile.weight" :min="30" :max="250" :step="0.5" controls-position="right" />
          <p class="field__hint">{{ $t('profile.field_reasons.weight') }}</p>
        </div>
      </div>
    </section>

    <!-- Goal section -->
    <section class="form-section">
      <h2 class="section-heading">{{ $t('profile.section_goal') }}</h2>
      <div class="section-divider" />

      <div class="field">
        <label for="profile-goal" class="field__label">{{ $t('auth.goal') }}</label>
        <el-select id="profile-goal" v-model="localProfile.goal">
          <el-option :label="$t('meal_plan.goals.lose_weight')" value="lose_weight" />
          <el-option :label="$t('meal_plan.goals.maintain')" value="maintain" />
          <el-option :label="$t('meal_plan.goals.gain_muscle')" value="gain_muscle" />
          <el-option :label="$t('meal_plan.goals.healthy')" value="healthy" />
        </el-select>
        <p class="field__hint">{{ $t('profile.goal_reason') }}</p>
      </div>
    </section>

    <!-- Actions -->
    <div class="actions">
      <el-button type="primary" :loading="saving" @click="save">
        {{ $t('common.save') }}
      </el-button>
      <el-button text tag="router-link" to="/meal-plan">
        {{ $t('profile.open_chat') }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'

import { useUserStore, type UserProfile } from '@/stores/user'

const { t } = useI18n()
const route = useRoute()
const userStore = useUserStore()
const {
  profile,
  missingProfileFields
} = storeToRefs(userStore)

const saving = ref(false)
const showMissing = ref(false)
const showMissingExpanded = computed<'true' | 'false'>(() => showMissing.value ? 'true' : 'false')
const onboardingMode = route.query.onboarding === '1'

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
  gap: 28px;
  max-width: 640px;
}

/* Header */
.page-header h1 {
  margin: 0;
  color: var(--color-secondary);
  font-size: var(--text-4xl);
  font-weight: var(--weight-bold);
  line-height: var(--leading-tight);
  letter-spacing: var(--tracking-tight);
}

.subtitle {
  margin: 8px 0 0;
  color: var(--color-text-secondary);
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
}

/* Missing fields bar */
.missing-bar {
  border-radius: 12px;
  background: var(--color-accent-soft);
  border: 1px solid var(--color-border-accent);
  overflow: hidden;
}

.missing-bar__toggle {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 14px 18px;
  border: none;
  background: transparent;
  color: var(--color-accent-strong);
  font-size: var(--text-sm);
  font-weight: var(--weight-bold);
  cursor: pointer;
}

.missing-bar__chevron {
  transition: transform 160ms ease;
  color: var(--color-accent-strong);
}

.missing-bar__chevron.is-open {
  transform: rotate(180deg);
}

.missing-bar__list {
  display: grid;
  gap: 2px;
  padding: 0 18px 14px;
}

.missing-bar__item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 14px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--color-surface-raised) 50%, transparent);
}

.missing-bar__item strong {
  font-size: var(--text-sm);
  font-weight: var(--weight-bold);
  color: var(--color-secondary);
}

.missing-bar__item span {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

/* Form sections */
.form-section {
  display: grid;
  gap: 18px;
}

.section-heading {
  margin: 0;
  font-size: var(--text-sm);
  font-weight: var(--weight-bold);
  color: var(--color-text-light);
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
}

.section-divider {
  height: 1px;
  background: var(--color-border-soft);
}

/* Username row */
.username-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.username-label {
  font-size: var(--text-sm);
  color: var(--color-text-light);
}

.username-value {
  font-size: var(--text-base);
  font-weight: var(--weight-medium);
  color: var(--color-secondary);
}

/* Fields */
.field {
  display: grid;
  gap: 8px;
}

.field__label {
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-secondary);
}

.field__hint {
  margin: 0;
  font-size: var(--text-xs);
  color: var(--color-text-light);
  line-height: 1.5;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

/* Element Plus overrides */
.field :deep(.el-radio-group) {
  display: flex;
  gap: 8px;
}

.field :deep(.el-radio-button__inner) {
  border-radius: 8px !important;
  border: 1px solid var(--color-border-soft) !important;
  background: var(--color-surface-raised) !important;
  color: var(--color-text-secondary) !important;
  font-weight: var(--weight-medium) !important;
  box-shadow: none !important;
  padding: 8px 18px;
  min-height: 40px;
  transition: border-color 160ms ease, color 160ms ease, background 160ms ease;
}

.field :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  border-color: var(--color-accent) !important;
  background: var(--color-accent-soft) !important;
  color: var(--color-accent-strong) !important;
}

.field :deep(.el-input-number),
.field :deep(.el-select) {
  width: 100%;
}

.field :deep(.el-input__wrapper),
.field :deep(.el-select__wrapper) {
  border-radius: 10px;
  min-height: 40px;
}

/* Actions */
.actions {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 4px;
}

/* Mobile */
@media (max-width: 640px) {
  .field-grid {
    grid-template-columns: 1fr;
  }

  .actions {
    flex-direction: column;
    align-items: stretch;
  }

  .actions :deep(.el-button) {
    width: 100%;
    min-height: 44px;
  }
}
</style>
