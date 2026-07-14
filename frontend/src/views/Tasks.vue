<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px">
      <h2>📋 任务管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon> 创建任务
      </el-button>
    </div>

    <!-- 任务列表 -->
    <el-card shadow="never" style="margin-bottom: 16px">
      <el-table :data="tasks" stripe v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="taskTypeTag(row.type)">{{ taskTypeLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="input_file" label="文件" min-width="140" show-overflow-tooltip />
        <el-table-column label="进度" width="200">
          <template #default="{ row }">
            <div v-if="row.total_count > 0">
              <el-progress
                :percentage="Math.round((row.success_count / row.total_count) * 100)"
                :stroke-width="8"
                :status="row.status === 'completed' ? 'success' : row.status === 'failed' ? 'exception' : ''"
              />
              <div style="font-size: 12px; color: #909399; margin-top: 4px">
                {{ row.success_count }}/{{ row.total_count }}
                <span v-if="row.fail_count > 0" style="color: #f56c6c"> (失败: {{ row.fail_count }})</span>
              </div>
            </div>
            <span v-else style="color: #c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">
            {{ row.created_at ? new Date(row.created_at).toLocaleString() : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'pending' || row.status === 'paused'"
              type="primary" size="small" @click="startTask(row.id)"
            >启动</el-button>
            <el-button
              v-if="row.status === 'running'"
              type="warning" size="small" @click="pauseTask(row.id)"
            >暂停</el-button>
            <el-button
              v-if="row.status === 'completed' || row.status === 'failed'"
              size="small" @click="viewLogs(row)"
            >查看日志</el-button>
            <el-button size="small" @click="viewLogs(row)">日志</el-button>
            <el-popconfirm
              v-if="row.status !== 'running'"
              title="确定删除此任务？"
              @confirm="deleteTask(row.id)"
            >
              <template #reference>
                <el-button type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <div style="display: flex; justify-content: center; margin-top: 16px">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @change="fetchTasks"
        />
      </div>
    </el-card>

    <!-- 日志面板 -->
    <el-card v-if="logTaskId" shadow="never">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>📜 任务 #{{ logTaskId }} 日志</span>
          <el-button size="small" @click="logTaskId = 0">关闭</el-button>
        </div>
      </template>
      <LogTerminal :task-id="logTaskId" :initial-logs="cachedLogs" />
    </el-card>

    <!-- 创建任务对话框 -->
    <TaskCreateDialog
      v-model="showCreateDialog"
      :url-files="urlFileList"
      @confirm="onCreateTask"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listTasks, createTask, startTask as apiStart, pauseTask as apiPause, deleteTask as apiDelete, getTaskLogs } from '../api/task'
import LogTerminal from '../components/common/LogTerminal.vue'
import TaskCreateDialog from '../components/task/TaskCreateDialog.vue'
import { ElMessage } from 'element-plus'

const tasks = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const showCreateDialog = ref(false)
const logTaskId = ref(0)
const cachedLogs = ref([])

// 模拟 URL 文件列表（实际可以从后端获取）
const urlFileList = ['url_test.txt', 'url_wrong.txt', 'remaining_urls.txt',
  'url_(1-49).txt', 'url_(50-99).txt', 'url_(100-150).txt', 'url_(151-203).txt', 'url_(204-255).txt']

function statusType(s) {
  const map = { pending: 'info', running: 'primary', paused: 'warning', completed: 'success', failed: 'danger' }
  return map[s] || 'info'
}

function statusLabel(s) {
  const map = { pending: '等待中', running: '运行中', paused: '已暂停', completed: '已完成', failed: '失败' }
  return map[s] || s
}

function taskTypeLabel(t) {
  const map = { fetch_urls: '抓取链接', crawl_articles: '爬取正文', crawl_content: '爬取正文', fetch_stats: '抓取阅读量', full_pipeline: '全流程' }
  return map[t] || t
}

function taskTypeTag(t) {
  const map = { fetch_urls: '', crawl_articles: 'success', crawl_content: 'success', fetch_stats: 'warning', full_pipeline: 'danger' }
  return map[t] || ''
}

async function fetchTasks() {
  loading.value = true
  try {
    const res = await listTasks({ page: page.value, page_size: pageSize.value })
    tasks.value = res.items || []
    total.value = res.total || 0
  } catch (_) {}
  loading.value = false
}

async function onCreateTask(form) {
  showCreateDialog.value = false
  try {
    const task = await createTask(form)
    ElMessage.success(`任务 #${task.id} 已创建`)
    // 自动启动
    await apiStart(task.id)
    ElMessage.success(`任务 #${task.id} 已启动`)
    fetchTasks()
  } catch (_) {}
}

async function startTask(id) {
  await apiStart(id)
  ElMessage.success('任务已启动')
  fetchTasks()
}

async function pauseTask(id) {
  await apiPause(id)
  ElMessage.success('任务已暂停')
  fetchTasks()
}

async function viewLogs(row) {
  logTaskId.value = row.id
  try {
    const logs = await getTaskLogs(row.id, 200)
    cachedLogs.value = (logs || []).map(l => ({
      level: l.level,
      message: l.message,
      time: l.created_at ? new Date(l.created_at).toTimeString().slice(0, 8) : '',
    }))
  } catch (_) {
    cachedLogs.value = []
  }
}

async function deleteTask(id) {
  await apiDelete(id)
  ElMessage.success('任务已删除')
  fetchTasks()
}

// 定时刷新（显示运行中任务的最新状态）
let timer = null
onMounted(() => {
  fetchTasks()
  timer = setInterval(() => {
    // 如果有运行中的任务，静默刷新
    if (tasks.value.some(t => t.status === 'running')) {
      fetchTasks()
    }
  }, 5000)
})
</script>
