<template>
  <el-dialog v-model="visible" title="文章预览" width="800px" top="20px" @close="content = ''">
    <div v-if="loading" style="text-align: center; padding: 40px">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
      <p style="margin-top: 12px; color: #999">加载中...</p>
    </div>
    <div v-else-if="content" class="markdown-body" v-html="renderedHtml"></div>
    <el-empty v-else description="暂无内容" />
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { getArticle } from '../../api/article'
import MarkdownIt from 'markdown-it'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  articleId: { type: Number, default: 0 },
})

const emit = defineEmits(['update:modelValue'])

const visible = ref(props.modelValue)
const loading = ref(false)
const content = ref('')

watch(() => props.modelValue, (v) => { visible.value = v })
watch(visible, (v) => emit('update:modelValue', v))

watch(() => props.articleId, async (id) => {
  if (id && id > 0) {
    loading.value = true
    try {
      const res = await getArticle(id)
      content.value = res.content || ''
    } catch (_) {
      content.value = ''
    }
    loading.value = false
  }
})

const md = new MarkdownIt({ html: false, linkify: true })
const renderedHtml = computed(() => {
  if (!content.value) return ''
  return md.render(content.value)
})
</script>

<style scoped>
.markdown-body {
  max-height: 65vh;
  overflow-y: auto;
  padding: 16px;
  line-height: 1.8;
  font-size: 14px;
}
.markdown-body :deep(h1) { font-size: 22px; margin-bottom: 12px; }
.markdown-body :deep(h2) { font-size: 18px; margin: 16px 0 8px; }
.markdown-body :deep(p) { margin-bottom: 8px; }
.markdown-body :deep(img) { max-width: 100%; }
</style>
