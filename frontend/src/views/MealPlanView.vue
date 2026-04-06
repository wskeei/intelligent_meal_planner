<template>
  <div class="meal-chat-page" :class="{ 'overlay-active': overlayVisible }">
    <section class="hero-shell">
      <div class="hero-copy">
        <p class="eyebrow">{{ $t('meal_plan.nutritionist') }}</p>
        <h1>{{ $t('meal_plan.chat_title') }}</h1>
        <p class="subtitle">{{ $t('meal_plan.chat_subtitle') }}</p>
      </div>
      <div class="hero-note">
        <span class="note-chip">{{ $t('meal_plan.session_tip') }}</span>
        <span class="note-chip muted">
          {{ $t('meal_plan.profile_progress', { completed: profileCompletionCompleted, total: profileCompletionTotal }) }}
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
            <el-button text type="primary" :disabled="loading" @click="restartSession">
              {{ $t('meal_plan.new_session') }}
            </el-button>
          </div>
        </template>

        <div v-if="reuseSummary" class="reuse-banner">
          <div>
            <p class="reuse-eyebrow">{{ $t('history.reuse_ready') }}</p>
            <p>{{ reuseSummary }}</p>
          </div>
          <el-button text type="primary" @click="draft = reuseDraft">
            {{ $t('meal_plan.use_prefill') }}
          </el-button>
        </div>

        <el-alert
          v-if="sessionError"
          :title="sessionError"
          type="error"
          show-icon
          :closable="false"
          class="inline-alert"
        >
          <template #default>
            <el-button type="primary" text @click="bootstrapSession">{{ $t('common.retry') }}</el-button>
          </template>
        </el-alert>

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

          <div v-if="loading && overlayMode !== 'generating'" class="message-row assistant pending">
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
          <el-alert
            v-if="messageError"
            :title="messageError"
            type="error"
            show-icon
            :closable="false"
            class="inline-alert"
          />

          <el-input
            v-model="draft"
            type="textarea"
            :rows="3"
            resize="none"
            :disabled="!isConversationActive"
            :placeholder="$t('meal_plan.chat_placeholder')"
            @keydown.enter.exact.prevent="sendMessage"
          />
          <div class="composer-actions">
            <p>{{ composerHint }}</p>
            <el-button
              type="primary"
              :loading="loading && overlayMode !== 'generating'"
              :disabled="loading || !isConversationActive || !draft.trim()"
              @click="sendMessage"
            >
              {{ $t('meal_plan.send') }}
            </el-button>
          </div>
        </div>
      </el-card>

      <aside class="result-stack" :class="{ muted: overlayVisible }">
        <el-card class="status-card" shadow="hover">
          <MealChatStatusPanel
            :eyebrow="$t('meal_plan.status_eyebrow')"
            :title="phaseTitle"
            :summary="phaseSummary"
            :known-title="$t('meal_plan.known_title')"
            :missing-title="$t('meal_plan.missing_title')"
            :next-title="$t('meal_plan.next_title')"
            :completed-copy="$t('meal_plan.missing_done')"
            :next-action="nextAction"
            :assistant-hint="followUpPlan?.assistant_message"
            :known-items="knownItems"
            :missing-items="missingItems"
          >
            <template #actions>
              <el-button v-if="!profileComplete" plain @click="$router.push('/profile?onboarding=1')">
                {{ $t('meal_plan.complete_profile') }}
              </el-button>
              <el-button
                v-if="canGenerate"
                type="primary"
                :loading="overlayMode === 'generating'"
                @click="startGenerationSequence"
              >
                {{ $t('meal_plan.generate_plan') }}
              </el-button>
              <el-button
                v-else-if="finalPlan && overlayMode !== 'result'"
                type="primary"
                @click="openResultOverlay"
              >
                {{ $t('meal_plan.view_result') }}
              </el-button>
              <el-button v-if="finalPlan" plain @click="openWeeklyPlanAttach">
                {{ $t('weekly_plan.attach_day') }}
              </el-button>
              <el-button v-if="finalPlan" plain @click="restartSession">
                {{ $t('meal_plan.start_over') }}
              </el-button>
            </template>
          </MealChatStatusPanel>
        </el-card>

        <el-card class="trace-card" shadow="never">
          <template #header>
            <div class="section-head compact">
              <div>
                <h2>{{ $t('meal_plan.crew_title') }}</h2>
                <p>{{ $t('meal_plan.crew_subtitle') }}</p>
              </div>
            </div>
          </template>

          <el-collapse>
            <el-collapse-item :title="$t('meal_plan.trace_toggle')">
              <p v-if="traceUnavailableMessage" class="crew-empty">{{ traceUnavailableMessage }}</p>
              <div v-else-if="crewTrace.length" class="crew-timeline">
                <article v-for="event in crewTrace" :key="`${event.agent}-${event.message}`" class="crew-event">
                  <div class="crew-event-head">
                    <strong>{{ event.agent }}</strong>
                    <span class="crew-status">{{ event.status }}</span>
                  </div>
                  <p>{{ event.message }}</p>
                </article>
              </div>
              <p v-else class="crew-empty">{{ $t('meal_plan.crew_empty') }}</p>
            </el-collapse-item>
          </el-collapse>
        </el-card>
      </aside>
    </section>

    <MealChatGenerationOverlay :visible="overlayMode === 'generating'" />
    <MealChatResultOverlay
      :visible="overlayMode === 'result' && Boolean(finalPlan)"
      :meal-plan="finalPlan"
      :alternatives="planAlternatives"
      :crew-trace="crewTrace"
      :preferences="sessionPreferences"
      @return-to-chat="handleReturnToChat"
      @add-to-list="openWeeklyPlanAttach"
      @start-over="restartSession"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import {
  isUnauthorizedError,
  mealChatApi,
  type ChatMessage,
  type CrewTraceEvent,
  type MealChatSession,
  type MealPlan,
  type NegotiatedMealPlan
} from '@/api'
import MealChatGenerationOverlay from '@/components/meal-chat/MealChatGenerationOverlay.vue'
import MealChatResultOverlay from '@/components/meal-chat/MealChatResultOverlay.vue'
import MealChatStatusPanel from '@/components/meal-chat/MealChatStatusPanel.vue'
import { useAuthStore } from '@/stores/auth'
import { useUserStore } from '@/stores/user'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const userStore = useUserStore()
const {
  profile,
  profileComplete,
  profileCompletionCompleted,
  profileCompletionTotal
} = storeToRefs(userStore)

