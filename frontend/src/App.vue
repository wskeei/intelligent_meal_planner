<template>
  <el-config-provider :locale="zhCn">
    <el-container class="app-container">
      <el-header class="app-header">
        <div class="logo">
          <el-icon :size="28"><Food /></el-icon>
          <span>智能配餐系统</span>
        </div>
        <el-menu
          mode="horizontal"
          :router="true"
          :default-active="$route.path"
          class="nav-menu"
        >
          <el-menu-item index="/">首页</el-menu-item>
          <el-menu-item index="/meal-plan">智能配餐</el-menu-item>
          <el-menu-item index="/recipes">菜品库</el-menu-item>
          <el-menu-item index="/history">历史记录</el-menu-item>
        </el-menu>
      </el-header>
      
      <el-main class="app-main">
        <router-view />
      </el-main>
      
      <el-footer class="app-footer">
        <span>© 2024 智能配餐系统 - 基于强化学习与多Agent协作</span>
      </el-footer>
    </el-container>
  </el-config-provider>
</template>

<script setup lang="ts">
import { Food } from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
}

.app-container {
  height: 100%;
}

.app-header {
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  color: white;
  font-size: 20px;
  font-weight: bold;
  margin-right: 40px;
}

.nav-menu {
  background: transparent;
  border: none;
  flex: 1;
}

.nav-menu .el-menu-item {
  color: rgba(255, 255, 255, 0.85);
  border-bottom: none;
}

.nav-menu .el-menu-item:hover,
.nav-menu .el-menu-item.is-active {
  color: white;
  background: rgba(255, 255, 255, 0.1);
}

.app-main {
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

.app-footer {
  text-align: center;
  color: #909399;
  font-size: 14px;
  background: #fff;
  border-top: 1px solid #ebeef5;
}
</style>