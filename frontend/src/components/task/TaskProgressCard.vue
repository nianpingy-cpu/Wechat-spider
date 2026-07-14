<template>
  <div class="progress-card">
    <div class="progress-header">
      <span class="task-title">任务 #{{ task.id }}</span>
      <el-tag :type="statusTagType" size="small">{{ statusText }}</el-tag>
    </div>
    <div class="progress-info">
      <span>{{ task.type === 'fetch_urls' ? '抓取链接' : '爬取文章' }}</span>
      <span v-if="task.type === 'fetch_urls'">
        第 {{ task.start_page }} - {{ task.end_page }} 页
      </span>
    </div>
    <el-progress
      v-if="task.total_count > 0"
      :percentage="Math.round((task.success_count / task.total_count) * 100)"
      :status="task.status === 'completed' ? 'success' : task.status === 'failed' ? 'exception' : ''"
      style="margin-top: 8px"
    />
    <div class="progress-stats" v-if="task.total_count > 0">
      <span>总数: {{ task.total_count }}</span>
      <span style="color: #67c23a">成功: {{ task.success_count }}</span>
      <span style="color: #f56c6c">失败: {{ task.fail_count }}</span>
    </div>
    <div class="progress-actions" v-if="task.status === 'running'">
      <el-button size="small" type="warning" @click="$emit('pause', task.id)">暂停</el-button>
    </div>
    <div class="progress-actions" v-if="task.status === 'paused'">
      <el-button size="small" type="primary" @click="$emit('resume', task.id)">继续</el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  task: { type: Object, required: true },
})

defineEmits(['pause', 'resume'])

const statusMap = {
  pending: '等待中',
  running: '运行中',
  paused: '已暂停',
  completed: '已完成',
  failed: '失败',
}

const statusTagMap = {
  pending: 'info',
  running: 'primary',
  paused: 'warning',
  completed: 'success',
  failed: 'danger',
}

const statusText = computed(() => statusMap[props.task.status] || props.task.status)
const statusTagType = computed(() => statusTagMap[props.task.status] || 'info')
</script>

<style scoped>
.progress-card {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}
.progress-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.task-title { font-weight: 600; font-size: 15px; }
.progress-info { display: flex; gap: 16px; color: #909399; font-size: 13px; }
.progress-stats { display: flex; gap: 16px; margin-top: 8px; font-size: 13px; }
.progress-actions { margin-top: 10px; display: flex; gap: 8px; }
</style>