const sessionId = ref<string | null>(null)
const currentSession = ref<MealChatSession | null>(null)
const optimisticMessages = ref<ChatMessage[] | null>(null)
const draft = ref('')
const loading = ref(false)
const messagesRef = ref<HTMLElement | null>(null)
const hasAppliedReuseDraft = ref(false)
const sessionError = ref('')
const messageError = ref('')
const overlayMode = ref<'hidden' | 'generating' | 'result'>('hidden')
const generationStartedAt = ref<number | null>(null)
const SESSION_STORAGE_KEY = 'meal-chat-active-session-id'
const CANONICAL_MISSING_FIELDS = new Set([
  'gender',
  'age',
  'height',
  'weight',
  'activity_level',
  'health_goal',
  'budget',
  'preferred_tags',
  'disliked_foods'
])

const overlayVisible = computed(() => overlayMode.value !== 'hidden')
const messages = computed(() => optimisticMessages.value ?? currentSession.value?.messages ?? [])

function isNegotiatedMealPlan(mealPlan: MealPlan | NegotiatedMealPlan): mealPlan is NegotiatedMealPlan {
  return 'alternatives' in mealPlan
}

const finalPlan = computed<MealPlan | null>(() => {
  const mealPlan = currentSession.value?.meal_plan
  if (!mealPlan) return null
  return isNegotiatedMealPlan(mealPlan) ? mealPlan.primary : mealPlan
})

const planAlternatives = computed(() => {
  const mealPlan = currentSession.value?.meal_plan
  return mealPlan && isNegotiatedMealPlan(mealPlan) ? mealPlan.alternatives : []
})

const crewTrace = computed<CrewTraceEvent[]>(() => currentSession.value?.crew_trace ?? [])
const sessionProfile = computed<Record<string, unknown>>(() => currentSession.value?.profile_snapshot ?? {})
const sessionPreferences = computed<Record<string, unknown>>(
  () => currentSession.value?.preferences_snapshot ?? {}
)
const knownFacts = computed<Record<string, unknown>>(() => currentSession.value?.known_facts ?? {})
const openQuestions = computed(() => currentSession.value?.open_questions ?? [])
const followUpPlan = computed(() => currentSession.value?.follow_up_plan ?? null)

