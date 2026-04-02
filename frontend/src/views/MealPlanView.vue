<template>
  <div class="meal-chat-page">
    <section class="hero-shell">
      <div class="hero-copy">
        <p class="eyebrow">{{ $t('meal_plan.nutritionist') }}</p>
        <h1>{{ $t('meal_plan.chat_title') }}</h1>
        <p class="subtitle">{{ $t('meal_plan.chat_subtitle') }}</p>
      </div>
      <div class="hero-note">
        <span class="note-chip">{{ $t('meal_plan.session_tip') }}</span>
        <span class="note-chip muted">
          {{ profileComplete ? $t('meal_plan.sync_profile') : $t('dashboard.profile_missing') }}
        </span>
      </div>
    </section>

    <section class="chat-layout">
      <el-card class="chat-card" shadow="hover">
        <template #header>
          <div class="section-head">
            <div>
              <h2>{{ $t('meal_plan.chat_title') }}</h2>
              <p>{{ $t('meal_plan.goal_summary') }}</p>
            </div>
            <el-button text type="primary" :disabled="loading" @click="bootstrapSession">
              {{ $t('meal_plan.new_session') }}
            </el-button>
          </div>
        </template>

        <div ref="messagesRef" class="messages">
          <div
            v-for="(message, index) in messages"
            :key="`${message.role}-${index}-${message.created_at ?? 'local'}`"
            :class="['message-row', message.role]"
          >
            <div class="message-meta">
              <span>{{ message.role === 'assistant' ? $t('meal_plan.nutritionist') : profile.username || $t('common.you') }}</span>
            </div>
            <div class="bubble">
              {{ message.content }}
            </div>
          </div>

          <div v-if="loading" class="message-row assistant pending">
            <div class="message-meta">
              <span>{{ $t('meal_plan.nutritionist') }}</span>
            </div>
            <div class="bubble pending-bubble">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </div>
          </div>
        </div>

        <div class="composer">
          <el-input
            v-model="draft"
            type="textarea"
            :rows="3"
            resize="none"
            :placeholder="$t('meal_plan.chat_placeholder')"
            @keydown.enter.exact.prevent="sendMessage"
          />
          <div class="composer-actions">
            <p>{{ $t('meal_plan.draft_hint') }}</p>
            <el-button type="primary" :loading="loading" @click="sendMessage">
              {{ $t('meal_plan.send') }}
            </el-button>
          </div>
        </div>
      </el-card>

      <aside class="result-stack">
        <el-card class="status-card" shadow="hover">
          <p class="eyebrow muted">{{ $t('meal_plan.final_plan') }}</p>
          <h3>{{ finalPlan ? $t('meal_plan.budget_safe_hint') : $t('meal_plan.awaiting_reply') }}</h3>
          <p class="status-copy">
            {{ finalPlan ? goalLabel : $t('meal_plan.session_tip') }}
          </p>
        </el-card>

        <el-card v-if="finalPlan" class="result-card" shadow="hover">
          <template #header>
            <div class="section-head compact">
              <div>
                <h2>{{ $t('meal_plan.final_plan') }}</h2>
                <p>{{ $t('meal_plan.budget_safe_hint') }}</p>
              </div>
              <div class="price-pill">¥{{ finalPlan.nutrition.total_price.toFixed(1) }}</div>
            </div>
          </template>

          <div class="meal-groups">
            <section v-for="group in groupedMeals" :key="group.key" class="meal-group">
              <div class="meal-group-head">
                <span class="meal-label">{{ mealLabel(group.key) }}</span>
                <span class="meal-count">{{ group.items.length }} {{ $t('meal_plan.items') }}</span>
              </div>

              <div class="meal-list">
                <article v-for="meal in group.items" :key="`${group.key}-${meal.recipe_id}`" class="meal-item">
                  <div>
                    <p class="meal-name">{{ meal.recipe_name }}</p>
                    <p class="meal-metrics">
                      {{ meal.calories.toFixed(0) }} kcal · {{ meal.protein.toFixed(0) }}g P
                    </p>
                  </div>
                  <strong>¥{{ meal.price.toFixed(1) }}</strong>
                </article>
              </div>
            </section>
          </div>

          <div class="summary-row">
            <span>{{ $t('meal_plan.total_cost') }}</span>
            <strong>¥{{ finalPlan.nutrition.total_price.toFixed(1) }}</strong>
          </div>
        </el-card>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

