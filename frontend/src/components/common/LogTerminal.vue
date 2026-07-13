<template>
  <div class="log-terminal" ref="terminalRef">
    <div v-if="logs.length === 0" style="color: #999; text-align: center; padding: 40px">
      暂无日志，启动任务后将在此实时显示...
    </div>
    <div v-for="(log, idx) in logs" :key="idx" class="log-line" :class="log.level">
      <span class="log-time">{{ log.time || '' }}</span>
      <span class="log-msg">{{ log.message }}</span>
    </div>
    <div v-if="connected" class="log-line info">
      <span class="log-time">{{ now }}</span>
      <span class="log-msg">⏳ 等待新日志...</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'

const props = defineProps({
  taskId: { type: Number, default: 0 },
  initialLogs: { type: Array, default: () => [] },
})

const logs = ref([])
const connected = ref(false)
const terminalRef = ref(null)
let ws = null

const now = computed(() => {
  const d = new Date()
  return d.toTimeString().slice(0, 8)
})

function connect() {
  if (!props.taskId || props.taskId === 0) return
  if (ws) ws.close()

  const apiBase = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')
  const wsUrl = apiBase.replace(/^http/, 'ws')
  ws = new WebSocket(`${wsUrl}/ws/tasks/${props.taskId}`)

  ws.onopen = () => { connected.value = true }
  ws.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      if (data.type === 'log') {
        logs.value.push(data)
        nextTick(() => {
          if (terminalRef.value) {
            terminalRef.value.scrollTop = terminalRef.value.scrollHeight
          }
        })
      }
    } catch (_) {}
  }
  ws.onclose = () => { connected.value = false }
  ws.onerror = () => { connected.value = false }
}

function disconnect() {
  if (ws) { ws.close(); ws = null }
  connected.value = false
}

watch(() => props.taskId, (newVal) => {
  if (newVal && newVal > 0) {
    logs.value = [...props.initialLogs]
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
.log-line { display: flex; gap: 10px; padding: 2px 0; }
.log-time { color: #6a9955; white-space: nowrap; flex-shrink: 0; }
.log-line.success .log-msg { color: #4ec9b0; }
.log-line.error .log-msg { color: #f48771; }
.log-line.warning .log-msg { color: #dcdcaa; }
.log-line.info .log-msg { color: #9cdcfe; }
</style>
