# DQN Autoresearch Workflow

自动化 DQN 训练实验循环：训练 -> 评估 -> 记录 -> 决策（保留/丢弃）。

## 模块结构

```
src/intelligent_meal_planner/rl/autoresearch/
├── __init__.py        # 模块导出
├── benchmark.py       # 基准测试场景与评分函数
├── evaluator.py       # 确定性评估器
├── runner.py          # 单次实验运行器（训练 + 评估 + 保存）
└── loop.py            # 循环日志工具（TSV 记录 + 保留/丢弃逻辑）

scripts/
├── run_dqn_autoresearch_experiment.py   # 单次实验 CLI
└── dqn_autoresearch_loop.py             # 多次循环 CLI
```

## 快速开始

> **环境要求**：使用 conda ai_lab 环境 + RTX 4060 GPU 训练。
> 激活环境：`conda activate ai_lab`

### 单次实验

```bash
conda activate ai_lab

# 短暂 smoke test（2000 步）
python scripts/run_dqn_autoresearch_experiment.py --timesteps 2000 --run-id smoke

# 正式实验（50000 步）
python scripts/run_dqn_autoresearch_experiment.py --timesteps 50000 --run-id exp001 --desc "baseline config"
```

输出保存至 `models/autoresearch/<run-id>/summary.json`。

### 多次循环实验

```bash
conda activate ai_lab

# 运行 5 轮实验，每轮 50000 步
python scripts/dqn_autoresearch_loop.py --iterations 5 --timesteps 50000

# 自定义基线分数
python scripts/dqn_autoresearch_loop.py --iterations 10 --timesteps 100000 --baseline-score 60.0
```

循环结果追加至 `models/autoresearch/results.tsv`。

## 基准测试场景

评估使用 5 个固定场景覆盖不同用户需求：

| 场景 | 目标热量 | 预算 | 蛋白质 | 特点 |
|------|---------|------|--------|------|
| standard | 2000 kcal | 100 元 | 100g | 标准饮食 |
| low_budget | 1800 kcal | 60 元 | 80g | 低预算 |
| high_protein | 2200 kcal | 120 元 | 150g | 高蛋白健身 |
| low_calorie | 1500 kcal | 80 元 | 75g | 低卡减脂 |
| generous_budget | 2500 kcal | 200 元 | 120g | 宽松预算 |

## 评分函数

综合得分由四个指标加权计算：

| 指标 | 权重 | 说明 |
|------|------|------|
| 热量准确度 | 30% | 越接近目标越高 |
| 预算合规率 | 25% | 未超支场景占比 |
| 菜品多样性 | 15% | 类别多样性评分 |
| 平均奖励 | 30% | 环境回报均值 |

## 结果解读

### summary.json 字段

| 字段 | 说明 |
|------|------|
| `aggregate_score` | 综合评分（0-100，越高越好） |
| `avg_reward` | 基准场景平均奖励 |
| `calorie_error_pct` | 平均热量误差百分比 |
| `budget_violation_rate` | 超预算场景比例（0-1） |
| `diversity_score` | 多样性评分（0-1） |

### results.tsv 格式

```
run_id	description	aggregate_score	avg_reward	calorie_error_pct	budget_violation_rate	diversity_score	decision
exp001	baseline	72.50	18.30	12.1	0.20	0.75	keep
exp002	lr=5e-5	68.20	16.50	15.3	0.40	0.70	discard
```

- `decision=keep`：分数 >= 当前基线，保留该实验配置
- `decision=discard`：分数 < 基线，丢弃

### AI Agent 自动进化模式

```bash
conda activate ai_lab

# 单次 AI 实验（agent 修改 dqn_train_config.py 后执行）
python scripts/dqn_autoresearch_run.py --timesteps 50000 > run.log 2>&1
grep "^aggregate_score:" run.log
```

详见 [dqn-autoresearch-program.md](dqn-autoresearch-program.md) 了解完整的 AI agent 自主循环协议。

### 查看进度图

每轮实验后会自动刷新进度图，也可手动生成：

```bash
conda activate ai_lab
python scripts/dqn_autoresearch_plot.py
```

图片保存在 `models/autoresearch/progress.png`，包含 4 个子图：
- **Aggregate Score**：综合评分趋势 + 最佳分数线
- **Avg Reward**：平均奖励趋势
- **Calorie Error & Budget Violations**：热量误差和预算超支率（越低越好）
- **Diversity Score**：菜品多样性 + keep/discard 饼图统计

## 运行测试

```bash
uv run python -m pytest tests/rl/test_autoresearch_*.py -q
```
