# DQN Autoresearch Workflow

自动化 DQN 训练实验循环：训练 -> 评估 -> 记录 -> 决策（保留/丢弃）。

## 模块结构

```
src/intelligent_meal_planner/rl/autoresearch/
├── __init__.py        # 模块导出
├── benchmark.py       # 基准测试场景与评分函数 (8 个场景)
├── evaluator.py       # 确定性评估器 (双阶段: closed + open)
├── recipe_validator.py # 自定义菜品验证器 (防作弊)
├── runner.py          # 单次实验运行器（训练 + 评估 + 保存）
└── loop.py            # 循环日志工具（TSV 记录 + 保留/丢弃逻辑）

scripts/
├── dqn_train_config.py                    # AI agent 可修改的训练配置
├── dqn_autoresearch_run.py                # 单次实验 CLI (含菜品验证+双阶段评估)
├── dqn_autoresearch_loop.py               # 多次循环 CLI
├── dqn_autoresearch_plot.py               # 进度可视化 (2x3 布局)
└── run_dqn_autoresearch_experiment.py     # 单次实验 CLI (旧版)
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

评估使用 8 个固定场景覆盖不同用户需求：

| 场景 | 目标热量 | 预算 | 蛋白质 | 特点 |
|------|---------|------|--------|------|
| standard | 2000 kcal | 100 元 | 100g | 标准饮食 |
| low_budget | 1800 kcal | 60 元 | 80g | 低预算 |
| high_protein | 2200 kcal | 120 元 | 150g | 高蛋白健身 |
| low_calorie | 1500 kcal | 80 元 | 75g | 低卡减脂 |
| generous_budget | 2500 kcal | 200 元 | 120g | 宽松预算 |
| **tight_budget** | 2000 kcal | **45 元** | 90g | 极限预算 |
| **keto_diet** | 1800 kcal | 100 元 | 135g | 低碳高脂 (碳水50g/脂肪120g) |
| **bulk_diet** | 3000 kcal | 150 元 | 180g | 增肌饮食 |

## 评分函数

综合得分由四个指标加权计算（双阶段评估：`aggregate = 0.5 * closed + 0.5 * open`）：

| 指标 | 权重 | 说明 |
|------|------|------|
| 热量准确度 | 30% | 越接近目标越高（3x 惩罚系数） |
| 预算合规率 | 25% | 未超支场景占比 |
| 菜品多样性 | 15% | 类别多样性评分（≥3类别才有分） |
| 平均奖励 | 30% | 环境回报均值 |

**双阶段评估防作弊：**
- **Closed (50%)**：仅用原始 150 道菜，price/budget_scale=1.0 — 测纯算法能力
- **Open (50%)**：全部菜品 + 自定义菜品 + scale — 鼓励有价值的调优

## 结果解读

### summary.json 字段

| 字段 | 说明 |
|------|------|
| `aggregate_score` | 综合评分 = 0.5*closed + 0.5*open |
| `closed_score` | 封闭赛评分（原始菜品，不可操控） |
| `open_score` | 开放赛评分（含自定义菜品+scale） |
| `avg_reward` | 基准场景平均奖励 |
| `calorie_error_pct` | 平均热量误差百分比 |
| `budget_violation_rate` | 超预算场景比例（0-1） |
| `diversity_score` | 多样性评分（0-1） |
| `price_scale` | 菜品价格缩放因子 |
| `budget_scale` | 预算限制缩放因子 |
| `n_custom_recipes` | 自定义菜品数量 |

### results.tsv 格式

```
run_id	description	aggregate_score	closed_score	open_score	avg_reward	calorie_error_pct	budget_violation_rate	diversity_score	price_scale	budget_scale	n_custom_recipes	decision
exp001	baseline	72.50	68.20	76.80	18.30	12.1	0.20	0.75	1.00	1.00	0	keep
exp002	add 3 recipes	74.10	68.20	80.00	19.10	10.5	0.10	0.80	1.00	1.10	3	keep
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

图片保存在 `models/autoresearch/progress.png`，包含 2x3 共 6 个子图：
- **Aggregate Score**：综合评分趋势 + closed/open 双线 + 最佳分数线
- **Avg Reward**：平均奖励趋势
- **Custom Recipes**：每轮自定义菜品数量柱状图
- **Calorie Error & Budget Violations**：热量误差和预算超支率（越低越好）
- **Diversity Score**：菜品多样性 + 最低门槛线
- **Keep/Discard/Crash**：决策饼图统计

## 运行测试

```bash
uv run python -m pytest tests/rl/test_autoresearch_*.py tests/rl/test_recipe_validator.py -q
```

## 自定义菜品与价格/预算调控

AI agent 在 `dqn_train_config.py` 中可以：

### 价格/预算缩放

```python
PRICE_SCALE = 0.8   # 所有菜品打 8 折
BUDGET_SCALE = 1.2  # 所有预算放宽 20%
```

### 添加自定义菜品

```python
CUSTOM_RECIPES = [
    {
        "name": "鸡胸肉沙拉",
        "calories": 350, "protein": 35, "carbs": 15, "fat": 12,
        "price": 18, "meal_type": ["lunch", "dinner"],
        "category": "Poultry", "tags": ["healthy"],
    },
]
```

### 菜品验证规则

每道自定义菜品必须通过 `recipe_validator.py` 验证：

| 规则 | 范围 | 说明 |
|------|------|------|
| 价格 | 3-50 元 | 中国正常餐饮价格 |
| 热量 | 50-800 kcal | 每道菜合理范围 |
| kcal/元 | 8-80 | 防止"完美"性价比菜品 |
| protein/元 | 0.15-5.0 | 防止超高蛋白性价比 |
| category | 9 种之一 | Meat/Vegan/Poultry/Breakfast/Seafood/Staple/Cold/Tofu/Soup |
| 最大数量 | 150 道 | action_dim 固定 300 = 150 原始 + 150 自定义 |
