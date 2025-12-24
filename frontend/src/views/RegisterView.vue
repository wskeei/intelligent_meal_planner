<template>
  <div class="auth-page">
    <el-card class="auth-card register">
      <h2 style="text-align: center; margin-bottom: 8px">Create Account</h2>
      <p style="text-align: center; margin-bottom: 24px; color: #64748b">Start your personalized health journey</p>
      
      <el-form label-position="top" size="large">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Username">
              <el-input v-model="form.username" />
            </el-form-item>
          </el-col>
           <el-col :span="12">
            <el-form-item label="Email">
              <el-input v-model="form.email" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="Password">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        
        <el-divider>Physical Profile</el-divider>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="Age">
              <el-input-number v-model="form.age" :min="10" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Height (cm)">
              <el-input-number v-model="form.height" :min="100" :max="250" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
             <el-form-item label="Weight (kg)">
              <el-input-number v-model="form.weight" :min="30" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="Gender">
          <el-radio-group v-model="form.gender">
            <el-radio label="male">Male</el-radio>
            <el-radio label="female">Female</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="Activity Level">
           <el-select v-model="form.activity_level" style="width: 100%">
             <el-option label="Sedentary" value="sedentary" />
             <el-option label="Lightly Active" value="light" />
             <el-option label="Moderate" value="moderate" />
             <el-option label="Very Active" value="active" />
           </el-select>
        </el-form-item>

         <el-form-item label="Goal">
           <el-select v-model="form.health_goal" style="width: 100%">
             <el-option label="Healthy Eating" value="healthy" />
             <el-option label="Lose Weight" value="lose_weight" />
             <el-option label="Gain Muscle" value="gain_muscle" />
             <el-option label="Maintain" value="maintain" />
           </el-select>
        </el-form-item>
        
        <el-button 
          type="primary" 
          size="large" 
          class="full-width" 
          :loading="loading"
          @click="handleRegister"
        >
          Create Account
        </el-button>
        
        <div class="auth-links">
          Already have an account? <router-link to="/login">Login</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const auth = useAuthStore()
const router = useRouter()
const loading = ref(false)

const form = reactive({
  username: '',
  email: '',
  password: '',
  age: 25,
  height: 170,
  weight: 65,
  gender: 'male',
  activity_level: 'moderate',
  health_goal: 'healthy'
})

const handleRegister = async () => {
  if (!form.username || !form.password || !form.email) {
    ElMessage.warning('Username, Email and Password are required')
    return
  }
  
  loading.value = true
  const success = await auth.register(form)
  loading.value = false
  
  if (success) {
    ElMessage.success('Account created! Please login.')
    router.push('/login')
  } else {
    ElMessage.error('Registration failed. Username or Email may exist.')
  }
}
</script>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 0;
}

.auth-card {
  width: 100%;
  max-width: 600px; /* Wider for register */
  padding: 20px;
  border-radius: var(--radius-lg);
}

.full-width {
  width: 100%;
  margin-top: 16px;
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
