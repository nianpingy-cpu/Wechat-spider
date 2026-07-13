import request from './request'

export function getOverview() {
  return request.get('/api/stats/overview')
}

export function getDailyStats() {
  return request.get('/api/stats/daily')
}

export function getTopRead(limit = 10) {
  return request.get('/api/stats/top-read', { params: { limit } })
}
