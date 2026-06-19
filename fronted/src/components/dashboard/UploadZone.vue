<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { useDocumentsStore } from '../../stores/documents'
import { useToast } from '../../composables/useToast'
import { PLAN_LIMITS } from '../../utils/constants'
import ProgressBar from '../ui/ProgressBar.vue'

const auth = useAuthStore()
const docsStore = useDocumentsStore()
const toast = useToast()

const isDragging = ref(false)
const fileInput = ref(null)

const planKey = computed(() => auth.plan || 'free')
const planMeta = computed(() => PLAN_LIMITS[planKey.value])

const quotaUsed = computed(() => auth.quota?.daily_used ?? 0)
const quotaLimit = computed(() => auth.quota?.daily_limit ?? planMeta.value.dailyAnalysisLimit)
const quotaExceeded = computed(() => quotaLimit.value !== Infinity && quotaUsed.value >= quotaLimit.value)

function openPicker() {
  if (quotaExceeded.value) {
    toast.warning('Kuota analisis harian Anda sudah habis. Upgrade paket untuk melanjutkan.')
    return
  }
  fileInput.value?.click()
}

function onDrop(e) {
  isDragging.value = false
  const file = e.dataTransfer.files?.[0]
  if (file) handleFile(file)
}

function onPick(e) {
  const file = e.target.files?.[0]
  if (file) handleFile(file)
  e.target.value = ''
}

async function handleFile(file) {
  if (quotaExceeded.value) {
    toast.warning('Kuota analisis harian Anda sudah habis. Upgrade paket untuk melanjutkan.')
    return
  }
  if (file.type !== 'application/pdf') {
    toast.error('Hanya file PDF yang didukung.')
    return
  }
  const maxBytes = planMeta.value.maxFileSizeMB * 1024 * 1024
  if (file.size > maxBytes) {
    toast.error(`Ukuran file melebihi batas paket ${planMeta.value.label} (maks. ${planMeta.value.maxFileSizeMB} MB).`)
    return
  }

  try {
    const doc = await docsStore.uploadDocument(file)
    toast.success(`"${file.name}" berhasil diunggah dan sedang diproses.`)
    // Catatan: validasi jumlah halaman dilakukan di backend setelah ekstraksi PyMuPDF.
    // Jika backend mengembalikan page_count melebihi planMeta.maxPagesPerDocument,
    // tampilkan peringatan di sini berdasarkan respons doc.page_count bila tersedia.
    if (doc?.page_count && doc.page_count > planMeta.value.maxPagesPerDocument) {
      toast.warning(
        `Dokumen memiliki ${doc.page_count} halaman, melebihi batas paket ${planMeta.value.label} (${planMeta.value.maxPagesPerDocument} hal.). Sebagian fitur mungkin dibatasi.`
      )
    }
  } catch (err) {
    toast.error(err?.response?.data?.detail || 'Upload gagal. Periksa koneksi ke backend.')
  }
}
</script>

<template>
  <div
    class="card relative flex flex-col items-center justify-center border-2 border-dashed p-8 text-center transition"
    :class="isDragging ? 'border-highlight bg-highlight-soft' : 'border-ink/15 hover:border-ink/25'"
    @dragover.prevent="isDragging = true"
    @dragleave.prevent="isDragging = false"
    @drop.prevent="onDrop"
  >
    <input ref="fileInput" type="file" accept="application/pdf" class="hidden" @change="onPick" />

    <template v-if="docsStore.isUploading">
      <p class="font-display text-base font-semibold text-ink">Mengunggah dokumen…</p>
      <div class="mt-3 w-full max-w-xs">
        <ProgressBar :value="docsStore.uploadProgress" tone="highlight" />
      </div>
      <p class="mt-1.5 font-mono text-xs text-ink/50">{{ docsStore.uploadProgress }}%</p>
    </template>

    <template v-else>
      <div class="flex h-12 w-12 items-center justify-center rounded-full bg-highlight-soft text-xl">📄</div>
      <p class="mt-3 font-display text-base font-semibold text-ink">Seret PDF ke sini, atau</p>
      <button class="btn-accent mt-3" @click="openPicker">Pilih File PDF</button>
      <p class="mt-3 text-xs text-ink/45">
        Maks. {{ planMeta.maxFileSizeMB }} MB · Maks. {{ planMeta.maxPagesPerDocument === Infinity ? 'tanpa batas' : planMeta.maxPagesPerDocument }} halaman
        · Paket {{ planMeta.label }}
      </p>
      <p v-if="quotaExceeded" class="mt-2 text-xs font-medium text-rubric">
        Kuota analisis harian habis ({{ quotaUsed }}/{{ quotaLimit }}).
        <router-link :to="{ name: 'pricing' }" class="underline">Upgrade paket</router-link>
      </p>
    </template>
  </div>
</template>
