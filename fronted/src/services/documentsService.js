import api from './api'

export const documentsApi = {
  upload(file, onUploadProgress) {
    const form = new FormData()
    form.append('file', file)
    return api.post('/documents/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress,
    })
  },
  analyze(payload) {
    // payload: { document_id, analysis_type, custom_prompt? }
    return api.post('/documents/analyze', payload)
  },
  chat(payload) {
    // payload: { document_id, session_id?, message }
    return api.post('/documents/chat', payload)
  },
  chatFeedback(chatId, feedback) {
    // feedback: 'like' | 'dislike'
    return api.put(`/documents/chat/${chatId}/feedback`, { feedback })
  },
  list(params = {}) {
    // params: { page, page_size, search? }
    return api.get('/documents/', { params })
  },
  history(params = {}) {
    return api.get('/documents/history', { params })
  },
  stats() {
    return api.get('/documents/stats')
  },
  detail(id) {
    return api.get(`/documents/${id}`)
  },
  chatMessages(sessionId) {
    return api.get(`/documents/chat/${sessionId}/messages`)
  },
  remove(id) {
    return api.delete(`/documents/${id}`)
  },
}
