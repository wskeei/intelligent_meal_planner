<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <h2 style="text-align: center; margin-bottom: 24px">{{ $t('auth.welcome_back') }}</h2>
      
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
        
        <el-button 
          type="primary" 
          size="large" 
          class="full-width" 
          :loading="loading"
          @click="handleLogin"
        >
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
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const auth = useAuthStore()
const username = ref('')
const password = ref('')
const loading = ref(false)

const handleLogin = async () => {
  if (!username.value || !password.value) {
    ElMessage.warning('Please fill in required fields')
    return
  }
  
  loading.value = true
  const success = await auth.login(username.value, password.value)
  loading.value = false
  
  if (success) {
    ElMessage.success('Login successful')
  } else {
    ElMessage.error('Invalid credentials')
  }
}
</script>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
}

.auth-card {
  width: 100%;
  max-width: 400px;
  padding: 20px;
  border-radius: var(--radius-lg);
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
