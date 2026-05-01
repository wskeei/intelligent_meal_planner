<template>
  <div class="plan-switcher">
    <el-dropdown
      trigger="click"
      :teleported="true"
      popper-class="plan-switcher__popper"
      @visible-change="onDropdownVisibleChange"
    >
      <button class="plan-switcher__trigger" type="button">
        <span class="plan-switcher__trigger-label">{{ currentPlanName }}</span>
        <el-icon class="plan-switcher__trigger-arrow"><ArrowDown /></el-icon>
      </button>

      <template #dropdown>
        <el-dropdown-menu class="plan-switcher__menu">
          <div
            v-if="plans.length === 0 && !showCreateInput"
            class="plan-switcher__empty"
          >
            {{ t('weekly_plan.no_plans_yet') }}
          </div>

          <div
            v-for="plan in plans"
            :key="plan.id"
            class="plan-switcher__row"
            @click="onSelectPlan(plan.id)"
          >
            <div class="plan-switcher__row-main">
              <el-icon
                v-if="plan.id === activePlanId"
                class="plan-switcher__check"
                :size="14"
              >
                <Check />
              </el-icon>
              <span v-else class="plan-switcher__check-spacer" />
              <span class="plan-switcher__plan-name">{{ plan.name }}</span>
              <span class="plan-switcher__plan-count">
                {{ t('weekly_plan.days_count', { count: plan.day_count }) }}
              </span>
            </div>
            <div
              class="plan-switcher__kebab-wrap"
              @click.stop
            >
              <el-dropdown trigger="click" :teleported="true" @command="onPlanAction($event as string, plan)">
                <button
                  class="plan-switcher__kebab"
                  type="button"
                  :aria-label="t('common.edit')"
                  @click.stop
                >
                  <el-icon :size="16"><MoreFilled /></el-icon>
                </button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="edit">
                      {{ t('weekly_plan.edit_plan') }}
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" divided>
                      {{ t('weekly_plan.delete_plan') }}
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>

          <div v-if="!showCreateInput" class="plan-switcher__create-row">
            <button
              class="plan-switcher__create-btn"
              type="button"
              @click.stop="showCreateInput = true"
            >
              <el-icon :size="14"><Plus /></el-icon>
              <span>{{ t('weekly_plan.new_plan') }}</span>
            </button>
          </div>

          <div v-else class="plan-switcher__create-input-row">
            <input
              ref="createInputRef"
              v-model="newPlanName"
              class="plan-switcher__name-input"
              :placeholder="t('weekly_plan.new_plan_placeholder')"
              maxlength="64"
              @keydown.enter="onCreatePlan"
              @keydown.escape="cancelCreate"
            />
            <button
              class="plan-switcher__confirm-btn"
              type="button"
              :disabled="!newPlanName.trim() || creating"
              @click.stop="onCreatePlan"
            >
              <el-icon v-if="!creating" :size="14"><Check /></el-icon>
              <span v-if="!creating">{{ t('common.confirm') }}</span>
            </button>
          </div>
        </el-dropdown-menu>
      </template>
    </el-dropdown>

    <!-- Edit dialog -->
    <el-dialog
      v-model="editDialogVisible"
      :title="t('weekly_plan.edit_plan')"
      width="360px"
      :close-on-click-modal="false"
      append-to-body
      destroy-on-close
    >
      <div class="plan-switcher__edit-form">
        <div class="plan-switcher__edit-field">
          <label class="plan-switcher__edit-label">{{ t('weekly_plan.new_plan_placeholder') }}</label>
          <input
            v-model="editName"
            class="plan-switcher__name-input"
            :placeholder="t('weekly_plan.new_plan_placeholder')"
            maxlength="64"
            @keydown.enter="onSaveEdit"
          />
        </div>
        <div class="plan-switcher__edit-field">
          <label class="plan-switcher__edit-label">{{ t('weekly_plan.notes_placeholder') }}</label>
          <textarea
            v-model="editNotes"
            class="plan-switcher__notes-input"
            :placeholder="t('weekly_plan.notes_placeholder')"
            rows="3"
          />
        </div>
      </div>
      <template #footer>
        <div class="plan-switcher__edit-footer">
          <el-button @click="editDialogVisible = false">{{ t('common.cancel') }}</el-button>
          <el-button
            type="primary"
            :disabled="!editName.trim() || saving"
            :loading="saving"
            @click="onSaveEdit"
          >
            {{ t('common.save') }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown, Check, MoreFilled, Plus } from '@element-plus/icons-vue'
