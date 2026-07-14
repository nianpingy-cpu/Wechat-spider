<template>
  <el-dialog v-model="visible" title="微信扫码登录" width="420px" :close-on-click-modal="false" @close="cancelScan">
    <div v-if="status === 'scanning' || status === 'starting'" style="text-align: center">
      <img v-if="qrImage" :src="qrImage" style="width: 280px; height: 280px; border: 1px solid #eee; border-radius: 8px" />
      <el-skeleton v-else style="width: 280px; height: 280px; margin: 0 auto" animated>
        <template #template>
          <el-skeleton-item variant="image" style="width: 280px; height: 280px" />
        </template>
      </el-skeleton>
      <p style="margin-top: 16px; color: #606266">
        <el-icon class="is-loading"><Loading /></el-icon>
        请用微信扫描二维码
      </p>
      <p style="font-size: 12px; color: #c0c4cc">打开微信 → 扫一扫 → 确认登录</p>
    </div>

    <div v-else-if="status === 'done'" style="text-align: center; padding: 20px">
      <el-result icon="success" title="登录成功！" sub-title="Cookie / Token / AppMsg Token 已自动填入">
        <template #extra>
          <el-button type="primary" @click="visible = false">关闭</el-button>
        </template>
      </el-result>
    </div>

    <div v-else-if="status === 'error'" style="text-align: center; padding: 20px">
      <el-result icon="error" title="登录失败" :sub-title="errorMsg">
        <template #extra>
          <el-button @click="cancelScan">关闭</el-button>
          <el-button type="primary" @click="startScan">重新扫码</el-button>
        </template>
      </el-result>
    </div>

    <div v-else-if="status === 'timeout'" style="text-align: center; padding: 20px">
      <el-result icon="warning" title="扫码超时" sub-title="请重新发起扫码">
        <template #extra>
          <el-button type="primary" @click="startScan">重新扫码</el-button>
        </template>
      </el-result>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue'
import { getConfigs } from '../../api/config'
import { ElMessage } from 'element-plus'

const props = defineProps({ modelValue: { type: Boolean, default: false } })
const emit = defineEmits(['update:modelValue', 'loggedIn'])

const visible = ref(props.modelValue)
const status = ref('idle')
const qrImage = ref('')
const errorMsg = ref('')
let ws = null
let scanId = ''

watch(() => props.modelValue, (v) => { visible.value = v; if (v) startScan() })
watch(visible, (v) => emit('update:modelValue', v))

function startScan() {
  scanId = Math.random().toString(36).slice(2, 10)
  status.value = 'starting'
  qrImage.value = ''
  errorMsg.value = ''

  if (ws) ws.close()

  const apiBase = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')
  const wsUrl = apiBase.replace(/^http/, 'ws')
  ws = new WebSocket(`${wsUrl}/ws/qrcode/${scanId}`)

  ws.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      if (data.type === 'qrcode') {
        qrImage.value = data.image
        if (status.value === 'starting') status.value = 'scanning'
      } else if (data.type === 'login_success') {
        status.value = 'done'
        ElMessage.success('登录成功！自动填写配置中...')
        // 刷新配置
        setTimeout(async () => {
          emit('loggedIn')
        }, 800)
        if (ws) ws.close()
      } else if (data.type === 'login_timeout') {
        status.value = 'timeout'
        if (ws) ws.close()
      } else if (data.type === 'login_error') {
        status.value = 'error'
        errorMsg.value = data.message || '未知错误'
        if (ws) ws.close()
      }
    } catch (_) {}
  }

  ws.onerror = () => {
    if (status.value !== 'done') {
      status.value = 'error'
      errorMsg.value = 'WebSocket 连接失败'
    }
  }
}

function cancelScan() {
  if (ws) { try { ws.send('cancel') } catch (_) {}; ws.close(); ws = null }
  status.value = 'idle'
  visible.value = false
}

onUnmounted(cancelScan)
</script>
