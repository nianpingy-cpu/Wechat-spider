<template>
  <div style="display: flex; flex-direction: column; height: 100%">
    <div style="padding: 20px 20px 10px; text-align: center">
      <h2 style="color: #fff; font-size: 18px; margin: 0">🕵️ WeChat Spider</h2>
      <p style="color: #8b8fa3; font-size: 12px; margin-top: 4px">微信公众号采集管理</p>
    </div>
    <el-menu
      :default-active="activeMenu"
      router
      background-color="#1d1e2c"
      text-color="#8b8fa3"
      active-text-color="#409EFF"
      style="border-right: none; flex: 1"
    >
      <el-menu-item index="/">
        <el-icon><DataAnalysis /></el-icon>
        <span>仪表盘</span>
      </el-menu-item>
      <el-menu-item index="/config">
        <el-icon><Setting /></el-icon>
        <span>配置管理</span>
      </el-menu-item>
      <el-menu-item index="/tasks">
        <el-icon><List /></el-icon>
        <span>任务管理</span>
      </el-menu-item>
      <el-menu-item index="/articles">
        <el-icon><Document /></el-icon>
        <span>文章浏览</span>
      </el-menu-item>
      <el-menu-item index="/stats">
        <el-icon><TrendCharts /></el-icon>
        <span>统计看板</span>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>
