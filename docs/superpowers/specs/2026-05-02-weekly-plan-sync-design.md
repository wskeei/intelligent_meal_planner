# 周计划与看板/记录/报告数据联通设计

## 背景与目标

当前系统中，周计划（`WeeklyPlanDay`）存储的是冻结的配餐 JSON 快照，而看板、记录、报告三大模块都基于 `IntakeRecord` 表读取实际摄入数据。两者完全割裂，导致：

- 用户在周计划中制定了配餐，但无法一键将计划转化为实际摄入记录
- 看板无法反映"计划 vs 实际"的完成情况
- 报告无法基于周计划的执行率进行分析

**目标**：在周计划中增加"完成确认"功能，确认后将当天配餐数据同步到 `IntakeRecord`，使看板、记录、报告能够统一消费实际执行数据。

## 关键决策

| 决策项 | 选择 | 说明 |
|--------|------|------|
| 确认粒度 | 按天整体确认 | 用户勾选当天即表示全天三餐已完成 |
| 关联策略 | 双向引用 | `WeeklyPlanDay` 增加 `completed` 状态，`IntakeRecord` 增加 `source_plan_day_id` |
| 撤销策略 | 支持取消确认 | 取消后自动删除同步的 `IntakeRecord`，恢复未确认状态 |
| 实现方案 | 方案一：直接同步 | 复用现有 `IntakeRecord` 表，通过 `source='plan'` + `source_plan_day_id` 标识来源 |

## 数据模型变更

### 后端（`src/intelligent_meal_planner/db/models.py`）

**`WeeklyPlanDay` 新增字段：**

```python
completed = Column(Boolean, default=False, nullable=False)
completed_at = Column(DateTime, nullable=True)
```

**`IntakeRecord` 新增字段：**

```python
source_plan_day_id = Column(
    Integer,
    ForeignKey("weekly_plan_days.id", ondelete="SET NULL"),
    nullable=True,
)
```

`source` 字段已有值 `'plan'` 时，表示该记录来自周计划同步。`source_plan_day_id` 提供精确追溯能力，为未来"计划偏差分析"打下基础。

### 前端类型（`frontend/src/api/index.ts`）

```typescript
interface WeeklyPlanDay {
  // ... existing fields
  completed: boolean
  completed_at?: string
}

interface IntakeRecord {
  // ... existing fields
  source_plan_day_id?: number
}
```

## API 设计

### 确认完成

```
POST /weekly-plans/{plan_id}/days/{date}/confirm
```

**行为（整个流程在一个数据库事务中执行）：**
1. 查询 `WeeklyPlanDay`，校验状态（不能重复确认）
2. 将 `completed` 设为 `True`，`completed_at` 设为当前时间
3. 遍历 `meal_plan_snapshot` 中的每个 `MealItem`，转换为 `IntakeRecord`
   - `source = 'plan'`
   - `source_plan_day_id = weekly_plan_day.id`
   - `recipe_id` 从 `MealItem` 中提取
   - `meal_type` 从 `MealItem` 中提取（breakfast/lunch/dinner）
   - `portion_size` 从 `MealItem` 中提取（默认 1.0）
   - `actual_calories/protein/carbs/fat` 根据 `recipe` 营养数据和 `portion_size` 计算
   - `date` 为 `WeeklyPlanDay.plan_date`
4. 批量插入 `IntakeRecord`
5. 提交事务 —— 若任何步骤失败（如 Recipe 不存在），整体回滚，`WeeklyPlanDay` 状态不变

**响应：** `200 OK`，返回同步的 `IntakeRecord` 列表概要

### 取消确认

```
POST /weekly-plans/{plan_id}/days/{date}/cancel-confirm
```

**行为（整个流程在一个数据库事务中执行）：**
1. 查询 `WeeklyPlanDay`，校验状态（必须已确认才能取消）
2. 将 `completed` 设为 `False`，`completed_at` 设为 `None`
3. 删除所有 `source='plan' AND source_plan_day_id = weekly_plan_day.id` 的 `IntakeRecord`
4. 提交事务

**响应：** `200 OK`

### 读取时返回完成状态

`GET /weekly-plans/{plan_id}` 和 `GET /weekly-plans/{plan_id}/days/{date}` 的响应中，`WeeklyPlanDay` 对象自然包含 `completed` 和 `completed_at` 字段。

## 前端交互设计

