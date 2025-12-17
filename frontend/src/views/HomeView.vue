<template>
  <div class="home">
    <!-- Hero Section -->
    <div class="hero">
      <h1>🍽️ 智能配餐系统</h1>
      <p class="subtitle">基于强化学习与多Agent协作的个性化配餐推荐</p>
      <el-button type="primary" size="large" @click="$router.push('/meal-plan')">
        <el-icon><MagicStick /></el-icon>
        开始配餐
      </el-button>
    </div>

    <!-- Features -->
    <el-row :gutter="20" class="features">
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon :size="32" color="#409EFF"><Cpu /></el-icon>
              <span>强化学习算法</span>
            </div>
          </template>
          <p>采用深度Q网络(DQN)算法，通过数万次模拟学习最优配餐策略，智能平衡营养、预算和口味。</p>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon :size="32" color="#67C23A"><UserFilled /></el-icon>
              <span>多Agent协作</span>
            </div>
          </template>
          <p>用户分析师Agent理解您的需求，配餐师Agent调用AI模型，两者协作为您定制专属方案。</p>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon :size="32" color="#E6A23C"><TrendCharts /></el-icon>
              <span>营养可视化</span>
            </div>
          </template>
          <p>直观展示营养达成情况，卡路里、蛋白质、碳水、脂肪一目了然，助您科学饮食。</p>
        </el-card>
      </el-col>
    </el-row>

    <!-- Quick Start -->
    <div class="quick-start">
      <h2>快速开始</h2>
      <el-row :gutter="20">
        <el-col :span="6" v-for="goal in healthGoals" :key="goal.value">
          <el-card 
            shadow="hover" 
            class="goal-card"
            @click="quickPlan(goal.value)"
          >
            <div class="goal-icon">{{ goal.icon }}</div>
            <div class="goal-name">{{ goal.label }}</div>
            <div class="goal-desc">{{ goal.desc }}</div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { MagicStick, Cpu, UserFilled, TrendCharts } from '@element-plus/icons-vue'

const router = useRouter()

const healthGoals = [
  { value: 'lose_weight', label: '减脂瘦身', icon: '🏃', desc: '低卡高蛋白' },
  { value: 'gain_muscle', label: '增肌塑形', icon: '💪', desc: '高蛋白高热量' },
  { value: 'maintain', label: '维持体重', icon: '⚖️', desc: '均衡营养' },
  { value: 'healthy', label: '健康饮食', icon: '🥗', desc: '标准健康餐' }
]

const quickPlan = (goal: string) => {
  router.push({ path: '/meal-plan', query: { goal } })
}
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
}

.hero {
  text-align: center;
  padding: 60px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  color: white;
  margin-bottom: 40px;
}

.hero h1 {
  font-size: 42px;
  margin-bottom: 16px;
}

.subtitle {
  font-size: 18px;
  opacity: 0.9;
  margin-bottom: 30px;
}

.features {
  margin-bottom: 40px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: bold;
}

.quick-start {
  text-align: center;
}

.quick-start h2 {
  margin-bottom: 24px;
  color: #303133;
}

.goal-card {
  cursor: pointer;
  transition: transform 0.3s;
  text-align: center;
}

.goal-card:hover {
  transform: translateY(-5px);
}

.goal-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.goal-name {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 8px;
}

.goal-desc {
  color: #909399;
  font-size: 14px;
}
</style>