const canGenerate = computed(() => {
  const value = currentSession.value?.presentation?.can_generate
  return typeof value === 'boolean' ? value : currentSession.value?.status === 'planning_ready'
})

const hasResultOverlay = computed(() => {
  const value = currentSession.value?.presentation?.has_result_overlay
  return typeof value === 'boolean' ? value : currentSession.value?.status === 'finalized'
})

const isConversationActive = computed(() => {
  return (
    Boolean(currentSession.value) &&
    currentSession.value?.status !== 'finalized' &&
    overlayMode.value !== 'generating'
  )
})

const reuseSeed = computed(() => {
  const goal = typeof route.query.reuse_goal === 'string' ? route.query.reuse_goal : ''
  const budget = typeof route.query.reuse_budget === 'string' ? route.query.reuse_budget : ''
  const tags = typeof route.query.reuse_tags === 'string' ? route.query.reuse_tags : ''
  const disliked = typeof route.query.reuse_disliked === 'string' ? route.query.reuse_disliked : ''

  if (!goal && !budget && !tags && !disliked) return null

  return {
    goal,
    budget,
    tags: tags ? tags.split(',').filter(Boolean) : [],
    disliked: disliked ? disliked.split(',').filter(Boolean) : []
  }
})

const reuseDraft = computed(() => {
  if (!reuseSeed.value) return ''

  const parts: string[] = []
  if (reuseSeed.value.goal) {
    parts.push(
      t('meal_plan.reuse_parts.goal', {
        value: t(`meal_plan.goals.${reuseSeed.value.goal}`)
      })
    )
  }
  if (reuseSeed.value.budget) {
    parts.push(
      t('meal_plan.reuse_parts.budget', {
        value: reuseSeed.value.budget
      })
    )
  }
  if (reuseSeed.value.tags.length) {
    parts.push(
      t('meal_plan.reuse_parts.tags', {
        value: reuseSeed.value.tags.join(localeJoiner.value)
      })
    )
  }
  if (reuseSeed.value.disliked.length) {
    parts.push(
      t('meal_plan.reuse_parts.disliked', {
        value: reuseSeed.value.disliked.join(localeJoiner.value)
      })
    )
  }

  return t('meal_plan.reuse_prefill', {
    details: parts.join(sentenceJoiner.value)
  })
})

const reuseSummary = computed(() => {
  if (!reuseSeed.value) return ''

  const parts = []
  if (reuseSeed.value.goal) {
    parts.push(t(`meal_plan.goals.${reuseSeed.value.goal}`))
  }
  if (reuseSeed.value.budget) {
    parts.push(`¥${reuseSeed.value.budget}`)
  }
  if (reuseSeed.value.tags.length) {
    parts.push(reuseSeed.value.tags.join(' / '))
  }

  return parts.join(' · ')
})

const phaseTitle = computed(() => {
  switch (currentSession.value?.status) {
    case 'discovering':
      return t('meal_plan.phase.discovering')
    case 'negotiating':
      return t('meal_plan.phase.negotiating')
    case 'planning':
    case 'planning_ready':
      return t('meal_plan.phase.planning')
    case 'finalized':
      return t('meal_plan.phase.finalized')
    default:
      return t('meal_plan.phase.discovering')
  }
})

const phaseSummary = computed(() => {
  switch (currentSession.value?.status) {
    case 'discovering':
      return t('meal_plan.phase_summary.discovering')
    case 'negotiating':
      return t('meal_plan.phase_summary.negotiating')
    case 'planning':
    case 'planning_ready':
      return t('meal_plan.phase_summary.planning')
    case 'finalized':
      return t('meal_plan.phase_summary.finalized')
    default:
      return t('meal_plan.phase_summary.discovering')
  }
})

const missingFieldKeys = computed<string[]>(() => {
  const value = knownFacts.value.missing_fields
  if (!Array.isArray(value)) return []
  return value.filter(
    (item): item is string => typeof item === 'string' && CANONICAL_MISSING_FIELDS.has(item)
  )
})

const missingItems = computed(() =>
  missingFieldKeys.value.map((field) => ({
    label: fieldLabel(field),
    hint: fieldReason(field)
  }))
)