### 周计划视图（`WeeklyPlanView.vue / DaySection.vue`）

每天卡片右上角增加一个勾选按钮：

- **未确认状态**：显示空心勾选框 + 文字"确认完成"。点击后弹出二次确认对话框："确认将今天配餐同步到饮食记录？同步后可在看板和报告中查看。"
- **已确认状态**：显示实心勾选框 + 绿色文字"已完成" + 完成时间（如"昨天 19:30"）。点击后弹出选项：取消确认 / 关闭。
- **未来日期**：允许确认（用户可以提前标记），但建议显示浅色提示"提前确认"
- **过去日期**：允许补确认，无特殊限制

**加载状态**：确认/取消请求期间，勾选按钮显示旋转动画，禁止重复点击。

### 看板视图（`DashboardView.vue`）

看板本身无需 UI 改动。因为同步数据进入 `IntakeRecord` 后，`DailySummary`、`NutritionChart`、`WeeklyDashboard` 会自然展示这些数据。

**可选增强（V2）**：在 `WeeklyDashboard` 中增加"计划完成率"指标（已完成天数 / 总计划天数），需要额外查询 `WeeklyPlanDay`。

### 记录视图（`IntakeLogView.vue`）

同步过来的记录显示在今日记录列表中。`QuickLog.vue` 中添加一条来源标签逻辑：
- `source='plan'` 时显示标签"来自周计划"
- `source='manual'` 时显示标签"手动记录"

**可选增强（V2）**：在记录卡片上显示"已关联周计划"标识，点击可跳转回周计划对应日期。

### 报告视图（`ReportView.vue`）

报告本身无需改动。因为 `ReportGenerator` 查询 `IntakeRecord`，同步后的数据自然被纳入统计。

**可选增强（V2）**：在周报中增加"计划执行分析"段落，计算当周计划完成率、平均偏差等。

## 数据流

### 确认完成流程

```
用户点击"确认完成"
  → DaySection 调用 weeklyPlanApi.confirmDay(plan_id, date)
  → POST /weekly-plans/{plan_id}/days/{date}/confirm
  → WeeklyPlanService.confirm_day()
    1. 读取 WeeklyPlanDay
    2. 校验：如果 completed=True，抛 409 Conflict
    3. 解析 meal_plan_snapshot JSON
    4. 对每个 MealItem：
       - 查 Recipe 表获取营养数据
       - 按 portion_size 计算实际摄入
       - 构建 IntakeRecord(source='plan', source_plan_day_id=day.id)
    5. 批量插入 IntakeRecord
    6. 更新 WeeklyPlanDay(completed=True, completed_at=now())
  → 返回 200 + 同步记录数
  → DaySection 更新本地状态（completed=true）
  → dashboardStore.loadAll() 触发重新加载（可选：自动刷新看板数据）
```

### 取消确认流程

```
用户点击"已完成" → 选择"取消确认"
  → DaySection 调用 weeklyPlanApi.cancelConfirm(plan_id, date)
  → POST /weekly-plans/{plan_id}/days/{date}/cancel-confirm
  → WeeklyPlanService.cancel_confirm()
    1. 读取 WeeklyPlanDay
    2. 校验：如果 completed=False，抛 409 Conflict
    3. 删除 IntakeRecord WHERE source='plan' AND source_plan_day_id=day.id
    4. 更新 WeeklyPlanDay(completed=False, completed_at=None)
  → 返回 200
  → DaySection 更新本地状态（completed=false）
  → dashboardStore.loadAll() 触发重新加载
```

### 前端 Store 联动

确认/取消操作后，建议自动触发 `dashboardStore.loadAll()` 和 `dashboardStore.loadTodayRecords()`，使看板和记录视图保持同步。这可以通过在 `useWeeklyPlanStore` 的 `confirmDay` / `cancelConfirm` action 中调用 `useDashboardStore().loadAll()` 实现。

## 看板/记录/报告的消费逻辑

### 看板（DashboardService）

**无需改动**。`daily_summary()` 和 `weekly_summary()` 继续查询 `IntakeRecord`，同步后的数据自然被纳入统计。

**V2 增强**：`weekly_summary()` 可以额外查询 `WeeklyPlanDay`，计算：
- `plan_completion_rate`: 已完成天数 / 有计划的天数
- `planned_vs_actual`: 计划营养 vs 实际营养的偏差

