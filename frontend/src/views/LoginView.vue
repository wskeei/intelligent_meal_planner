<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <p class="eyebrow">{{ $t('auth.product_name') }}</p>
      <h1>{{ $t('auth.welcome_back') }}</h1>
      <p class="subtitle">{{ $t('auth.login_intro') }}</p>

      <el-form label-position="top" @submit.prevent>
        <el-alert
          v-if="errorMessage"
          :title="errorMessage"
          type="error"
          show-icon
          :closable="false"
          class="inline-alert"
        />

        <el-form-item :label="$t('auth.username')">
          <el-input v-model="username" :placeholder="$t('auth.username')" size="large" />
        </el-form-item>

        <el-form-item :label="$t('auth.password')">
          <el-input
            v-model="password"
            type="password"
            :placeholder="$t('auth.password')"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-button type="primary" size="large" class="full-width" :loading="loading" @click="handleLogin">
          {{ $t('auth.login_btn') }}
        </el-button>

        <div class="auth-links">
          {{ $t('auth.no_account') }} <router-link to="/register">{{ $t('auth.register_link') }}</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const route = useRoute()
const auth = useAuthStore()
const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

const redirectTarget = computed(() =>
  typeof route.query.redirect === 'string' ? route.query.redirect : '/'
)

async function handleLogin() {
  if (!username.value || !password.value) {
    errorMessage.value = t('auth.login_missing')
    ElMessage.warning(errorMessage.value)
    return
  }

  errorMessage.value = ''
  loading.value = true
  const result = await auth.login(username.value, password.value, {
    redirectTo: redirectTarget.value
  })
  loading.value = false

  if (result.ok) {
    errorMessage.value = ''
    ElMessage.success(t('auth.login_success'))
  } else {
    const key =
      result.reason === 'invalid_credentials' ? 'auth.invalid_credentials' : 'auth.login_inline_error'
    const toastKey =
      result.reason === 'invalid_credentials' ? 'auth.invalid_credentials' : 'auth.login_failed'

    errorMessage.value = t(key)
    ElMessage.error(t(toastKey))
  }
}
</script>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 160px);
  padding: 20px 0;
}

.auth-card {
  width: 100%;
  max-width: 440px;
  min-width: 0;
  padding: 24px;
  border-radius: 24px;
  background: var(--gradient-surface);
  border: 1px solid var(--color-border-soft);
  box-shadow: var(--shadow-md);
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
  margin: 12px 0 24px;
  color: var(--color-text-secondary);
  line-height: 1.6;
  max-width: 42ch;
}

.full-width {
  width: 100%;
}

.inline-alert {
  margin-bottom: 16px;
}

.auth-links {
  text-align: center;
  margin-top: 16px;
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.auth-links a {
  color: var(--color-primary-dark);
  font-weight: 600;
  text-decoration: underline;
  text-decoration-color: color-mix(in srgb, var(--color-primary-dark) 36%, transparent);
  text-underline-offset: 0.18em;
}

.auth-links a:hover,
.auth-links a:focus-visible {
  color: var(--color-secondary);
}

@media (max-width: 640px) {
  .auth-card {
    padding: 20px;
  }
}
</style>
