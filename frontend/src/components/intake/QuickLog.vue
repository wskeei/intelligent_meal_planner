<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { recipeApi, intakeApi, type Recipe } from '@/api'

const emit = defineEmits<{ logged: [] }>()

const mealType = ref('lunch')
const selectedRecipe = ref<number | null>(null)
const portionSize = ref(1.0)
const recipes = ref<Recipe[]>([])
const loading = ref(false)

onMounted(async () => {
  const { data } = await recipeApi.getList({ limit: 50 })
  recipes.value = data.items
})

async function submit() {
  if (!selectedRecipe.value) return
  loading.value = true
  try {
    await intakeApi.quickLog({
      date: new Date().toISOString().slice(0, 10),
      recipe_id: selectedRecipe.value,
      portion_size: portionSize.value,
      meal_type: mealType.value,
    })
    selectedRecipe.value = null
    portionSize.value = 1.0
    emit('logged')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="quick-log">
    <h2>{{ $t('nutrition.quick_log') }}</h2>
    <el-form :inline="true" @submit.prevent="submit">
      <el-form-item>
        <el-select v-model="mealType" style="width: 120px">
          <el-option :label="$t('meal_types.breakfast')" value="breakfast" />
          <el-option :label="$t('meal_types.lunch')" value="lunch" />
          <el-option :label="$t('meal_types.dinner')" value="dinner" />
          <el-option :label="$t('nutrition.snack')" value="snack" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-select v-model="selectedRecipe" filterable :placeholder="$t('nutrition.select_recipe')" style="width: 200px">
          <el-option v-for="r in recipes" :key="r.id" :label="r.name" :value="r.id" />
        </el-select>
      </el-form-item>
      <el-form-item :label="$t('nutrition.portion')">
        <el-input-number v-model="portionSize" :min="0.5" :max="3" :step="0.5" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="loading" @click="submit">
          {{ $t('nutrition.log') }}
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.quick-log {
  padding: 16px;
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
}
</style>
