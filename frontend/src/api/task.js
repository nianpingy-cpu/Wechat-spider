import request from './request'

export function createTask(data) {
  return request.post('/api/tasks', data)
}

export function listTasks(params) {
  return request.get('/api/tasks', { params })
}

export function getTask(id) {
  return request.get(`/api/tasks/${id}`)
}

export function startTask(id) {
  return request.post(`/api/tasks/${id}/start`)
}

export function pauseTask(id) {
  return request.post(`/api/tasks/${id}/pause`)
}

export function retryFailed(id) {
  return request.post(`/api/tasks/${id}/retry-failed`)
}

export function getTaskLogs(id, limit = 200) {
  return request.get(`/api/tasks/${id}/logs`, { params: { limit } })
}

export function deleteTask(id) {
  return request.delete(`/api/tasks/${id}`)
}
