import request from './request'

export function getConfigs() {
  return request.get('/api/config')
}

export function updateConfig(items) {
  return request.put('/api/config', { items })
}

export function testToken() {
  return request.post('/api/config/test-token')
}
