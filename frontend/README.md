# 智能配餐系统前端

基于 Vue 3 + TypeScript + Element Plus 构建的现代化前端应用。

## 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **TypeScript** - 类型安全的 JavaScript 超集
- **Vite** - 下一代前端构建工具
- **Vue Router** - 官方路由管理器
- **Element Plus** - 基于 Vue 3 的组件库
- **Axios** - HTTP 客户端
- **ECharts** - 数据可视化图表库

## 项目结构

```
frontend/
├── src/
│   ├── api/           # API 接口封装
│   │   └── index.ts   # Axios 实例和接口定义
│   ├── router/        # 路由配置
│   │   └── index.ts   # Vue Router 配置
│   ├── views/         # 页面组件
│   │   ├── HomeView.vue      # 首页
│   │   ├── MealPlanView.vue  # 配餐页面
│   │   ├── RecipesView.vue   # 菜品库页面
│   │   └── HistoryView.vue   # 历史记录页面
│   ├── App.vue        # 根组件
│   └── main.ts        # 入口文件
├── index.html         # HTML 模板
├── package.json       # 依赖配置
├── tsconfig.json      # TypeScript 配置
└── vite.config.ts     # Vite 配置
```

## 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

前端将在 http://localhost:5173 启动。

### 3. 构建生产版本

```bash
npm run build
```

构建产物将输出到 `dist/` 目录。

## 页面说明

### 首页 (/)
- 系统介绍和功能概览
- 快速入口按钮

### 智能配餐 (/meal-plan)
- 设置健康目标（减脂/增肌/均衡）
- 设置营养目标和预算
- AI 生成个性化配餐方案
- 营养达成分析图表

### 菜品库 (/recipes)
- 浏览所有菜品
- 按餐次、分类、价格筛选
- 查看菜品详细信息

### 历史记录 (/history)
- 查看历史配餐记录
- 重复使用历史配置
- 管理历史数据

## 与后端联调

确保后端 API 服务运行在 http://localhost:8000，前端已配置代理转发 `/api` 请求到后端。

启动后端：
```bash
cd ..  # 回到项目根目录
uv run uvicorn src.intelligent_meal_planner.api.main:app --reload
```

## 开发说明

- TypeScript 报错"找不到模块"是因为未安装依赖，运行 `npm install` 后会自动解决
- 开发时前后端需要同时运行
- 修改代码后 Vite 会自动热更新