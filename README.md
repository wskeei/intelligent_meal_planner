# 基于 DQN 与 CrewAI 多智能体协作的智能配餐系统

## 项目简介

本项目是一个智能配餐系统，当前运行时主流程已经切换为“对话式 intake + CrewAI 多智能体协作 + DQN 配餐”的模式。

核心技术：

- 强化学习算法：使用 Dueling Double DQN 模型生成一日三餐候选方案
- 对话式编排：FastAPI 后端维护会话状态、预算校验和正式出餐时机
- 结构化提取：DeepSeek（OpenAI 兼容接口）用于从自然语言中抽取资料和偏好
- Web 服务：FastAPI 后端 + Vue 3 / Element Plus 前端
- 用户系统：JWT 身份认证与服务端个人档案

## 核心流程

1. 与用户多轮对话，收集目标、预算、忌口和口味偏好
2. intake 信息齐全后，启动 CrewAI 多智能体团队
3. 团队完成需求审查、营养规划、预算协调、DQN 配餐、结果解读
4. 前端同时展示正式方案和可见的协作过程

## 对话理解升级

当前 meal chat 后端每轮会执行：

1. AI 提取用户本轮自由表达中的目标、预算、忌口和口味线索
2. 将提取结果归一化成标准字段与枚举
3. 计算理解置信度、关键缺失项和潜在语义冲突
4. 如果信息不足，则以营养师语气进行追问
5. 信息充分后才进入预算协商与强化学习配餐

理解状态会保存在会话 memory 中，包括：

- 规范化后的偏好与补充资料
- 当前轮的 `analysis` 和 `follow_up_plan`
- `open_questions`、`clarification_history` 与 richer trace 元数据

## 环境配置

本项目使用 `uv` 管理 Python 环境和依赖。

### 前置要求

- 安装 [uv](https://docs.astral.sh/uv/)
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
MEAL_CHAT_TRACE_DIR=logs/meal_chat
```

可选运行参数：

```env
MEAL_PLANNER_API_HOST=0.0.0.0
MEAL_PLANNER_API_PORT=9000
MEAL_PLANNER_API_RELOAD=1
VITE_API_BASE_URL=
VITE_API_PROXY_TARGET=
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

### Linux 一键启动

Linux 下推荐使用项目内置 shell 脚本：

```bash
chmod +x start_project.sh scripts/start_backend.sh scripts/start_frontend.sh
./start_project.sh
```

脚本会自动：

- 检查 `uv` 和 `npm`
- 在缺失时执行 `uv sync`
- 在缺失时执行 `frontend/npm install`
- 自动探测可用后端端口
- 后台启动前后端，并把日志写到 `backend.log` / `frontend.log`

首次从 Windows 目录直接迁移到 Linux 时，建议先重新安装前端依赖，避免 `node_modules/.bin/*` 缺少可执行位：

```bash
rm -rf frontend/node_modules
cd frontend
npm install
```

### Windows 一键启动

如果你在 Windows 上，也可以直接使用项目内置脚本：

```bat
start_project.bat
```

它会自动检查依赖、选择可用后端端口，并分别启动前后端窗口。

## Meal Chat Trace Logs

后端对话式配餐会把每个会话的调试轨迹写入：

`logs/meal_chat/YYYY-MM-DD/<session_id>.jsonl`

每行都是一条 JSON 记录，包含：

- 会话开始事件
- 成功处理的轮次事件
- 失败轮次事件与异常文本
- 提取器调试元数据，例如 `expected_slot`、模型原始响应以及是否命中 fallback

## 运行时说明

- `/meal-plan`：对话式配餐入口
- `/profile`：服务端档案编辑页，聊天中补齐的资料会同步回这里
- `/history`：查看已完成会话中的正式配餐结果

旧的单轮 pseudo-agent 运行入口已经移除，`main.py agent` 只保留兼容提示，不再参与实际配餐链路。
训练入口 `uv run python main.py train` 只会调用 DQN 训练脚本。

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
│   └── agents/
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
