<template>
  <el-container style="height: 100vh">
    <el-aside width="220px" style="background: #1d1e2c; overflow: hidden">
      <AppSidebar />
    </el-aside>
    <el-container>
      <el-header style="height: 56px; padding: 0 20px; border-bottom: 1px solid #e4e7ed; display: flex; align-items: center; background: #fff">
        <AppHeader />
      </el-header>
      <el-main style="background: #f5f7fa; padding: 20px">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import AppSidebar from './components/layout/AppSidebar.vue'
import AppHeader from './components/layout/AppHeader.vue'
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Microsoft YaHei', sans-serif; }
</style>