const knownItems = computed(() => {
  const items: Array<{ label: string; value: string }> = []
  const pushItem = (label: string, value: unknown) => {
    if (value === null || value === undefined || value === '') return
    items.push({ label, value: String(value) })
  }

  pushItem(t('meal_plan.field_labels.health_goal'), goalText(sessionPreferences.value.health_goal))
  pushItem(t('meal_plan.field_labels.budget'), budgetText(sessionPreferences.value.budget))
  pushItem(t('meal_plan.field_labels.gender'), optionText('gender', sessionProfile.value.gender))
  pushItem(t('meal_plan.field_labels.age'), sessionProfile.value.age ? `${sessionProfile.value.age}` : '')
  pushItem(t('meal_plan.field_labels.height'), sessionProfile.value.height ? `${sessionProfile.value.height} cm` : '')
  pushItem(t('meal_plan.field_labels.weight'), sessionProfile.value.weight ? `${sessionProfile.value.weight} kg` : '')
  pushItem(
    t('meal_plan.field_labels.activity_level'),
    optionText('activity_level', sessionProfile.value.activity_level)
  )

  const preferredTags = Array.isArray(sessionPreferences.value.preferred_tags)
    ? sessionPreferences.value.preferred_tags.join(localeJoiner.value)
    : ''
  const dislikedFoods = Array.isArray(sessionPreferences.value.disliked_foods)
    ? sessionPreferences.value.disliked_foods.join(localeJoiner.value)
    : ''

  pushItem(t('meal_plan.field_labels.preferred_tags'), preferredTags)
  pushItem(t('meal_plan.field_labels.disliked_foods'), dislikedFoods)

  return items
})

const nextAction = computed(() => {
  if (currentSession.value?.status === 'finalized') {
    return t('meal_plan.next_after_final')
  }

  if (canGenerate.value) {
    return t('meal_plan.ready_to_generate')
  }

  if (followUpPlan.value?.assistant_message) {
    return followUpPlan.value.assistant_message
  }

  if (openQuestions.value.length) {
    const firstQuestion = openQuestions.value[0]
    const label = CANONICAL_MISSING_FIELDS.has(firstQuestion) ? fieldLabel(firstQuestion) : firstQuestion
    return t('meal_plan.answer_next', { field: label })
  }

  return t('meal_plan.session_tip')
})

const composerHint = computed(() => {
  if (overlayMode.value === 'generating') {
    return t('meal_plan.generation.summary')
  }

  if (!isConversationActive.value) {
    return t('meal_plan.final_hint')
  }

  return reuseSeed.value && !hasAppliedReuseDraft.value
    ? t('meal_plan.prefill_hint')
    : t('meal_plan.draft_hint')
})

const localeJoiner = computed(() => (locale.value === 'en' ? ', ' : '、'))
const sentenceJoiner = computed(() => (locale.value === 'en' ? ', ' : '，'))
const traceUnavailableMessage = computed(() =>
  locale.value === 'en' && crewTrace.value.length ? t('meal_plan.trace_unavailable_locale') : ''
)

function goalText(goal: unknown) {
  return typeof goal === 'string' ? t(`meal_plan.goals.${goal}`) : ''
}

function budgetText(budget: unknown) {
  return budget ? `¥${budget}` : ''
}

function optionText(type: 'gender' | 'activity_level', value: unknown) {
  if (!value || typeof value !== 'string') return ''
  if (type === 'gender') return t(`auth.${value}`)
  return t(`auth.activity.${value}`)
}

function fieldLabel(field: string) {
  return t(`meal_plan.field_labels.${field}`)
}

function fieldReason(field: string) {
  return t(`meal_plan.field_reasons.${field}`)
}

function handleAuthFailure() {
  authStore.logout()
  ElMessage.error(t('meal_plan.auth_required'))
}

function prefersReducedMotion() {
  return (
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  )
}

function minimumGenerationDuration() {
  return prefersReducedMotion() ? 240 : 1400
}

async function waitForMinimumGenerationDuration(startedAt: number, minDuration: number) {
  const elapsed = performance.now() - startedAt
  const remaining = Math.max(0, minDuration - elapsed)

  if (remaining === 0) return

  await new Promise<void>((resolve) => {
    window.setTimeout(resolve, remaining)
  })
}

