<template>
  <div>
    <!-- Phase 筛选标签 -->
    <div class="phase-filters" v-if="phases.length > 1">
      <el-tag
        v-for="p in phases"
        :key="p.value"
        :type="phaseFilter === p.value ? 'primary' : 'info'"
        :effect="phaseFilter === p.value ? 'dark' : 'plain'"
        size="small"
        style="cursor: pointer; margin-right: 6px; margin-bottom: 8px"
        @click="phaseFilter = phaseFilter === p.value ? '' : p.value"
      >
        {{ p.label }}
      </el-tag>
      <el-tag v-if="phaseFilter" size="small" type="warning" style="cursor: pointer" @click="phaseFilter = ''">
        清除筛选
      </el-tag>
    </div>

    <!-- 日志终端 -->
    <div class="log-terminal" ref="terminalRef">
      <div v-if="filteredLogs.length === 0" style="color: #999; text-align: center; padding: 40px">
        {{ connected ? '⏳ 等待日志...' : '暂无日志，启动任务后将在此实时显示...' }}
      </div>
      <div v-for="(log, idx) in filteredLogs" :key="idx" class="log-line" :class="log.level">
        <span class="log-phase" v-if="log.phase">[{{ phaseLabel(log.phase) }}]</span>
        <span class="log-time">{{ log.time || '' }}</span>
        <span class="log-msg">{{ log.message }}</span>
      </div>
      <div v-if="connected && filteredLogs.length > 0" class="log-line info">
        <span class="log-time">{{ now }}</span>
        <span class="log-msg">● 实时监听中...</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { getTaskLogs } from '../../api/task'

const props = defineProps({
  taskId: { type: Number, default: 0 },
  initialLogs: { type: Array, default: () => [] },
})

const logs = ref([])
const connected = ref(false)
const phaseFilter = ref('')
const terminalRef = ref(null)
let ws = null
let lastLogTime = null

const phaseMap = {
  searching: '搜索',
  fetching: '抓取',
  crawling: '爬取',
  stats: '统计',
  retry: '重试',
  pipeline: '流程',
}

const phases = computed(() => {
  const seen = new Set()
  const result = []
  for (const l of logs.value) {
    if (l.phase && !seen.has(l.phase)) {
      seen.add(l.phase)
      result.push({ value: l.phase, label: phaseMap[l.phase] || l.phase })
    }
  }
  return result
})

const filteredLogs = computed(() => {
  if (!phaseFilter.value) return logs.value
  return logs.value.filter(l => l.phase === phaseFilter.value)
})

const now = computed(() => new Date().toTimeString().slice(0, 8))

function phaseLabel(p) { return phaseMap[p] || p }

function connect() {
  if (!props.taskId || props.taskId === 0) return
  if (ws) ws.close()

  const apiBase = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')
  const wsUrl = apiBase.replace(/^http/, 'ws')
  ws = new WebSocket(`${wsUrl}/ws/tasks/${props.taskId}`)

  ws.onopen = () => {
    connected.value = true
    // 重连后补拉断线期间的日志
    if (lastLogTime) {
      fetchMissingLogs()
    }
  }
  ws.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      if (data.type === 'log') {
        logs.value.push(data)
        if (data.time) lastLogTime = data.time
        nextTick(() => {
          if (terminalRef.value) {
            terminalRef.value.scrollTop = terminalRef.value.scrollHeight
          }
        })
      }
    } catch (_) {}
  }
  ws.onclose = () => { connected.value = false; setTimeout(() => { if (props.taskId > 0) connect() }, 3000) }
  ws.onerror = () => { connected.value = false }
}

async function fetchMissingLogs() {
  try {
    const res = await getTaskLogs(props.taskId, 500)
    if (res && res.length > 0) {
      // 合并：去重后只追加新日志
      const existingTimes = new Set(logs.value.map(l => l.time + l.message))
      for (const l of res) {
        const t = l.created_at ? new Date(l.created_at).toTimeString().slice(0, 8) : ''
        const key = t + l.message
        if (!existingTimes.has(key)) {
          logs.value.push({
            level: l.level, message: l.message, phase: l.phase || '',
            time: t,
          })
        }
      }
    }
  } catch (_) {}
}

function disconnect() {
  if (ws) { ws.close(); ws = null }
  connected.value = false
}

watch(() => props.taskId, (newVal) => {
  if (newVal && newVal > 0) {
    logs.value = [...props.initialLogs]
    lastLogTime = null
    connect()
  } else {
    disconnect()
  }
})

onMounted(() => {
  logs.value = [...props.initialLogs]
  if (props.taskId && props.taskId > 0) connect()
})

onUnmounted(() => { disconnect() })
</script>

<style scoped>
.phase-filters { margin-bottom: 8px; }
.log-terminal {
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 13px;
  padding: 12px;
  border-radius: 6px;
  height: 400px;
  overflow-y: auto;
  line-height: 1.6;
}
.log-line { display: flex; gap: 8px; padding: 2px 0; }
.log-phase { color: #c586c0; white-space: nowrap; flex-shrink: 0; font-size: 11px; }
.log-time { color: #6a9955; white-space: nowrap; flex-shrink: 0; }
.log-line.success .log-msg { color: #4ec9b0; }
.log-line.error .log-msg { color: #f48771; }
.log-line.warning .log-msg { color: #dcdcaa; }
.log-line.info .log-msg { color: #9cdcfe; }
</style>
