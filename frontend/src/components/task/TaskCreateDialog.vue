<template>
  <el-dialog v-model="visible" title="创建新任务" width="500px" @close="resetForm">
    <el-form :model="form" label-width="100px">
      <el-form-item label="任务类型">
        <el-radio-group v-model="form.type">
          <el-radio value="fetch_urls">抓取链接</el-radio>
          <el-radio value="crawl_content">爬取正文</el-radio>
          <el-radio value="fetch_stats">抓取阅读量</el-radio>
          <el-radio value="full_pipeline">🚀 全流程一键</el-radio>
        </el-radio-group>
      </el-form-item>

      <template v-if="form.type === 'fetch_urls' || form.type === 'full_pipeline'">
        <el-form-item label="起始页码">
          <el-input-number v-model="form.start_page" :min="0" :max="10000" />
        </el-form-item>
        <el-form-item label="结束页码">
          <el-input-number v-model="form.end_page" :min="1" :max="10000" />
        </el-form-item>
        <el-form-item v-if="form.type === 'fetch_urls'" label="输出文件">
          <el-input v-model="form.input_file" placeholder="url_(1-50).txt" />
        </el-form-item>
      </template>

      <template v-if="form.type === 'crawl_content'">
        <el-form-item label="输入文件">
          <el-select v-model="form.input_file" filterable allow-create placeholder="选择 URL 文件">
            <el-option v-for="f in urlFiles" :key="f" :label="f" :value="f" />
          </el-select>
        </el-form-item>
      </template>

      <template v-if="form.type === 'fetch_stats'">
        <el-alert type="info" :closable="false" show-icon style="margin-bottom: 12px">
          将遍历数据库中所有已有文章，更新其阅读量、点赞数和在看数。
        </el-alert>
      </template>

      <template v-if="form.type === 'full_pipeline'">
        <el-alert type="success" :closable="false" show-icon style="margin-bottom: 12px">
          自动串联 3 步：抓取链接 → 爬取正文 → 更新阅读量，全自动完成。
        </el-alert>
      </template>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="onConfirm" :loading="loading">创建任务</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  urlFiles: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:modelValue', 'confirm'])

const visible = ref(props.modelValue)
const loading = ref(false)

watch(() => props.modelValue, (v) => { visible.value = v })
watch(visible, (v) => emit('update:modelValue', v))

const form = reactive({
  type: 'fetch_urls',
  start_page: 1,
  end_page: 50,
  input_file: '',
})

watch(() => form.type, (t) => {
  if (t === 'fetch_urls' && !form.input_file) {
    form.input_file = `url_(${form.start_page}-${form.end_page}).txt`
  }
})

function resetForm() {
  form.type = 'fetch_urls'
  form.start_page = 1
  form.end_page = 50
  form.input_file = ''
}

function onConfirm() {
  if (form.type === 'fetch_urls' && !form.input_file) {
    form.input_file = `url_(${form.start_page}-${form.end_page}).txt`
  }
  loading.value = true
  emit('confirm', { ...form })
  setTimeout(() => { loading.value = false }, 500)
}
</script>
