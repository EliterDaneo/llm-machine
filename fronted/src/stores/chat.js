import { defineStore } from 'pinia'
import { documentsApi } from '../services/documentsService'

export const useChatStore = defineStore('chat', {
  state: () => ({
    currentSessionId: null,
    messages: [],
    isSending: false,
    isLoadingMessages: false,
  }),

  actions: {
    async loadSession(sessionId) {
      this.isLoadingMessages = true
      this.currentSessionId = sessionId
      try {
        const { data } = await documentsApi.chatMessages(sessionId)

        // PERBAIKAN 1: Ambil key "messages" dari response backend (default ke array kosong)
        this.messages = data.messages || []

        return this.messages
      } catch (error) {
        console.error("Gagal memuat sesi:", error)
        this.messages = [] // Reset jika error agar tidak crash
        throw error
      } finally {
        this.isLoadingMessages = false
      }
    },

    startNewSession() {
      this.currentSessionId = null
      this.messages = []
    },

    async sendMessage({ documentId, message }) {
      // Simpan ID lokal untuk diganti dengan ID asli dari DB nanti
      const localMsgId = `local-${Date.now()}`

      // Optimistic render bubble user
      this.messages.push({
        id: localMsgId,
        role: 'user',
        content: message,
        created_at: new Date().toISOString(),
      })

      this.isSending = true
      try {
        const { data } = await documentsApi.chat({
          document_id: documentId,
          session_id: this.currentSessionId,
          message,
        })

        this.currentSessionId = data.session_id || this.currentSessionId

        // PERBAIKAN 2: Timpa pesan optimistic user dengan data asli dari database
        // (Penting agar pesan user memiliki ID UUID asli untuk fitur feedback, dll)
        if (data.user_message) {
          const idx = this.messages.findIndex(m => m.id === localMsgId)
          if (idx !== -1) {
            this.messages[idx] = data.user_message
          }
        }

        // PERBAIKAN 3: Masukkan pesan assistant dari object "assistant_message"
        if (data.assistant_message) {
          this.messages.push(data.assistant_message)
        }

        return data
      } finally {
        this.isSending = false
      }
    },

    async giveFeedback(chatId, feedback) {
      await documentsApi.chatFeedback(chatId, feedback)
      const msg = this.messages.find((m) => m.id === chatId)
      if (msg) msg.feedback = feedback
    },
  },
})