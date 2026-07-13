<template>
  <div>
    <h2 style="margin-bottom: 20px">📊 仪表盘</h2>

    <!-- 统计卡片 -->
    <el-row :gutter="16" style="margin-bottom: 24px">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #e6f7ff"><el-icon :size="28" color="#1890ff"><Document /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ overview.total_articles }}</div>
              <div class="stat-label">文章总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #fff7e6"><el-icon :size="28" color="#fa8c16"><View /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ formatNum(overview.total_reads) }}</div>
              <div class="stat-label">总阅读量</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #f6ffed"><el-icon :size="28" color="#52c41a"><List /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ overview.total_tasks }}</div>
              <div class="stat-label">总任务数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #f0f5ff"><el-icon :size="28" color="#2f54eb"><CircleCheck /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ overview.completed_tasks }} / {{ overview.total_tasks }}</div>
              <div class="stat-label">已完成 / 总任务</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 运行中的任务 -->
    <el-card shadow="never" style="margin-bottom: 24px">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span><el-icon><VideoPlay /></el-icon> 运行中的任务 ({{ runningTasks.length }})</span>
          <el-button type="primary" size="small" @click="$router.push('/tasks')">查看全部</el-button>
        </div>
      </template>
      <div v-if="runningTasks.length === 0" style="color: #999; text-align: center; padding: 20px">
        暂无运行中的任务，前往任务管理创建新任务
      </div>
      <div v-for="t in runningTasks" :key="t.id">
        <TaskProgressCard :task="t" @pause="handlePause" />
      </div>
    </el-card>

    <!-- 快捷操作 + 最近任务 -->
    <el-row :gutter="16">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><span>⚡ 快捷操作</span></template>
          <div style="display: flex; flex-direction: column; gap: 12px">
            <el-button type="primary" @click="$router.push('/config')">
              <el-icon><Setting /></el-icon> 配置 Token / Cookie
            </el-button>
            <el-button type="success" @click="$router.push('/tasks')">
              <el-icon><Plus /></el-icon> 创建抓取链接任务
            </el-button>
            <el-button type="warning" @click="$router.push('/articles')">
              <el-icon><Search /></el-icon> 浏览已抓取文章
            </el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><span>📋 最近任务</span></template>
          <el-table :data="recentTasks" size="small" style="width: 100%">
            <el-table-column prop="id" label="ID" width="50" />
            <el-table-column prop="type" label="类型" width="90">
              <template #default="{ row }">
                <el-tag size="small">{{ row.type === 'fetch_urls' ? '抓取链接' : '爬取文章' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="statusType(row.status)" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="进度">
              <template #default="{ row }">
                <el-progress
                  v-if="row.total_count > 0"
                  :percentage="Math.round((row.success_count / row.total_count) * 100)"
                  :stroke-width="8"
                />
                <span v-else>-</span>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="recentTasks.length === 0" style="color: #999; text-align: center; padding: 20px">
            暂无任务记录
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getOverview } from '../api/stats'
import { listTasks, pauseTask } from '../api/task'
import TaskProgressCard from '../components/task/TaskProgressCard.vue'
import { ElMessage } from 'element-plus'

const overview = ref({ total_articles: 0, total_reads: 0, total_tasks: 0, completed_tasks: 0, running_tasks: 0 })
const runningTasks = ref([])
const recentTasks = ref([])

function formatNum(n) {
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return n?.toLocaleString?.() || String(n)
}

function statusType(s) {
  const map = { pending: 'info', running: 'primary', paused: 'warning', completed: 'success', failed: 'danger' }
  return map[s] || 'info'
}

async function handlePause(id) {
  await pauseTask(id)
  ElMessage.success('任务已暂停')
  fetchData()
}

async function fetchData() {
  try {
    overview.value = await getOverview()
  } catch (_) {}
  try {
    const res = await listTasks({ page_size: 100 })
    const items = res.items || []
    runningTasks.value = items.filter(t => t.status === 'running' || t.status === 'paused')
    recentTasks.value = items.slice(0, 5)
  } catch (_) {}
}

onMounted(fetchData)
</script>

<style scoped>
.stat-card { display: flex; align-items: center; gap: 16px; }
.stat-icon { width: 56px; height: 56px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
.stat-value { font-size: 28px; font-weight: 700; color: #303133; }
.stat-label { font-size: 13px; color: #909399; margin-top: 2px; }
</style>
