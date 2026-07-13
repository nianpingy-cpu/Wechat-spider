import request from './request'

export function listArticles(params) {
  return request.get('/api/articles', { params })
}

export function getArticle(id) {
  return request.get(`/api/articles/${id}`)
}

export function deleteArticle(id) {
  return request.delete(`/api/articles/${id}`)
}

export function exportCsv(params) {
  return request.get('/api/articles/export/csv', { params, responseType: 'blob' })
}

export function exportJson(params) {
  return request.get('/api/articles/export/json', { params, responseType: 'blob' })
}
