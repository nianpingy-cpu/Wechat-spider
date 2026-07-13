<template>
  <div>
    <h2 style="margin-bottom: 20px">📈 统计看板</h2>

    <!-- 总览卡片 -->
    <el-row :gutter="16" style="margin-bottom: 24px">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-value">{{ overview.total_articles }}</div>
            <div class="stat-label">文章总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-value">{{ formatNum(overview.total_reads) }}</div>
            <div class="stat-label">总阅读量</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-value">{{ overview.completed_tasks }}</div>
            <div class="stat-label">已完成任务</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-value">{{ overview.running_tasks }}</div>
            <div class="stat-label">运行中任务</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="16" style="margin-bottom: 24px">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>📅 每日文章发布数量</template>
          <div ref="dailyChartRef" style="height: 350px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>🏆 阅读量 Top 10</template>
          <div ref="topReadChartRef" style="height: 350px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Top 10 表格 -->
    <el-card shadow="never">
      <template #header>🔥 热门文章 Top 10</template>
      <el-table :data="topRead" stripe style="width: 100%">
        <el-table-column type="index" label="排名" width="60" />
        <el-table-column prop="title" label="标题" min-width="280" show-overflow-tooltip />
        <el-table-column prop="publish_date" label="发布日期" width="140" />
        <el-table-column prop="read_count" label="阅读量" width="120" sortable>
          <template #default="{ row }">
            <span style="color: #f56c6c; font-weight: 600">{{ row.read_count.toLocaleString() }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { getOverview, getDailyStats, getTopRead } from '../api/stats'
import * as echarts from 'echarts'

const overview = ref({ total_articles: 0, total_reads: 0, completed_tasks: 0, running_tasks: 0 })
const topRead = ref([])

const dailyChartRef = ref(null)
const topReadChartRef = ref(null)

function formatNum(n) {
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return n?.toLocaleString?.() || String(n)
}

onMounted(async () => {
  // 加载数据
  try { overview.value = await getOverview() } catch (_) {}
  try { topRead.value = await getTopRead(10) } catch (_) {}

  let dailyStats = []
  try { dailyStats = await getDailyStats() } catch (_) {}

  // 渲染图表
  await nextTick()

  // 每日文章数量柱状图
  if (dailyChartRef.value && dailyStats.length > 0) {
    const chart = echarts.init(dailyChartRef.value)
    chart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: dailyStats.map(d => d.date),
        axisLabel: { rotate: 30, fontSize: 11 },
      },
      yAxis: { type: 'value', name: '文章数' },
      series: [{
        name: '文章数',
        type: 'bar',
        data: dailyStats.map(d => d.count),
        itemStyle: { color: '#409EFF', borderRadius: [4, 4, 0, 0] },
      }],
      grid: { left: 50, right: 20, top: 20, bottom: 60 },
    })
    window.addEventListener('resize', () => chart.resize())
  }

  // 阅读量 Top 10 横向柱状图
  if (topReadChartRef.value && topRead.value.length > 0) {
    const chart = echarts.init(topReadChartRef.value)
    const names = topRead.value.map(a => a.title.length > 15 ? a.title.slice(0, 15) + '...' : a.title)
    chart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'value', name: '阅读量' },
      yAxis: {
        type: 'category',
        data: names.reverse(),
        axisLabel: { fontSize: 11 },
      },
      series: [{
        name: '阅读量',
        type: 'bar',
        data: [...topRead.value].reverse().map(a => a.read_count),
        itemStyle: { color: '#f56c6c', borderRadius: [0, 4, 4, 0] },
      }],
      grid: { left: 140, right: 20, top: 10, bottom: 20 },
    })
    window.addEventListener('resize', () => chart.resize())
  }
})
</script>

<style scoped>
.stat-card { text-align: center; padding: 8px 0; }
.stat-value { font-size: 32px; font-weight: 700; color: #303133; }
.stat-label { font-size: 13px; color: #909399; margin-top: 4px; }
</style>