async function scrollToBottom() {
  await nextTick()
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

function persistSessionId(value: string | null) {
  if (typeof window === 'undefined') return

  if (value) {
    window.localStorage.setItem(SESSION_STORAGE_KEY, value)
    return
  }

  window.localStorage.removeItem(SESSION_STORAGE_KEY)
}

async function restoreSession() {
  if (typeof window === 'undefined') return 'not_restored' as const

  const savedSessionId = window.localStorage.getItem(SESSION_STORAGE_KEY)
  if (!savedSessionId) return 'not_restored' as const

  try {
    const { data } = await mealChatApi.getSession(savedSessionId)
    sessionId.value = data.session_id
    currentSession.value = data
    optimisticMessages.value = null
    overlayMode.value = data.presentation?.overlay_state === 'result' ? 'result' : 'hidden'
    await scrollToBottom()
    return 'restored' as const
  } catch (error) {
    console.error(error)
    if (isUnauthorizedError(error)) {
      handleAuthFailure()
      return 'auth_failed' as const
    }
    persistSessionId(null)
    return 'not_restored' as const
  }
}

async function updatePresentationState(overlayState: 'hidden' | 'result') {
  if (!sessionId.value) return

  try {
    const { data } = await mealChatApi.updatePresentation(sessionId.value, overlayState)
    currentSession.value = data
    persistSessionId(data.session_id)
  } catch (error) {
    console.error(error)
    if (isUnauthorizedError(error)) {
      handleAuthFailure()
    }
  }
}

async function bootstrapSession() {
  loading.value = true
  sessionError.value = ''
  messageError.value = ''
  overlayMode.value = 'hidden'
  generationStartedAt.value = null

  try {
    if (authStore.isAuthenticated && !profile.value.username) {
      await authStore.fetchUser()
    }

    if (!route.query.reuse_goal && !route.query.reuse_budget && !route.query.reuse_tags && !route.query.reuse_disliked) {
      const restoreResult = await restoreSession()
      if (restoreResult === 'restored' || restoreResult === 'auth_failed') return
    }

    const { data } = await mealChatApi.createSession()
    sessionId.value = data.session_id
    currentSession.value = data
    optimisticMessages.value = null
    persistSessionId(data.session_id)

    if (reuseDraft.value && !hasAppliedReuseDraft.value) {
      draft.value = reuseDraft.value
      hasAppliedReuseDraft.value = true
    }

    await scrollToBottom()
  } catch (error) {
    console.error(error)
    if (isUnauthorizedError(error)) {
      handleAuthFailure()
      return
    }
    sessionError.value = t('meal_plan.session_inline_error')
    ElMessage.error(t('meal_plan.session_failed'))
  } finally {
    loading.value = false
  }
}

async function startGenerationSequence() {
  if (!sessionId.value || overlayMode.value === 'generating' || !canGenerate.value) return

  overlayMode.value = 'generating'
  loading.value = true
  messageError.value = ''
  generationStartedAt.value = performance.now()

  try {
    const { data } = await mealChatApi.generateSession(sessionId.value)
    await waitForMinimumGenerationDuration(
      generationStartedAt.value,
      minimumGenerationDuration()
    )
    currentSession.value = data
    persistSessionId(data.session_id)
    optimisticMessages.value = null
    overlayMode.value = data.meal_plan ? 'result' : 'hidden'
    await scrollToBottom()
  } catch (error) {
    console.error(error)
    if (isUnauthorizedError(error)) {
      overlayMode.value = 'hidden'
      handleAuthFailure()
      return
    }
    overlayMode.value = 'hidden'
    messageError.value = t('meal_plan.generation_inline_error')
    ElMessage.error(t('meal_plan.generation_failed'))
  } finally {
    loading.value = false
  }
}

async function sendMessage() {
  if (!sessionId.value || !draft.value.trim() || loading.value || !isConversationActive.value) return

  loading.value = true
  messageError.value = ''
  const content = draft.value.trim()
  draft.value = ''
  optimisticMessages.value = [...messages.value, { role: 'user', content }]

  try {
    await scrollToBottom()
    const { data } = await mealChatApi.sendMessage(sessionId.value, content)
    currentSession.value = data
    persistSessionId(data.session_id)
    optimisticMessages.value = null
    await scrollToBottom()
  } catch (error) {
    console.error(error)
    if (isUnauthorizedError(error)) {
      optimisticMessages.value = null
      draft.value = content
      handleAuthFailure()
      return
    }
    optimisticMessages.value = null
    draft.value = content
    messageError.value = t('meal_plan.message_inline_error')
    ElMessage.error(t('meal_plan.message_failed'))
  } finally {
    loading.value = false
  }
}

async function openResultOverlay() {
  if (!finalPlan.value || !hasResultOverlay.value) return
  overlayMode.value = 'result'
  await updatePresentationState('result')
}

async function handleReturnToChat() {
  overlayMode.value = 'hidden'
  await updatePresentationState('hidden')
}

function openWeeklyPlanAttach() {
  if (!finalPlan.value || !currentSession.value?.session_id) return

  router.push({
    path: '/weekly-plan',
    query: {
      source_session_id: currentSession.value.session_id,
      meal_plan_id: finalPlan.value.id,
      source_label: finalPlan.value.meals.map((meal) => meal.recipe_name).join(' / ')
    }
  })
}

async function restartSession() {
  if (route.query.reuse_goal || route.query.reuse_budget || route.query.reuse_tags || route.query.reuse_disliked) {
    await router.replace({ path: '/meal-plan' })
  }

  overlayMode.value = 'hidden'
  generationStartedAt.value = null
  hasAppliedReuseDraft.value = false
  currentSession.value = null
  optimisticMessages.value = null
  sessionId.value = null
  draft.value = ''
  persistSessionId(null)
  await bootstrapSession()
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

.hero-shell,
.chat-layout,
.result-stack {
  transition:
    filter var(--overlay-enter-duration) var(--overlay-ease),
    transform var(--overlay-enter-duration) var(--overlay-ease),
    opacity var(--overlay-enter-duration) var(--overlay-ease);
}

.meal-chat-page.overlay-active .hero-shell,
.meal-chat-page.overlay-active .chat-layout {
  filter: blur(8px);
  transform: scale(0.985);
  opacity: 0.42;
  pointer-events: none;
  user-select: none;
}

.meal-chat-page.overlay-active .result-stack.muted {
  opacity: 0.36;
}

.hero-shell {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding: clamp(20px, 3vw, 32px);
  border-radius: 28px;
  background:
    radial-gradient(circle at top right, rgba(74, 222, 128, 0.18), transparent 32%),
    linear-gradient(140deg, #ffffff, #f4fbf5 55%, #eef6f1);
  border: 1px solid rgba(34, 197, 94, 0.12);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
}

.hero-copy {
  max-width: 720px;
}

.eyebrow,
.reuse-eyebrow {
  margin: 0 0 8px;
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

.note-chip.muted {
  background: rgba(148, 163, 184, 0.12);
  color: var(--color-text-secondary);
}

.chat-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(320px, 0.95fr);
  gap: 24px;
  align-items: start;
}

.chat-card,
.status-card,
.trace-card {
  border: none;
  border-radius: 24px;
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.08);
}

.status-card {
  background: linear-gradient(160deg, #10251a, #173728);
  color: #effff5;
}

.trace-card {
  background: linear-gradient(180deg, #ffffff, #f7faf8);
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

.reuse-banner {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  padding: 14px 16px;
  border-radius: 18px;
  background: #f7faf8;
  margin-bottom: 18px;
}

.inline-alert {
  margin-bottom: 16px;
}

.reuse-banner p {
  margin: 0;
  color: var(--color-text-secondary);
  line-height: 1.6;
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
  white-space: pre-wrap;
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

.crew-event-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.crew-timeline {
  display: grid;
  gap: 10px;
}

.crew-event {
  padding: 12px 14px;
  border-radius: 14px;
  background: #ffffff;
  border: 1px solid rgba(34, 197, 94, 0.12);
}

.crew-event-head strong {
  color: var(--color-secondary);
}

.crew-event p,
.crew-empty {
  margin: 4px 0 0;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.crew-status {
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(34, 197, 94, 0.12);
  color: #166534;
  font-size: 0.76rem;
  font-weight: 700;
  text-transform: uppercase;
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
  .reuse-banner,
  .section-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .status-card :deep(.el-button) {
    width: 100%;
    min-height: 44px;
  }
}
</style>
