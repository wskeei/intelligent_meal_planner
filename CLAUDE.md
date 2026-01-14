# Intelligent Meal Planner - Claude Code 项目文档

## 项目概述

基于强化学习（Reinforcement Learning）与多 Agent 协作的智能配餐系统。使用 MaskablePPO 算法训练配餐模型，能够根据用户的营养目标、预算限制和口味偏好，智能生成一日三餐的食谱推荐。

## 技术栈

- **强化学习**: Stable-Baselines3 + sb3-contrib (MaskablePPO)
- **环境**: Gymnasium
- **后端**: FastAPI
- **前端**: Streamlit (规划中)
- **多Agent**: CrewAI (规划中)

## 项目结构

```
intelligent_meal_planner/
├── src/intelligent_meal_planner/
│   ├── data/
│   │   └── recipes.json          # 中国菜谱数据库 (150道菜品)
│   └── rl/
│       ├── environment.py        # 强化学习环境 (MealPlanningEnv)
│       ├── train_dqn.py          # 训练脚本 (模块化版本)
│       ├── check_device.py       # 设备检查工具
│       └── test_env.py           # 环境测试
├── scripts/
│   ├── train_optimized.py        # 高性能训练脚本 (推荐使用)
│   ├── train_gpu_windows.py      # Windows GPU训练脚本
│   ├── test_model_detailed.py    # 模型详细测试
│   ├── test_different_targets.py # 不同目标测试
│   ├── analyze_training.py       # 训练结果分析
│   ├── visualize_results.py      # 结果可视化
│   └── verify_new_recipes.py     # 菜谱验证脚本
├── models/                       # 训练产出 (gitignore)
│   ├── ppo_meal_fast_final.zip   # 最终模型
│   ├── vec_normalize_fast.pkl    # 归一化统计
│   ├── checkpoints/              # 训练检查点
│   └── logs/                     # 训练日志
└── frontend/                     # 前端代码 (规划中)
```

## 菜谱数据库

### 基本信息
- **总菜品数量**: 150 道中国菜
- **价格范围**: 3-48 元
- **平均价格**: 17.3 元

### 餐次覆盖
| 餐次 | 菜品数量 |
|------|----------|
| 早餐 | 20 |
| 午餐 | 137 |
| 晚餐 | 132 |

### 类别分布
- Meat: 56 | Vegan: 25 | Poultry: 17
- Breakfast: 14 | Seafood: 13 | Staple: 12
- Cold: 5 | Tofu: 4 | Soup: 4

### 营养性价比
| 指标 | 最低 | 最高 | 平均 |
|------|------|------|------|
| 热量/元 | 10.0 kcal | 70.0 kcal | 30.3 kcal |
| 蛋白质/元 | 0.33g | 4.00g | 1.32g |

## 强化学习环境

### 状态空间 (13维)
```
[0] 当前进度 (step/max_steps)
[1-4] 累计营养比例 (卡路里/蛋白质/碳水/脂肪)
[5] 累计花费比例
[6-7] 剩余资源比例 (卡路里/预算)
[8] 剩余步数比例
[9-11] 当前餐次 one-hot (breakfast/lunch/dinner)
[12] 多样性指标
```

### 动作空间
- 离散动作: 从150道菜品中选择
- 动作掩码规则:
  1. 只能选择符合当前餐次的菜品
  2. 只能选择预算范围内的菜品
  3. **不能选择已经选过的菜品** (强制多样性，防止局部最优)

### 奖励函数
```
R_total = w1*R_nutrition + w2*R_budget + w3*R_variety + P_dislike

- R_nutrition: 营养达标奖励 (卡路里±10%, 蛋白质±20%, 碳水±25%, 脂肪±30%)
- R_budget: 预算控制奖励
- R_variety: 多样性奖励 (鼓励选择不同类别)
- P_dislike: 忌口惩罚
```

### 课程学习 (Curriculum Learning)
| 阶段 | 训练步数 | 预算 | 目标 |
|------|----------|------|------|
| Stage 1 | 0-100k | 120元 (固定) | 2000 kcal (固定) |
| Stage 2 | 100k-300k | 80-150元 | 1800-2200 kcal |
| Stage 3 | 300k+ | 50-250元 | 1200-3000 kcal |

## 训练指南

### 环境准备
```bash
conda activate ai_lab
```

### 开始训练
```bash
# 默认50万步训练
python scripts/train_optimized.py

# 指定训练步数
python scripts/train_optimized.py --timesteps 300000

# 测试已训练的模型
python scripts/train_optimized.py --mode test
```

### 训练配置 (针对 RTX 4060 + 24核CPU)
- 并行环境: 24个 (SubprocVecEnv)
- Batch Size: 512
- Buffer Size: 6144 (24 * 256)
- 学习率: 3e-4 (线性衰减)
- 熵系数: 0.1 → 0.01

### 监控训练
```bash
tensorboard --logdir models/logs/tensorboard
```

## 测试模型

### 详细测试
```bash
python scripts/test_model_detailed.py
```

### 不同目标测试
```bash
python scripts/test_different_targets.py
```

### 验证菜谱配置
```bash
python scripts/verify_new_recipes.py
```

## 默认参数

| 参数 | 值 | 说明 |
|------|-----|------|
| target_calories | 2000 kcal | 目标卡路里 |
| target_protein | 100g | 目标蛋白质 |
| target_carbs | 250g | 目标碳水化合物 |
| target_fat | 65g | 目标脂肪 |
| budget_limit | 100 元 | 预算限制 |
| meals_per_day | 3 | 每日餐数 |
| items_per_meal | 2 | 每餐菜品数 |

## 开发备注

### 2024年更新记录
1. 将菜谱从西式菜品更换为150道中国菜
2. 调整价格从不合理的西方价格到符合中国市场的价格
3. 优化预算参数 (从150元调整为100元)
4. 更新课程学习的预算范围
5. **新增：动作掩码禁止选择已选过的菜品** (解决局部最优问题)

### 待完成功能
- [ ] 前端界面 (Streamlit)
- [ ] CrewAI 多Agent集成
- [ ] 用户忌口功能完善
- [ ] API服务部署

## 常见问题

### Q: 模型训练不收敛？
检查预算设置是否合理，确保在给定预算下存在可行解。

### Q: 动作掩码导致无有效动作？
环境已内置防死锁机制，会自动选择最便宜的菜品。

### Q: 如何添加新菜品？
编辑 `src/intelligent_meal_planner/data/recipes.json`，按照现有格式添加。

## 相关文件

- `intelligent_meal_planner_proposal.md` - 项目设计方案
- `.gitignore` - Git忽略配置 (models/ 目录已忽略)