import { mealChatApi, type ChatMessage, type MealPlan } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useUserStore } from '@/stores/user'

const { t } = useI18n()
const authStore = useAuthStore()
const userStore = useUserStore()
const { profile, profileComplete } = storeToRefs(userStore)

const sessionId = ref<string | null>(null)
const messages = ref<ChatMessage[]>([])
const draft = ref('')
const loading = ref(false)
const finalPlan = ref<MealPlan | null>(null)
const messagesRef = ref<HTMLElement | null>(null)

const groupedMeals = computed(() => {
  const order = ['breakfast', 'lunch', 'dinner']
  const buckets = new Map<string, NonNullable<MealPlan['meals']>>()

  if (!finalPlan.value) return []

  for (const meal of finalPlan.value.meals) {
    const list = buckets.get(meal.meal_type) ?? []
    list.push(meal)
    buckets.set(meal.meal_type, list)
  }

  return order
    .filter((key) => buckets.has(key))
    .map((key) => ({ key, items: buckets.get(key) ?? [] }))
})

const goalLabel = computed(() => {
  const goal = finalPlan.value?.target.health_goal ?? profile.value.goal
  return t(`meal_plan.goals.${goal}`)
})

function mealLabel(type: string) {
  return t(`recipes.${type}`)
}

async function scrollToBottom() {
  await nextTick()
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

async function bootstrapSession() {
  loading.value = true
  try {
    if (authStore.isAuthenticated && !profile.value.username) {
      await authStore.fetchUser()
    }

    const { data } = await mealChatApi.createSession()
    sessionId.value = data.session_id
    messages.value = data.messages
    finalPlan.value = data.meal_plan
    await scrollToBottom()
  } catch (error) {
    console.error(error)
    ElMessage.error(t('meal_plan.session_failed'))
  } finally {
    loading.value = false
  }
}

async function sendMessage() {
  if (!sessionId.value || !draft.value.trim() || loading.value) return

  loading.value = true
  const content = draft.value.trim()
  draft.value = ''
  messages.value = [...messages.value, { role: 'user', content }]

  try {
    await scrollToBottom()
    const { data } = await mealChatApi.sendMessage(sessionId.value, content)
    messages.value = data.messages
    finalPlan.value = data.meal_plan
    await scrollToBottom()
  } catch (error) {
    console.error(error)
    messages.value = messages.value.slice(0, -1)
    draft.value = content
    ElMessage.error(t('meal_plan.message_failed'))
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await bootstrapSession()
})
</script>

<style scoped>
.meal-chat-page {
  display: grid;
  gap: 24px;
}

.hero-shell {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding: clamp(20px, 3vw, 32px);
  border-radius: 28px;
  background:
    radial-gradient(circle at top right, rgba(74, 222, 128, 0.22), transparent 30%),
    linear-gradient(140deg, #ffffff, #f4fbf5 55%, #eef6f1);
  border: 1px solid rgba(34, 197, 94, 0.12);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
}

.hero-copy {
  max-width: 720px;
}

.eyebrow {
  margin-bottom: 8px;
  color: var(--color-primary-dark);
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.hero-copy h1 {
  margin: 0;
  color: var(--color-secondary);
  font-size: clamp(2rem, 4vw, 3.2rem);
  line-height: 1.02;
}

.subtitle {
  margin-top: 14px;
  color: var(--color-text-secondary);
  font-size: 1rem;
  line-height: 1.7;
}

.hero-note {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: flex-end;
  min-width: 220px;
}

.note-chip {
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(34, 197, 94, 0.12);
  color: #166534;
  font-size: 0.9rem;
  font-weight: 600;
}

.note-chip.muted,
.eyebrow.muted {
  background: rgba(148, 163, 184, 0.12);
  color: var(--color-text-secondary);
}

.chat-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(300px, 0.9fr);
  gap: 24px;
  align-items: start;
}

.chat-card,
.status-card,
.result-card {
  border: none;
  border-radius: 24px;
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.08);
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.section-head h2 {
  margin: 0;
  font-size: 1.2rem;
  color: var(--color-secondary);
}

.section-head p {
  margin: 4px 0 0;
  color: var(--color-text-secondary);
  font-size: 0.92rem;
}

.messages {
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-height: 58vh;
  min-height: 420px;
  overflow: auto;
  padding-right: 6px;
}

.message-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 80%;
}

.message-row.user {
  align-self: flex-end;
}

.message-meta {
  color: var(--color-text-light);
  font-size: 0.82rem;
  font-weight: 600;
}

.bubble {
  padding: 16px 18px;
  border-radius: 20px;
  background: #f7faf8;
  color: var(--color-text-main);
  line-height: 1.7;
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.message-row.user .bubble {
  background: linear-gradient(135deg, var(--color-primary-dark), var(--color-primary));
  color: #052e16;
  border: none;
}

.pending-bubble {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary-dark);
  opacity: 0.35;
  animation: pulse 1.1s infinite ease-in-out;
}

.dot:nth-child(2) {
  animation-delay: 0.12s;
}

.dot:nth-child(3) {
  animation-delay: 0.24s;
}

.composer {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
}

.composer-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 12px;
}

