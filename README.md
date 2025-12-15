# 基于强化学习与多Agent协作的智能配餐系统

## 项目简介

本项目是一个智能配餐系统，采用以下核心技术：
- **强化学习算法**：使用 DQN（深度Q网络）进行配餐优化
- **多Agent协作**：基于 CrewAI 框架实现智能营养师团队
- **Web服务**：FastAPI 后端 + Streamlit 前端

## 环境配置

本项目使用 `uv` 进行 Python 环境和依赖管理，确保跨平台一致性。

### 前置要求

- 安装 [uv](https://docs.astral.sh/uv/) 包管理器
- Windows 10/11 或 Linux/macOS

### 快速开始

#### 1. 克隆项目

```bash
git clone <your-repo-url>
cd intelligent_meal_planner
```

#### 2. 使用 uv 同步环境

```bash
# uv 会自动：
# 1. 安装项目指定的 Python 版本（3.10.16）
# 2. 创建独立的虚拟环境 .venv
# 3. 安装所有依赖包
uv sync
```

#### 3. 激活虚拟环境

**Windows:**
```cmd
.venv\Scripts\activate
```

**Linux/macOS:**
```bash
source .venv/bin/activate
```

#### 4. 运行项目

```bash
# 训练 DQN 模型
uv run python -m intelligent_meal_planner.train

# 启动 FastAPI 后端
uv run uvicorn intelligent_meal_planner.api:app --reload

# 启动 Streamlit 前端
uv run streamlit run intelligent_meal_planner/app.py
```

## 项目结构

```
intelligent_meal_planner/
├── src/
│   └── intelligent_meal_planner/
│       ├── __init__.py
│       ├── data/
│       │   └── recipes.json          # 菜品数据库
│       ├── rl/
│       │   ├── environment.py        # 强化学习环境
│       │   └── dqn_model.py          # DQN 模型训练
│       ├── agents/
│       │   ├── user_profiler.py      # 用户需求分析师
│       │   └── rl_chef.py            # 强化学习配餐师
│       ├── tools/
│       │   ├── rl_model_tool.py      # 模型调用工具
│       │   └── recipe_db_tool.py     # 数据库查询工具
│       ├── api.py                    # FastAPI 后端
│       └── app.py                    # Streamlit 前端
├── models/                           # 训练好的模型文件
├── tests/                            # 测试文件
├── pyproject.toml                    # 项目配置
├── uv.lock                           # 依赖锁定文件
└── README.md
```

## 依赖管理

### 添加新依赖

```bash
uv add <package-name>
```

### 移除依赖

```bash
uv remove <package-name>
```

### 更新依赖

```bash
uv sync --upgrade
```

## 开发指南

### 代码格式化

```bash
uv run black src/
uv run ruff check src/
```

### 运行测试

```bash
uv run pytest
```

## 技术栈

- **Python**: 3.10.16 (由 uv 管理)
- **强化学习**: Stable-Baselines3, Gymnasium
- **多Agent框架**: CrewAI
- **Web框架**: FastAPI, Streamlit
- **深度学习**: PyTorch

## 注意事项

1. **虚拟环境隔离**：本项目使用 uv 创建的独立虚拟环境，不依赖 conda
2. **跨平台兼容**：`uv.lock` 文件确保在不同机器上环境一致
3. **中文编码**：Windows 系统下确保使用 UTF-8 编码，避免乱码

## 学习资源

- [uv 官方文档](https://docs.astral.sh/uv/)
- [Stable-Baselines3 文档](https://stable-baselines3.readthedocs.io/)
- [CrewAI 文档](https://docs.crewai.com/)
- [FastAPI 教程](https://fastapi.tiangolo.com/)