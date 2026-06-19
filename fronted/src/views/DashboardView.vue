<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useDocumentsStore } from '../stores/documents'
import DashboardLayout from '../components/layout/DashboardLayout.vue'
import OverviewStats from '../components/dashboard/OverviewStats.vue'
import QuotaIndicator from '../components/dashboard/QuotaIndicator.vue'
import UploadZone from '../components/dashboard/UploadZone.vue'
import DocumentList from '../components/dashboard/DocumentList.vue'

const auth = useAuthStore()
const docsStore = useDocumentsStore()

onMounted(async () => {
  try {
    await Promise.all([docsStore.fetchStats(), docsStore.fetchDocuments({ page_size: 5 })])
  } catch (err) {
    // Backend mungkin belum jalan — biarkan halaman tetap tampil dengan state kosong
    console.warn('Gagal memuat data dashboard', err)
  }
})
</script>

<template>
  <DashboardLayout title="Dashboard" :subtitle="`Selamat datang kembali, ${auth.user?.username || ''}`">
    <div class="space-y-6">
      <OverviewStats :stats="docsStore.stats" />

      <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div class="lg:col-span-2">
          <UploadZone />
        </div>
        <QuotaIndicator />
      </div>

      <div>
        <div class="mb-3 flex items-center justify-between">
          <h2 class="font-display text-lg font-semibold text-ink">Dokumen Terbaru</h2>
          <router-link :to="{ name: 'documents' }" class="text-sm font-medium text-ink/55 hover:text-ink">
            Lihat semua →
          </router-link>
        </div>
        <DocumentList :documents="docsStore.documents" />
      </div>
    </div>
  </DashboardLayout>
</template>
