<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px">
      <h2>📄 文章浏览</h2>
      <div style="display: flex; gap: 8px">
        <el-button @click="doExport('csv')">
          <el-icon><Download /></el-icon> 导出 CSV
        </el-button>
        <el-button @click="doExport('json')">
          <el-icon><Download /></el-icon> 导出 JSON
        </el-button>
      </div>
    </div>

    <!-- 搜索区 -->
    <el-card shadow="never" style="margin-bottom: 16px">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="搜索文章标题" clearable @clear="fetchArticles" @keyup.enter="fetchArticles" />
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY年MM月DD日"
            style="width: 280px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchArticles">
            <el-icon><Search /></el-icon> 搜索
          </el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 文章列表 -->
    <el-card shadow="never">
      <el-table :data="articles" stripe v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="publish_date" label="发布日期" width="130" />
        <el-table-column prop="read_count" label="阅读量" width="100" sortable>
          <template #default="{ row }">
            <span v-if="row.read_count > 0">{{ row.read_count.toLocaleString() }}</span>
            <span v-else style="color: #c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="like_count" label="点赞数" width="80" />
        <el-table-column prop="old_like_count" label="在看数" width="80" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="previewArticle(row.id)">预览</el-button>
            <el-popconfirm title="确定删除此文章？" @confirm="deleteArticle(row.id)">
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
          @change="fetchArticles"
        />
      </div>
    </el-card>

    <!-- 预览弹窗 -->
    <ArticlePreview v-model="showPreview" :article-id="previewId" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { listArticles, deleteArticle as apiDelete, exportCsv, exportJson } from '../api/article'
import ArticlePreview from '../components/article/ArticlePreview.vue'
import { ElMessage } from 'element-plus'

const articles = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const searchForm = reactive({ keyword: '' })
const dateRange = ref(null)

const showPreview = ref(false)
const previewId = ref(0)

async function fetchArticles() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (searchForm.keyword) params.keyword = searchForm.keyword
    if (dateRange.value && dateRange.value.length === 2) {
      params.date_from = dateRange.value[0]
      params.date_to = dateRange.value[1]
    }
    const res = await listArticles(params)
    articles.value = res.items || []
    total.value = res.total || 0
  } catch (_) {}
  loading.value = false
}

function resetSearch() {
  searchForm.keyword = ''
  dateRange.value = null
  page.value = 1
  fetchArticles()
}

function previewArticle(id) {
  previewId.value = id
  showPreview.value = true
}

async function deleteArticle(id) {
  await apiDelete(id)
  ElMessage.success('文章已删除')
  fetchArticles()
}

async function doExport(format) {
  try {
    const params = {}
    if (searchForm.keyword) params.keyword = searchForm.keyword
    let res
    if (format === 'csv') {
      res = await exportCsv(params)
    } else {
      res = await exportJson(params)
    }
    const url = window.URL.createObjectURL(new Blob([res]))
    const link = document.createElement('a')
    link.href = url
    link.download = `articles_export.${format}`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success(`已导出为 ${format.toUpperCase()} 文件`)
  } catch (_) {}
}

onMounted(fetchArticles)
</script>
