<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <p class="eyebrow">{{ $t('auth.product_name') }}</p>
      <h1>{{ $t('auth.welcome_back') }}</h1>
      <p class="subtitle">{{ $t('auth.login_intro') }}</p>

      <el-form label-position="top" @submit.prevent>
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

const redirectTarget = computed(() =>
  typeof route.query.redirect === 'string' ? route.query.redirect : '/'
)

async function handleLogin() {
  if (!username.value || !password.value) {
    ElMessage.warning(t('auth.login_missing'))
    return
  }

  loading.value = true
  const success = await auth.login(username.value, password.value, {
    redirectTo: redirectTarget.value
  })
  loading.value = false

  if (success) {
    ElMessage.success(t('auth.login_success'))
  } else {
    ElMessage.error(t('auth.login_failed'))
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
  max-width: 440px;
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
  margin: 12px 0 24px;
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
