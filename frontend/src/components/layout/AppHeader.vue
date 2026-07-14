<template>
  <div style="display: flex; justify-content: space-between; align-items: center; width: 100%">
    <el-breadcrumb separator="/">
      <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
      <el-breadcrumb-item v-if="title">{{ title }}</el-breadcrumb-item>
    </el-breadcrumb>
    <div style="display: flex; align-items: center; gap: 12px">
      <el-tag type="success" size="small" effect="dark">v1.0</el-tag>
      <span style="font-size: 13px; color: #606266">管理员</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const title = computed(() => route.meta?.title || '')
</script>
