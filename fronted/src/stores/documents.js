import { defineStore } from 'pinia'
import { documentsApi } from '../services/documentsService'

function extractList(data, keys = []) {
  if (Array.isArray(data)) return data
  for (const key of keys) {
    if (Array.isArray(data?.[key])) return data[key]
  }
  console.warn('extractList: tidak menemukan array pada response. Keys tersedia:', data ? Object.keys(data) : data)
  return []
}

export const useDocumentsStore = defineStore('documents', {
  state: () => ({
    documents: [],
    pagination: { page: 1, pageSize: 10, total: 0 },
    stats: null,
    chatSessions: [],
    analysisHistory: [],
    currentDocument: null,
    analyses: [], // hasil analisis untuk currentDocument
    isLoadingList: false,
    isUploading: false,
    isAnalyzing: false,
    uploadProgress: 0,
  }),

  actions: {
    async fetchDocuments(params = {}) {
      this.isLoadingList = true
      try {
        const { data } = await documentsApi.list({
          page: this.pagination.page,
          page_size: this.pagination.pageSize,
          ...params,
        })
        this.documents = extractList(data, ['documents', 'items', 'results'])
        if (data?.pagination) {
          this.pagination = { ...this.pagination, ...data.pagination }
        } else if (data?.total !== undefined) {
          this.pagination.total = data.total
        }
        return this.documents
      } finally {
        this.isLoadingList = false
      }
    },

    async fetchStats() {
      const { data } = await documentsApi.stats()
      this.stats = data
      return data
    },

    async fetchHistory(params = {}) {
      const { data } = await documentsApi.history(params)
      this.chatSessions = extractList(data, ['chat_sessions', 'sessions'])
      this.analysisHistory = extractList(data, ['analyses', 'analysis_history', 'results'])
      return { chatSessions: this.chatSessions, analysisHistory: this.analysisHistory }
    },

    async fetchDocumentDetail(id) {
      const { data } = await documentsApi.detail(id)
      this.currentDocument = data.document ?? data
      this.analyses = extractList(data.document ?? data, ['analyses', 'analysis_results'])
      return this.currentDocument
    },

    async uploadDocument(file) {
      this.isUploading = true
      this.uploadProgress = 0
      try {
        const { data } = await documentsApi.upload(file, (evt) => {
          if (evt.total) {
            this.uploadProgress = Math.round((evt.loaded / evt.total) * 100)
          }
        })
        if (!Array.isArray(this.documents)) this.documents = []
        this.documents.unshift(data)
        return data
      } finally {
        this.isUploading = false
        this.uploadProgress = 0
      }
    },

    async analyzeDocument(payload) {
      this.isAnalyzing = true
      try {
        const { data } = await documentsApi.analyze(payload)
        const analysisObj = data.analysis ?? data
        if (!Array.isArray(this.analyses)) this.analyses = []
        this.analyses.unshift(analysisObj)
        return analysisObj
      } finally {
        this.isAnalyzing = false
      }
    },

    async deleteDocument(id) {
      await documentsApi.remove(id)
      this.documents = (this.documents || []).filter((d) => d.id !== id)
    },
  },
})