import { useWeeklyPlanStore } from '@/stores/weeklyPlan'
import type { WeeklyPlanSummary } from '@/api'

const props = defineProps<{
  plans: WeeklyPlanSummary[]
  activePlanId: number | null
}>()

const emit = defineEmits<{
  select: [id: number]
}>()

const { t } = useI18n()
const store = useWeeklyPlanStore()

// --- Current plan display ---
const currentPlanName = computed(() => {
  if (!props.activePlanId) return t('weekly_plan.no_plans_yet')
  const active = props.plans.find((p) => p.id === props.activePlanId)
  return active?.name ?? t('weekly_plan.no_plans_yet')
})

// --- Create inline ---
const showCreateInput = ref(false)
const newPlanName = ref('')
const creating = ref(false)
const createInputRef = ref<HTMLInputElement | null>(null)

watch(showCreateInput, (v) => {
  if (v) {
    nextTick(() => createInputRef.value?.focus())
  }
})

function cancelCreate() {
  showCreateInput.value = false
  newPlanName.value = ''
}

async function onCreatePlan() {
  const name = newPlanName.value.trim()
  if (!name) return
  creating.value = true
  try {
    const created = await store.createPlan(name)
    emit('select', created.id)
    ElMessage.success(t('weekly_plan.create_success'))
    cancelCreate()
  } catch {
    ElMessage.error(t('weekly_plan.errors.create_failed'))
  } finally {
    creating.value = false
  }
}

// --- Plan actions (edit / delete) ---
const editDialogVisible = ref(false)
const editPlanId = ref<number | null>(null)
const editName = ref('')
const editNotes = ref('')
const saving = ref(false)

function onPlanAction(action: string, plan: WeeklyPlanSummary) {
  if (action === 'edit') {
    editPlanId.value = plan.id
    editName.value = plan.name
    editNotes.value = plan.notes ?? ''
    editDialogVisible.value = true
  } else if (action === 'delete') {
    onDeletePlan(plan)
  }
}

async function onSaveEdit() {
  const name = editName.value.trim()
  if (!name || !editPlanId.value) return
  saving.value = true
  try {
    await store.updatePlan(editPlanId.value, { name, notes: editNotes.value })
    ElMessage.success(t('weekly_plan.edit_success'))
    editDialogVisible.value = false
  } catch {
    ElMessage.error(t('weekly_plan.errors.edit_failed'))
  } finally {
    saving.value = false
  }
}

async function onDeletePlan(plan: WeeklyPlanSummary) {
  try {
    await ElMessageBox.confirm(
      t('weekly_plan.delete_confirm_message'),
      t('weekly_plan.delete_confirm_title'),
      { confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel'), type: 'warning' }
    )
  } catch {
    return // user cancelled
  }
  try {
    await store.deletePlan(plan.id)
    ElMessage.success(t('weekly_plan.delete_success'))
  } catch {
    ElMessage.error(t('weekly_plan.errors.delete_failed'))
  }
}

// --- Select plan ---
function onSelectPlan(id: number) {
  emit('select', id)
}

// --- Reset create input when dropdown closes ---
function onDropdownVisibleChange(visible: boolean) {
  if (!visible) {
    cancelCreate()
  }
}
</script>

<style scoped>
.plan-switcher {
  display: inline-flex;
}

/* Trigger button */
.plan-switcher__trigger {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 40px;
  padding: 0 14px;
  border: 1px solid var(--color-border-soft);
  border-radius: 10px;
  background: var(--color-surface-raised);
  color: var(--color-secondary);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  cursor: pointer;
  transition: border-color 0.15s;
  min-width: 0;
}

.plan-switcher__trigger:hover {
  border-color: var(--color-accent);
}

.plan-switcher__trigger:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.plan-switcher__trigger-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plan-switcher__trigger-arrow {
  flex-shrink: 0;
  color: var(--color-text-light);
  font-size: 12px;
  transition: transform 0.2s;
}

/* Dropdown menu */
.plan-switcher__menu {
  min-width: 280px;
  padding: 6px 0;
}

/* Plan row */
.plan-switcher__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 16px;
  cursor: pointer;
  transition: background 0.1s;
}

