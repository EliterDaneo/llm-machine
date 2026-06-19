<script setup>
import { onMounted, ref } from 'vue'
import { useDocumentsStore } from '../stores/documents'
import { useChatStore } from '../stores/chat'
import { formatRelativeTime, truncate } from '../utils/formatters'
import DashboardLayout from '../components/layout/DashboardLayout.vue'
import Badge from '../components/ui/Badge.vue'

const docsStore = useDocumentsStore()
const chatStore = useChatStore()

const selectedSessionId = ref(null)
const isLoadingMessages = ref(false)

onMounted(() => {
  docsStore.fetchHistory().catch(() => { })
})

async function openSession(item) {
  selectedSessionId.value = item.session_id || item.id
  isLoadingMessages.value = true
  try {
    await chatStore.loadSession(selectedSessionId.value)
  } finally {
    isLoadingMessages.value = false
  }
}
</script>

<template>
  <DashboardLayout title="Riwayat Chat & Analisis" subtitle="Lihat kembali percakapan dan hasil analisis sebelumnya">
    <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <!-- Session list -->
      <div class="card lg:col-span-1">
        <div class="border-b border-ink/8 px-4 py-3">
          <h3 class="font-display text-sm font-semibold text-ink">Sesi Chat</h3>
        </div>
        <div class="max-h-[60vh] overflow-y-auto">
          <button v-for="item in docsStore.chatSessions" :key="item.session_id || item.id"
            class="flex w-full flex-col items-start gap-1 border-b border-ink/6 px-4 py-3 text-left transition last:border-0 hover:bg-paper-dim/60"
            :class="selectedSessionId === (item.session_id || item.id) ? 'bg-highlight-soft' : ''"
            @click="openSession(item)">
            <span class="truncate text-sm font-medium text-ink">{{ item.document_filename || item.filename || 'Dokumen'
              }}</span>
            <span class="truncate text-xs text-ink/45">{{ truncate(item.last_message || item.preview || '', 60)
              }}</span>
            <span class="text-[11px] text-ink/35">{{ formatRelativeTime(item.updated_at || item.created_at) }}</span>
          </button>
          <div v-if="!docsStore.chatSessions.length" class="px-4 py-10 text-center text-sm text-ink/40">
            Belum ada riwayat chat.
          </div>
        </div>
      </div>

      <!-- Selected conversation -->
      <div class="card flex flex-col lg:col-span-2">
        <div class="border-b border-ink/8 px-5 py-3.5">
          <h3 class="font-display text-sm font-semibold text-ink">Percakapan</h3>
        </div>
        <div class="flex-1 space-y-3 overflow-y-auto p-5" style="min-height: 50vh">
          <div v-if="!selectedSessionId" class="flex h-full items-center justify-center text-sm text-ink/40">
            Pilih sesi chat di samping untuk melihat isi percakapan.
          </div>
          <div v-else-if="isLoadingMessages" class="flex h-full items-center justify-center text-sm text-ink/40">
            Memuat percakapan…
          </div>
          <template v-else>
            <div v-for="msg in chatStore.messages" :key="msg.id" class="flex"
              :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
              <div class="max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed"
                :class="msg.role === 'user' ? 'rounded-br-sm bg-ink text-paper' : 'rounded-bl-sm bg-paper-dim text-ink/85'">
                <p class="whitespace-pre-wrap">{{ msg.content }}</p>
                <span class="mt-1 block text-[11px] opacity-50">{{ formatRelativeTime(msg.created_at) }}</span>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- Analysis history -->
    <div v-if="docsStore.analysisHistory.length" class="mt-8">
      <h2 class="mb-3 font-display text-lg font-semibold text-ink">Riwayat Analisis</h2>
      <div class="card overflow-hidden">
        <table class="w-full text-left text-sm">
          <thead class="border-b border-ink/8 bg-paper-dim/60 text-xs uppercase tracking-wide text-ink/45">
            <tr>
              <th class="px-5 py-3 font-semibold">Dokumen</th>
              <th class="px-5 py-3 font-semibold">Jenis</th>
              <th class="px-5 py-3 font-semibold">Provider</th>
              <th class="px-5 py-3 font-semibold">Waktu</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in docsStore.analysisHistory" :key="item.id" class="border-b border-ink/6 last:border-0">
              <td class="px-5 py-3 text-ink">{{ item.document_filename || item.filename }}</td>
              <td class="px-5 py-3">
                <Badge tone="neutral">{{ item.analysis_type }}</Badge>
              </td>
              <td class="px-5 py-3 text-ink/60">{{ item.provider || '-' }}</td>
              <td class="px-5 py-3 text-ink/55">{{ formatRelativeTime(item.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </DashboardLayout>
</template>
