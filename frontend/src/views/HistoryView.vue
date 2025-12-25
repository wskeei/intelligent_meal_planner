<template>
  <div class="history">
    <el-card>
      <template #header>
        <div class="header">
          <span>{{ $t('history.title') }}</span>
          <el-button type="danger" :disabled="!history.length" @click="clearHistory">
            {{ $t('history.clear') }}
          </el-button>
        </div>
      </template>

      <el-empty v-if="!history.length" :description="$t('history.empty')">
        <el-button type="primary" @click="$router.push('/meal-plan')">{{ $t('history.go_generate') }}</el-button>
      </el-empty>

      <el-timeline v-else>
        <el-timeline-item
          v-for="(item, index) in history"
          :key="index"
          :timestamp="item.timestamp"
          placement="top"
        >
          <el-card shadow="hover">
            <div class="history-header">
              <el-tag>{{ item.health_goal }}</el-tag>
              <span class="budget">{{ $t('history.budget') }}: ¥{{ item.budget }}</span>
            </div>
            
            <el-row :gutter="16" class="meals">
              <el-col :span="8" v-for="(meal, mealType) in item.meals" :key="mealType">
                <div class="meal-item">
                  <div class="meal-type">{{ $t('recipes.' + (mealType as string)) }}</div>
                  <div class="meal-name">{{ meal.name }}</div>
                  <div class="meal-info">
                    {{ meal.calories }} kcal | ¥{{ meal.price }}
                  </div>
                </div>
              </el-col>
            </el-row>

            <el-divider />
            
            <div class="summary">
              <span>{{ $t('history.total_calories') }}: <strong>{{ item.total_calories }}</strong> kcal</span>
              <span>{{ $t('history.total_price') }}: <strong>¥{{ item.total_price }}</strong></span>
            </div>

            <div class="actions">
              <el-button size="small" @click="reuse(item)">{{ $t('history.reuse') }}</el-button>
              <el-button size="small" type="danger" @click="removeItem(index)">{{ $t('common.delete') }}</el-button>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface HistoryItem {
  timestamp: string
  health_goal: string
  budget: number
  meals: Record<string, { name: string; calories: number; price: number }>
  total_calories: number
  total_price: number
}

const router = useRouter()
const history = ref<HistoryItem[]>([])

onMounted(() => {
  loadHistory()
})

const loadHistory = () => {
  const saved = localStorage.getItem('meal_plan_history')
  if (saved) {
    history.value = JSON.parse(saved)
  }
}

const saveHistory = () => {
  localStorage.setItem('meal_plan_history', JSON.stringify(history.value))
}

const clearHistory = async () => {
  try {
    await ElMessageBox.confirm(t('history.confirm_clear'), t('history.prompt'), {
      type: 'warning'
    })
    history.value = []
    saveHistory()
    ElMessage.success(t('history.cleared'))
  } catch {
    // Cancelled
  }
}

const removeItem = (index: number) => {
  history.value.splice(index, 1)
  saveHistory()
  ElMessage.success(t('history.deleted'))
}

const reuse = (item: HistoryItem) => {
  router.push({
    path: '/meal-plan',
    query: {
      health_goal: item.health_goal,
      budget: item.budget
    }
  })
}
</script>

<style scoped>
.history {
  max-width: 900px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.budget {
  color: #E6A23C;
  font-weight: bold;
}

.meals {
  margin: 16px 0;
}

.meal-item {
  text-align: center;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.meal-type {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.meal-name {
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.meal-info {
  font-size: 12px;
  color: #606266;
}

.summary {
  display: flex;
  justify-content: space-around;
  color: #606266;
}

.summary strong {
  color: #409EFF;
}

.actions {
  margin-top: 16px;
  text-align: right;
}
</style>