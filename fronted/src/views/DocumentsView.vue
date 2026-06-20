<script setup>
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { useDocumentsStore } from '../stores/documents'
import DashboardLayout from '../components/layout/DashboardLayout.vue'
import UploadZone from '../components/dashboard/UploadZone.vue'
import DocumentList from '../components/dashboard/DocumentList.vue'

const docsStore = useDocumentsStore()
const search = ref('')
const showUpload = ref(false)
const isSearching = ref(false)

let debounceTimer = null

onMounted(() => {
  fetchDocs()
})

onBeforeUnmount(() => {
  clearTimeout(debounceTimer)
})

async function fetchDocs() {
  isSearching.value = true
  try {
    // PERBAIKAN: selalu reset ke page 1 tiap kali kata kunci berubah,
    // supaya nggak "nyangkut" di halaman lama saat hasil pencarian lebih sedikit
    // dari isi halaman sebelumnya. (Cek juga apakah fetchDocuments di store
    // benar2 meneruskan { page } ini ke query params.)
    await docsStore.fetchDocuments({ search: search.value.trim() || undefined, page: 1 })
  } catch {
    // error sudah ditangani di store kalau ada toast/log di sana
  } finally {
    isSearching.value = false
  }
}

// PERBAIKAN: live search dengan debounce 400ms — nggak perlu pencet Enter lagi
watch(search, () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchDocs, 400)
})

function clearSearch() {
  search.value = ''
  fetchDocs()
}
</script>

<template>
  <DashboardLayout title="Dokumen" subtitle="Kelola semua PDF yang pernah Anda unggah">
    <template #actions>
      <button class="btn-accent" @click="showUpload = !showUpload">
        {{ showUpload ? 'Tutup' : '+ Unggah PDF' }}
      </button>
    </template>

    <div class="space-y-6">
      <UploadZone v-if="showUpload" />

      <div class="flex items-center gap-3">
        <div class="relative max-w-sm flex-1">
          <input v-model="search" type="text" class="input-field w-full pr-8" placeholder="Cari nama dokumen…" />
          <button v-if="search" type="button"
            class="absolute right-2 top-1/2 -translate-y-1/2 text-ink/30 transition hover:text-ink/60"
            title="Hapus pencarian" @click="clearSearch">
            ✕
          </button>
        </div>
        <span v-if="isSearching" class="text-xs text-ink/40">Mencari…</span>
      </div>

      <DocumentList :documents="docsStore.documents"
        :empty-hint="search ? `Tidak ada dokumen yang cocok dengan &quot;${search}&quot;.` : 'Belum ada dokumen yang diunggah.'" />
    </div>
  </DashboardLayout>
</template>