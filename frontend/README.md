# 智能配餐系统前端

基于 Vue 3 + TypeScript + Element Plus 的前端应用。

## 当前产品模型

### 智能配餐 `/meal-plan`

- 页面已切换为对话式配餐流程
- 不再暴露热量、蛋白质、碳水、脂肪滑块
- 页面会先创建会话，再按轮次收集预算、偏好和缺失资料
- 只有在信息充分时才返回正式配餐结果
- 若预算不足，只提示提高预算，不返回超预算方案

### 用户资料 `/profile`

- 资料以服务端存储为准
- 营养师对话中收集到的身体资料会自动同步回档案页

## 开发命令

```bash
cd frontend
npm install
npm run dev
npm run build
```

默认通过 `VITE_API_BASE_URL` 访问后端，未配置时使用：

```env
VITE_API_BASE_URL=/api
```

本地开发默认通过 Vite 代理把 `/api` 转发到：

```env
VITE_API_PROXY_TARGET=http://127.0.0.1:9000
```

如果是从 Windows 直接复制到 Linux，先重新安装前端依赖，避免 `.bin` 可执行权限丢失：

```bash
rm -rf node_modules
npm install
```

## 页面说明

- `/`：当前目标、资料完整度、进入对话配餐的主入口
- `/meal-plan`：营养师聊天界面与正式配餐结果展示
- `/profile`：编辑服务端身体资料与默认健康目标
- `/history`：查看已完成会话的配餐历史
- `/recipes`：浏览菜谱
- `/shopping-list`：购物清单
