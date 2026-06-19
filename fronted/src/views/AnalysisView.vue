<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDocumentsStore } from '../stores/documents'
import { useChatStore } from '../stores/chat'
import { useToast } from '../composables/useToast'
import { formatBytes, formatDateTime } from '../utils/formatters'
import DashboardLayout from '../components/layout/DashboardLayout.vue'
import AnalysisPanel from '../components/dashboard/AnalysisPanel.vue'
import ChatPanel from '../components/dashboard/ChatPanel.vue'
import BaseModal from '../components/ui/BaseModal.vue'
import Badge from '../components/ui/Badge.vue'

const props = defineProps({
  id: { type: [String, Number], required: true },
})

const router = useRouter()
const docsStore = useDocumentsStore()
const chatStore = useChatStore()
const toast = useToast()

const showDeleteConfirm = ref(false)
const isDeleting = ref(false)

const doc = computed(() => docsStore.currentDocument)

onMounted(async () => {
  chatStore.startNewSession()
  try {
    await docsStore.fetchDocumentDetail(props.id)
  } catch (err) {
    toast.error('Gagal memuat dokumen. Kembali ke daftar dokumen.')
    router.push({ name: 'documents' })
  }
})

async function confirmDelete() {
  isDeleting.value = true
  try {
    await docsStore.deleteDocument(props.id)
    toast.success('Dokumen dihapus.')
    router.push({ name: 'documents' })
  } catch (err) {
    toast.error('Gagal menghapus dokumen.')
  } finally {
    isDeleting.value = false
  }
}
</script>

<template>
  <DashboardLayout :title="doc?.filename || 'Memuat…'" subtitle="Detail dokumen, hasil analisis, dan chat">
    <template #actions>
      <router-link :to="{ name: 'documents' }" class="btn-ghost">← Kembali</router-link>
      <button class="btn-danger" @click="showDeleteConfirm = true">Hapus Dokumen</button>
    </template>

    <div v-if="doc" class="space-y-6">
      <div class="card flex flex-wrap items-center gap-x-8 gap-y-3 p-5 text-sm">
        <div>
          <p class="text-ink/40">Halaman</p>
          <p class="font-mono font-medium text-ink">{{ doc.page_count ?? '-' }}</p>
        </div>
        <div>
          <p class="text-ink/40">Ukuran File</p>
          <p class="font-mono font-medium text-ink">{{ formatBytes(doc.file_size ?? doc.size) }}</p>
        </div>
        <div>
          <p class="text-ink/40">Diunggah</p>
          <p class="font-medium text-ink">{{ formatDateTime(doc.created_at) }}</p>
        </div>
        <div>
          <p class="text-ink/40">Status</p>
          <Badge :tone="doc.status === 'ready' ? 'stamp' : doc.status === 'failed' ? 'rubric' : 'highlight'">
            {{ doc.status }}
          </Badge>
        </div>
      </div>

      <div class="grid grid-cols-1 gap-6 lg:grid-cols-2" style="height: calc(100vh - 320px); min-height: 480px">
        <AnalysisPanel :document-id="doc.id" />
        <ChatPanel :document-id="doc.id" />
      </div>
    </div>

    <div v-else class="flex h-64 items-center justify-center text-ink/40">Memuat dokumen…</div>

    <BaseModal v-model="showDeleteConfirm" title="Hapus dokumen?">
      <p class="text-sm text-ink/60">
        Dokumen ini beserta seluruh riwayat analisis dan chat akan dihapus permanen.
      </p>
      <div class="mt-5 flex justify-end gap-2.5">
        <button class="btn-ghost" @click="showDeleteConfirm = false">Batal</button>
        <button class="btn-danger" :disabled="isDeleting" @click="confirmDelete">
          {{ isDeleting ? 'Menghapus…' : 'Ya, hapus' }}
        </button>
      </div>
    </BaseModal>
  </DashboardLayout>
</template>
