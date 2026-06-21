<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useDocumentsStore } from '../../stores/documents'
import { useToast } from '../../composables/useToast'
import { formatBytes, formatRelativeTime } from '../../utils/formatters'
import { DOCUMENT_STATUS } from '../../utils/constants'
import Badge from '../ui/Badge.vue'
import BaseModal from '../ui/BaseModal.vue'

defineProps({
  documents: { type: Array, default: () => [] },
  emptyHint: { type: String, default: 'Belum ada dokumen yang diunggah.' },
})

const router = useRouter()
const docsStore = useDocumentsStore()
const toast = useToast()

const confirmTarget = ref(null)
const isDeleting = ref(false)

function statusMeta(status) {
  return DOCUMENT_STATUS[status] || DOCUMENT_STATUS.processing
}

function openDocument(doc) {
  // PERBAIKAN: Gunakan doc.uuid sebagai fallback jika doc.id undefined
  const documentId = doc.id || doc.uuid

  if (!documentId) {
    toast.error('ID Dokumen tidak ditemukan.')
    return
  }

  router.push({ name: 'analysis', params: { id: documentId } })
}

function askDelete(doc) {
  confirmTarget.value = doc
}

async function confirmDelete() {
  if (!confirmTarget.value) return
  isDeleting.value = true

  const documentId = confirmTarget.value.id || confirmTarget.value.uuid

  try {
    await docsStore.deleteDocument(documentId)
    toast.success(`"${confirmTarget.value.filename}" dihapus.`)
    confirmTarget.value = null
  } catch (err) {
    toast.error(err?.response?.data?.detail || 'Gagal menghapus dokumen.')
  } finally {
    isDeleting.value = false
  }
}

// TAMBAHAN: Fungsi untuk memformat tanggal ke zona waktu lokal (browser pengguna)
function formatLocalTime(dateString) {
  if (!dateString) return '-'

  // Memastikan string dibaca sebagai UTC jika belum ada timezone offset (opsional, tergantung API)
  // Date() secara otomatis menerjemahkan ISO UTC ("...Z") ke waktu lokal device pengguna.
  const date = new Date(dateString)

  return new Intl.DateTimeFormat('id-ID', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZoneName: 'short' // Akan menampilkan WIB/WITA/WIT secara otomatis
  }).format(date)
}
</script>

<template>
  <div class="card overflow-hidden">
    <div class="overflow-x-auto">
      <table class="min-w-[800px] w-full text-left text-sm">
        <thead class="border-b border-ink/8 bg-paper-dim/60 text-xs uppercase tracking-wide text-ink/45">
          <tr>
            <th class="px-5 py-3 font-semibold">Dokumen</th>
            <th class="px-5 py-3 font-semibold">Halaman</th>
            <th class="px-5 py-3 font-semibold">Ukuran</th>
            <th class="px-5 py-3 font-semibold">Status</th>
            <th class="px-5 py-3 font-semibold">Diunggah</th>
            <th class="px-5 py-3 font-semibold text-right">Aksi</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="doc in documents" :key="doc.id || doc.uuid"
            class="cursor-pointer border-b border-ink/6 transition last:border-0 hover:bg-paper-dim/50"
            @click="openDocument(doc)">
            <td class="px-5 py-3.5">
              <div class="flex items-center gap-2.5">
                <span class="text-base">📄</span>
                <span class="max-w-[260px] truncate font-medium text-ink">{{ doc.filename }}</span>
              </div>
            </td>
            <td class="px-5 py-3.5 font-mono text-ink/70">{{ doc.page_count ?? '-' }}</td>
            <td class="px-5 py-3.5 font-mono text-ink/70">{{ formatBytes(doc.file_size ?? doc.size) }}</td>
            <td class="px-5 py-3.5">
              <Badge :tone="doc.status === 'ready' ? 'stamp' : doc.status === 'failed' ? 'rubric' : 'highlight'">
                {{ statusMeta(doc.status).label }}
              </Badge>
            </td>

            <td class="px-5 py-3.5 text-ink/55">
              <div class="flex flex-col">
                <span :title="formatLocalTime(doc.created_at)">
                  {{ formatRelativeTime(doc.created_at) }}
                </span>
              </div>
            </td>

            <td class="px-5 py-3.5 text-right">
              <button class="rounded-lg px-2.5 py-1.5 text-ink/40 transition hover:bg-rubric-soft hover:text-rubric"
                title="Hapus dokumen" @click.stop="askDelete(doc)">
                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14z"
                    stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="!documents.length" class="px-5 py-12 text-center">
        <p class="text-sm text-ink/45">{{ emptyHint }}</p>
      </div>
    </div>
  </div>

  <BaseModal :model-value="!!confirmTarget" title="Hapus dokumen?" @update:model-value="confirmTarget = null">
    <p class="text-sm text-ink/60">
      Dokumen <span class="font-semibold text-ink">"{{ confirmTarget?.filename }}"</span> beserta riwayat analisis dan
      chat terkait akan dihapus. Tindakan ini tidak dapat dibatalkan.
    </p>
    <div class="mt-5 flex justify-end gap-2.5">
      <button class="btn-ghost" @click="confirmTarget = null">Batal</button>
      <button class="btn-danger" :disabled="isDeleting" @click="confirmDelete">
        {{ isDeleting ? 'Menghapus…' : 'Ya, hapus' }}
      </button>
    </div>
  </BaseModal>
</template>