<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <p class="eyebrow">{{ $t('auth.product_name') }}</p>
      <h1>{{ $t('auth.create_account') }}</h1>
      <p class="subtitle">{{ $t('auth.start_journey') }}</p>

      <div class="info-banner">
        <strong>{{ $t('auth.minimum_signup_title') }}</strong>
        <p>{{ $t('auth.minimum_signup_desc') }}</p>
      </div>

      <el-form label-position="top" size="large">
        <el-form-item :label="$t('auth.username')">
          <el-input v-model="form.username" />
        </el-form-item>

        <el-form-item :label="$t('auth.email')">
          <el-input v-model="form.email" />
        </el-form-item>

        <el-form-item :label="$t('auth.password')">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>

        <el-button type="primary" size="large" class="full-width" :loading="loading" @click="handleRegister">
          {{ $t('auth.create_btn') }}
        </el-button>

        <div class="auth-links">
          {{ $t('auth.has_account') }} <router-link to="/login">{{ $t('auth.login_link') }}</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const auth = useAuthStore()
const router = useRouter()
const loading = ref(false)

const form = reactive({
  username: '',
  email: '',
  password: '',
  health_goal: 'healthy'
})

async function handleRegister() {
  if (!form.username || !form.password || !form.email) {
    ElMessage.warning(t('auth.register_missing'))
    return
  }

  loading.value = true

  try {
    const created = await auth.register(form)
    if (!created) {
      ElMessage.error(t('auth.register_failed'))
      return
    }

    const loggedIn = await auth.login(form.username, form.password, {
      redirectTo: '/profile?onboarding=1'
    })

    if (loggedIn) {
      ElMessage.success(t('auth.register_success'))
      return
    }

    ElMessage.success(t('auth.register_success_fallback'))
    router.push('/login')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 160px);
}

.auth-card {
  width: 100%;
  max-width: 520px;
  padding: 24px;
  border-radius: 24px;
}

.eyebrow {
  margin: 0 0 10px;
  color: var(--color-primary-dark);
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

h1 {
  margin: 0;
  color: var(--color-secondary);
  font-size: 2rem;
}

.subtitle {
  margin: 12px 0 18px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.info-banner {
  margin-bottom: 20px;
  padding: 14px 16px;
  border-radius: 18px;
  background: #f7faf8;
}

.info-banner strong {
  color: var(--color-secondary);
}

.info-banner p {
  margin: 6px 0 0;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.full-width {
  width: 100%;
}

.auth-links {
  text-align: center;
  margin-top: 16px;
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.auth-links a {
  color: var(--color-primary-dark);
  font-weight: 600;
}
</style>