### 记录（IntakeTracker）

**无需改动**。`get_daily()` 和 `get_records()` 继续返回所有 `IntakeRecord`，包括 `source='plan'` 的。

**注意**：用户在记录视图中手动编辑或删除 `source='plan'` 的记录时，不会影响 `WeeklyPlanDay` 的 `completed` 状态。这是一个已知的行为边界——周计划的"完成状态"和实际记录的"存在性"是弱一致的。如果用户删除了一条 plan 来源的记录，周计划仍然显示"已完成"。V2 可以考虑增加一个后台校验或状态提示。

### 报告（ReportGenerator）

**无需改动**。`generate_weekly_report()` 和 `generate_monthly_report()` 查询 `IntakeRecord`，同步数据自然纳入。

**V2 增强**：报告中增加"周计划执行分析"章节，展示：
- 计划完成天数 / 总计划天数
- 每餐的按时完成率
- 计划 vs 实际的营养偏差（RMSE 或平均绝对误差）

## 错误处理

| 场景 | 行为 |
|------|------|
| 重复确认 | 后端返回 `409 Conflict`，前端提示"当天已完成确认" |
| 取消未确认的天 | 后端返回 `409 Conflict`，前端提示"当天尚未确认" |
| WeeklyPlanDay 不存在 | 后端返回 `404 Not Found` |
| meal_plan_snapshot 为空 | 后端返回 `422 Unprocessable Entity`，提示"当天没有配餐，无法确认" |
| 同步时 Recipe 不存在 | 后端返回 `422`，提示"菜谱数据异常"（防御性处理，正常不应发生） |
| 网络异常 | 前端显示错误 Toast，本地状态不更新，用户可重试 |
| 取消确认时 IntakeRecord 已被用户手动删除部分 | 仅删除仍存在的记录，不报错，正常完成取消流程 |

## 测试策略

### 后端测试

1. **确认成功**：`WeeklyPlanDay.completed` 变为 True，`IntakeRecord` 正确创建，营养计算准确
2. **取消成功**：`WeeklyPlanDay.completed` 变为 False，关联 `IntakeRecord` 被删除
3. **重复确认**：第二次确认返回 409
4. **取消未确认**：返回 409
5. **空计划确认**：`meal_plan_snapshot` 为空时返回 422
6. **批量同步营养计算**：验证 portion_size 不为 1.0 时的营养值缩放正确

### 前端测试

1. **UI 状态切换**：未确认 → 确认中（loading） → 已确认 → 取消确认
2. **二次确认对话框**：确认和取消操作前均有对话框拦截
3. **Store 联动**：确认后看板数据自动刷新
4. **错误提示**：网络错误、409 错误均有 Toast 提示

### 集成测试

1. 完整流程：生成配餐 → 添加到周计划 → 确认完成 → 看板显示数据 → 报告中包含数据 → 取消确认 → 看板数据消失

## 数据库迁移

新增 Alembic migration：

```python
# 在 weekly_plan_days 表添加列
op.add_column('weekly_plan_days', sa.Column('completed', sa.Boolean(), nullable=False, server_default='false'))
op.add_column('weekly_plan_days', sa.Column('completed_at', sa.DateTime(), nullable=True))

# 在 intake_records 表添加列
op.add_column('intake_records', sa.Column('source_plan_day_id', sa.Integer(), nullable=True))
op.create_foreign_key('fk_intake_records_plan_day', 'intake_records', 'weekly_plan_days', ['source_plan_day_id'], ['id'], ondelete='SET NULL')
```

## 影响范围总结

| 模块 | 改动量 | 说明 |
|------|--------|------|
| 数据模型 | 小 | 2 个表各加 1-2 个字段 |
| 后端 API | 中 | 新增 2 个 endpoint，修改 1 个 service |
| 周计划前端 | 中 | DaySection 增加勾选交互，Store 增加 action |
| 看板前端 | 无 | 数据同步后自然消费 |
| 记录前端 | 极小 | 可选：增加来源标签显示 |
| 报告前端 | 无 | 数据同步后自然消费 |
| 数据库 | 小 | 1 个 migration |

## 版本规划

- **V1（本设计）**：完成确认/取消确认、数据同步到 IntakeRecord、基础联动
- **V2**：看板增加"计划完成率"、报告增加"计划执行分析"、记录显示周计划来源标识