.plan-switcher__row:hover {
  background: var(--color-surface-raised);
}

.plan-switcher__row-main {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.plan-switcher__check {
  flex-shrink: 0;
  color: var(--color-accent-strong);
}

.plan-switcher__check-spacer {
  flex-shrink: 0;
  width: 14px;
  height: 14px;
}

.plan-switcher__plan-name {
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plan-switcher__plan-count {
  flex-shrink: 0;
  font-size: var(--text-xs);
  color: var(--color-text-light);
}

/* Kebab button */
.plan-switcher__kebab-wrap {
  opacity: 0;
  transition: opacity 0.15s;
}

.plan-switcher__row:hover .plan-switcher__kebab-wrap {
  opacity: 1;
}

@media (hover: none) {
  .plan-switcher__kebab-wrap {
    opacity: 1;
  }
}

.plan-switcher__kebab {
  display: inline-grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--color-text-light);
  cursor: pointer;
  transition: background 0.1s, color 0.1s;
}

.plan-switcher__kebab:hover {
  background: var(--color-border-soft);
  color: var(--color-secondary);
}

/* Empty state */
.plan-switcher__empty {
  padding: 16px;
  text-align: center;
  color: var(--color-text-light);
  font-size: var(--text-sm);
}

/* Create row */
.plan-switcher__create-row {
  border-top: 1px solid var(--color-border-soft);
  margin-top: 4px;
  padding-top: 4px;
}

.plan-switcher__create-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 16px;
  border: none;
  background: transparent;
  color: var(--color-accent-strong);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  cursor: pointer;
  transition: background 0.1s;
}

.plan-switcher__create-btn:hover {
  background: var(--color-surface-raised);
}

/* Inline create input */
.plan-switcher__create-input-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-top: 1px solid var(--color-border-soft);
  margin-top: 4px;
  padding-top: 8px;
}

.plan-switcher__name-input {
  flex: 1;
  min-width: 0;
  padding: 7px 10px;
  border: 1px solid var(--color-border-soft);
  border-radius: 8px;
  background: var(--color-surface-raised);
  color: var(--color-secondary);
  font-size: var(--text-sm);
  outline: none;
  transition: border-color 0.15s;
}

.plan-switcher__name-input:focus {
  border-color: var(--color-accent);
  box-shadow: var(--focus-ring);
}

.plan-switcher__confirm-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
  padding: 7px 12px;
  border: none;
  border-radius: 8px;
  background: var(--color-accent-strong);
  color: var(--color-accent-contrast);
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
  cursor: pointer;
  transition: opacity 0.15s;
  min-height: 34px;
}

.plan-switcher__confirm-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.plan-switcher__confirm-btn:not(:disabled):hover {
  opacity: 0.85;
}

/* Edit dialog form */
.plan-switcher__edit-form {
  display: grid;
  gap: 12px;
}

.plan-switcher__edit-field {
  display: grid;
  gap: 6px;
}

.plan-switcher__edit-label {
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  color: var(--color-text-light);
}

.plan-switcher__notes-input {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--color-border-soft);
  border-radius: 8px;
  background: var(--color-surface-raised);
  color: var(--color-secondary);
  font-size: var(--text-sm);
  font-family: inherit;
  resize: vertical;
  outline: none;
  transition: border-color 0.15s;
  box-sizing: border-box;
}

.plan-switcher__notes-input:focus {
  border-color: var(--color-accent);
  box-shadow: var(--focus-ring);
}

.plan-switcher__edit-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* Responsive */
@media (max-width: 480px) {
  .plan-switcher__menu {
    min-width: 240px;
  }
}
</style>
