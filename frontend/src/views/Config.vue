<template>
  <div>
    <h2 style="margin-bottom: 20px">⚙️ 配置管理</h2>
    <p style="color: #909399; margin-bottom: 20px">
      在此配置微信公众号接口的认证信息。Token 和 Cookie 需通过浏览器 F12 抓包获取，详见项目 README。
    </p>

    <el-card shadow="never" style="max-width: 720px">
      <template #header><span>认证配置</span></template>

      <el-form :model="form" label-width="120px" v-loading="loading">
        <el-form-item label="公众号名称">
          <el-input v-model="form.target_name" placeholder="例如：公安部刑侦局" />
        </el-form-item>

        <el-form-item label="Token">
          <el-input v-model="form.token" placeholder="从浏览器地址栏 token= 参数获取" />
          <div class="form-tip">登录 mp.weixin.qq.com 后，从网址 ?token=XXXX 中获取</div>
        </el-form-item>

        <el-form-item label="Cookie">
          <el-input v-model="form.cookie" type="textarea" :rows="4" placeholder="从浏览器 Network 面板请求 Headers 中获取" />
          <div class="form-tip">F12 → Network → 任意请求 → Request Headers → Cookie</div>
        </el-form-item>

        <el-form-item label="AppMsg Token">
          <el-input v-model="form.appmsg_token" placeholder="从 getappmsgext 请求参数中获取（用于抓取阅读量）" />
          <div class="form-tip">在电脑微信中点开一篇文章，Network 中搜索 getappmsgext，复制 appmsg_token 参数值</div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="saveConfig" :loading="saving">
            <el-icon><Check /></el-icon> 保存配置
          </el-button>
          <el-button type="success" @click="doTest" :loading="testing" style="margin-left: 12px">
            <el-icon><Connection /></el-icon> 测试连接
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 测试结果 -->
      <el-alert
        v-if="testResult"
        :title="testResult.message"
        :type="testResult.success ? 'success' : 'error'"
        :closable="true"
        show-icon
        style="margin-top: 16px"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getConfigs, updateConfig, testToken } from '../api/config'
import { ElMessage } from 'element-plus'

const loading = ref(true)
const saving = ref(false)
const testing = ref(false)
const testResult = ref(null)

const form = reactive({
  token: '',
  cookie: '',
  appmsg_token: '',
  target_name: '',
})

onMounted(async () => {
  try {
    const configs = await getConfigs()
    for (const c of configs) {
      if (c.key in form) form[c.key] = c.value
    }
  } catch (_) {}
  loading.value = false
})

async function saveConfig() {
  saving.value = true
  try {
    const items = Object.entries(form).map(([key, value]) => ({ key, value }))
    await updateConfig(items)
    ElMessage.success('配置已保存')
  } catch (_) {}
  saving.value = false
}

async function doTest() {
  testing.value = true
  testResult.value = null
  try {
    // 先保存
    const items = Object.entries(form).map(([key, value]) => ({ key, value }))
    await updateConfig(items)

    const res = await testToken()
    testResult.value = res
  } catch (e) {
    testResult.value = { success: false, message: '测试请求失败: ' + (e.message || '未知错误') }
  }
  testing.value = false
}
</script>

<style scoped>
.form-tip { font-size: 12px; color: #c0c4cc; margin-top: 4px; }
</style>
