# 基于强化学习与多 Agent 协作的智能配餐系统

## 项目简介

本项目是一个智能配餐系统，当前运行时主流程已经切换为“营养师多轮对话 + 隐藏目标量化 + 严格预算约束”的配餐模式。

核心技术：

- 强化学习算法：使用 RL 模型生成一日三餐候选方案
- 对话式编排：FastAPI 后端维护会话状态、预算校验和正式出餐时机
- 结构化提取：DeepSeek（OpenAI 兼容接口）用于从自然语言中抽取资料和偏好
- Web 服务：FastAPI 后端 + Vue 3 / Element Plus 前端
- 用户系统：JWT 身份认证与服务端个人档案

## 对话式配餐

用户进入 `/meal-plan` 后，不再手动设置热量、蛋白质、碳水、脂肪等显式数值，而是通过与“营养师”对话完成配餐：

1. 优先读取账户中已保存的身体资料
2. 对缺失的性别、年龄、身高、体重、活动水平逐项补问
3. 采集预算、忌口、口味偏好和健康目标
4. 在后端映射为隐藏营养目标
5. 使用严格预算模式调用 RL 规划器
6. 若预算不足，则明确提示提高预算，不返回超预算方案

## 环境配置

本项目使用 `uv` 管理 Python 环境和依赖。

### 前置要求

- 安装 [uv](https://docs.astral.sh/uv/) 包管理器
- Node.js 18+
- Windows 10/11 或 Linux/macOS

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd intelligent_meal_planner
```

### 2. 同步 Python 环境

```bash
uv sync
```

### 3. 配置 DeepSeek

复制 `.env.example` 为 `.env`，然后填写你的 DeepSeek 配置：

```env
DEEPSEEK_API_KEY=your_key_here
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
```

### 4. 启动后端

```bash
uv run python main.py api
```

后端地址：`http://127.0.0.1:9000`

### 5. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端地址：`http://localhost:5173`

### Windows 一键启动

如果你在 Windows 上，也可以直接使用项目内置脚本：

```bat
start_project.bat
```

它会自动检查依赖、选择可用后端端口，并分别启动前后端窗口。

## 运行时说明

- `/meal-plan`：对话式配餐入口
- `/profile`：服务端档案编辑页，聊天中补齐的资料会同步回这里
- `/history`：查看已完成会话中的正式配餐结果

旧的单轮 CrewAI 运行入口已经退役，`main.py agent` 只保留兼容提示，不再参与实际配餐链路。

## 项目结构

```text
intelligent_meal_planner/
├── frontend/
├── src/intelligent_meal_planner/
│   ├── api/
│   ├── db/
│   ├── meal_chat/
│   ├── rl/
│   ├── tools/
│   └── agents/        # 已退役，仅保留兼容占位
├── tests/
├── docs/
├── pyproject.toml
└── uv.lock
```

## 开发命令

### 后端测试

```bash
uv run python -m pytest
```

### 前端构建

```bash
cd frontend
npm run build
```

### 代码格式化

```bash
uv run black src tests
uv run ruff check src tests
```

## DQN Autoresearch

自动化 DQN 训练实验循环：

```bash
uv run python scripts/run_dqn_autoresearch_experiment.py --timesteps 50000 --run-id exp001
uv run python scripts/dqn_autoresearch_loop.py --iterations 5 --timesteps 50000
```

详见 [docs/dqn-autoresearch.md](docs/dqn-autoresearch.md)。