.composer-actions p {
  color: var(--color-text-light);
  font-size: 0.84rem;
}

.result-stack {
  display: grid;
  gap: 16px;
}

.status-card {
  background: linear-gradient(160deg, #10251a, #173728);
  color: #effff5;
}

.status-card h3 {
  margin: 8px 0 10px;
  font-size: 1.2rem;
}

.status-copy {
  color: rgba(239, 255, 245, 0.78);
  line-height: 1.6;
}

.price-pill {
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(34, 197, 94, 0.12);
  color: var(--color-primary-dark);
  font-weight: 700;
}

.meal-groups {
  display: grid;
  gap: 16px;
}

.meal-group {
  padding: 16px;
  border-radius: 18px;
  background: #f8fbf8;
}

.meal-group-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.meal-label {
  color: var(--color-secondary);
  font-weight: 700;
}

.meal-count {
  color: var(--color-text-light);
  font-size: 0.82rem;
}

.meal-list {
  display: grid;
  gap: 10px;
}

.meal-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 14px;
  background: #ffffff;
}

.meal-name {
  margin: 0;
  font-weight: 700;
  color: var(--color-secondary);
}

.meal-metrics {
  margin: 4px 0 0;
  color: var(--color-text-secondary);
  font-size: 0.84rem;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
  color: var(--color-text-secondary);
}

.summary-row strong {
  color: var(--color-secondary);
  font-size: 1.1rem;
}

@keyframes pulse {
  0%,
  80%,
  100% {
    transform: translateY(0);
    opacity: 0.25;
  }
  40% {
    transform: translateY(-4px);
    opacity: 1;
  }
}

@media (max-width: 960px) {
  .hero-shell,
  .chat-layout {
    grid-template-columns: 1fr;
    display: grid;
  }

  .hero-note {
    align-items: flex-start;
  }

  .messages {
    max-height: 48vh;
    min-height: 360px;
  }
}

@media (max-width: 640px) {
  .message-row {
    max-width: 100%;
  }

  .composer-actions,
  .meal-group-head,
  .summary-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .price-pill {
    align-self: flex-start;
  }
}
</style>
