# DQN Autoresearch — AI Agent 自主实验指令

这是一个自主研究实验框架。你（AI agent）将独立迭代 DQN 配餐模型的训练配置，运行实验，评估结果，并决定保留或丢弃改动。

## 执行环境

**必须使用 conda ai_lab 环境 + GPU 训练。**

- Python: `D:/Download/tools/conda/envs/ai_lab/python.exe`
- GPU: NVIDIA RTX 4060 (CUDA)
- 所有训练和实验命令前需要 `conda activate ai_lab`，或直接使用完整路径调用 python
- 项目 src 已通过 sys.path 自动注入，无需 pip install

## Setup

与用户一起完成初始设置：

1. **确定 run tag**：基于日期提议标签（例如 `mar14`），分支 `autoresearch-dqn/<tag>` 不能已存在。
2. **创建分支**：`git checkout -b autoresearch-dqn/<tag>`
3. **阅读相关文件**：
   - `scripts/dqn_train_config.py` — **你唯一可以修改的文件**。包含所有超参数和训练循环。
   - `src/intelligent_meal_planner/rl/environment.py` — 环境定义（只读）。
   - `src/intelligent_meal_planner/rl/autoresearch/benchmark.py` — 基准场景和评分（只读）。
   - `src/intelligent_meal_planner/rl/autoresearch/evaluator.py` — 评估逻辑（只读）。
   - `src/intelligent_meal_planner/rl/dqn/agent.py` — DQN agent 实现（只读）。
   - `src/intelligent_meal_planner/rl/dqn/networks.py` — 网络架构（只读）。
4. **初始化 results.tsv**：在项目根目录创建 `results.tsv`，只含表头。基线在第一次运行后记录。
5. **确认开始**：确认设置无误后启动循环。

## 规则

**你可以做的：**
- 修改 `scripts/dqn_train_config.py` — 这是你唯一编辑的文件。所有改动都允许：超参数、网络结构、epsilon 策略、PER 参数、训练循环、batch size 等。

**你不能做的：**
- 修改 `environment.py` — 环境机制是固定的。
- 修改 `benchmark.py` 或 `evaluator.py` — 评估逻辑是固定的。
- 修改 `dqn/agent.py` 或 `dqn/networks.py` — agent 核心代码是固定的。
- 修改 `dqn_autoresearch_run.py` — 执行入口是固定的。
- 安装新依赖或修改 `pyproject.toml`。

**目标：获得最高的 `aggregate_score`。** 评估使用 5 个固定的基准场景（standard、low_budget、high_protein、low_calorie、generous_budget），综合评分考虑热量准确度(30%)、预算合规(25%)、菜品多样性(15%)和平均奖励(30%)。

**简洁原则：** 相同效果下，更简单的配置更好。小幅提升但增加大量复杂性不值得保留。删除代码获得相同或更好结果是好事。

## 输出格式

实验完成后会打印标准化输出：

```
---
aggregate_score:      72.500000
avg_reward:           18.300000
calorie_error_pct:    12.100000
budget_violation_rate: 0.200000
diversity_score:      0.750000
timesteps:            50000
```

提取关键指标：
```bash
grep "^aggregate_score:" run.log
```

## 日志格式 (results.tsv)

制表符分隔（NOT 逗号），6 列：

```
commit	aggregate_score	avg_reward	status	description
```

1. git commit hash（短格式，7 字符）
2. aggregate_score（例如 72.500000）— crash 时用 0.000000
3. avg_reward（例如 18.300000）— crash 时用 0.000000
4. status：`keep`、`discard` 或 `crash`
5. 简短描述本次实验做了什么

示例：
```
commit	aggregate_score	avg_reward	status	description
a1b2c3d	65.230000	15.400000	keep	baseline
b2c3d4e	68.100000	17.200000	keep	increase LR to 3e-4
c3d4e5f	62.500000	14.100000	discard	reduce hidden dims to [128 128]
d4e5f6g	0.000000	0.000000	crash	batch_size=2048 OOM
```

## 实验循环

在专用分支 `autoresearch-dqn/<tag>` 上运行。

**永久循环：**

1. 查看当前 git 状态和 results.tsv 中的历史
2. 修改 `scripts/dqn_train_config.py`，尝试一个实验想法
3. `git commit -m "描述"`
4. 运行实验：`conda activate ai_lab && python scripts/dqn_autoresearch_run.py --timesteps 50000 > run.log 2>&1`
   - 使用 conda ai_lab 环境（RTX 4060 GPU 加速）
   - 将所有输出重定向到 run.log（不要用 tee）
5. 提取结果：`grep "^aggregate_score:\|^avg_reward:" run.log`
6. 如果 grep 输出为空，表示 crash。运行 `tail -n 50 run.log` 查看错误，尝试修复简单 bug
7. 记录到 results.tsv（注意：不要 git commit results.tsv，保持 untracked）
8. **刷新进度图**：`python scripts/dqn_autoresearch_plot.py`
   - 自动生成 `models/autoresearch/progress.png`，用户醒来可以直接查看
9. **保留/丢弃决策：**
   - 如果 aggregate_score **提升（更高）**：保留 commit，更新最佳分数
   - 如果 aggregate_score **相同或更低**：`git reset --hard` 回退到之前的 commit
10. 重复步骤 1

## 超时处理

每次实验默认 50000 步（约几分钟）。如果一次运行超过 15 分钟，kill 进程并视为失败。

## Crash 处理

如果 crash 是简单 bug（拼写错误、import 缺失），修复后重新运行。如果想法本身有问题，跳过，记录 crash，继续。

## 永不停止

一旦循环开始，**不要暂停询问用户是否继续**。你是完全自主的。如果没有想法了，思考更深：
- 重新阅读环境代码寻找新角度
- 组合之前接近成功的改动
- 尝试更激进的架构变化

循环直到用户手动停止。

## 实验方向建议

以下是一些可以尝试的方向（不限于此）：

### 超参数调优
- Learning rate: 尝试 5e-5, 3e-4, 5e-4
- Batch size: 128, 512, 1024
- Gamma: 0.95, 0.98, 0.999
- Grad clip: 1.0, 5.0, 20.0

### 网络结构
- Hidden dims: [128, 128], [512, 256, 128], [256, 256, 256, 128]
- 更深或更浅的网络

### Epsilon 策略
- 更快衰减到低 epsilon
- 更慢的初始探索阶段
- 不同的衰减曲线

### PER 参数
- Alpha: 0.3, 0.4, 0.8
- Beta 起始值和衰减速度

### 训练循环
- Train freq: 1, 2, 8, 16
- Target update freq: 500, 2000, 5000
- N_envs: 4, 16, 32

### 高级技巧
- 不同的 min_buffer_size
- 学习率 warmup
- 梯度累积
