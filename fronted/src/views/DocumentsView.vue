<script setup>
import { onMounted, ref } from 'vue'
import { useDocumentsStore } from '../stores/documents'
import DashboardLayout from '../components/layout/DashboardLayout.vue'
import UploadZone from '../components/dashboard/UploadZone.vue'
import DocumentList from '../components/dashboard/DocumentList.vue'

const docsStore = useDocumentsStore()
const search = ref('')
const showUpload = ref(false)

onMounted(() => {
  docsStore.fetchDocuments().catch(() => { })
})

function onSearch() {
  docsStore.fetchDocuments({ search: search.value || undefined }).catch(() => { })
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
        <input v-model="search" type="text" class="input-field max-w-sm" placeholder="Cari nama dokumen…"
          @keyup.enter="onSearch" />
        <button class="btn-ghost" @click="onSearch">Cari</button>
      </div>

      <DocumentList :documents="docsStore.documents" empty-hint="Tidak ada dokumen ditemukan." />
    </div>
  </DashboardLayout>
</template>
