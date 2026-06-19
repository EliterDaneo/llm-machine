<script setup>
import { ref, computed } from 'vue'
import { useDocumentsStore } from '../../stores/documents'
import { useToast } from '../../composables/useToast'
import { useClipboard } from '../../composables/useClipboard'
import { ANALYSIS_TYPES } from '../../utils/constants'
import { formatRelativeTime } from '../../utils/formatters'
import Badge from '../ui/Badge.vue'

const props = defineProps({
  documentId: { type: [String, Number], required: true },
})

const docsStore = useDocumentsStore()
const toast = useToast()
const { copied, copy } = useClipboard()

const activeType = ref('summary')
const customPrompt = ref('')
const activeAnalysisId = ref(null)

const analysesForType = computed(() =>
  docsStore.analyses.filter((a) => a.analysis_type === activeType.value)
)
const latestResult = computed(() => {
  if (activeAnalysisId.value) {
    return docsStore.analyses.find((a) => a.id === activeAnalysisId.value)
  }
  return analysesForType.value[0] || null
})

function selectType(type) {
  activeType.value = type
  activeAnalysisId.value = null
}

async function runAnalysis() {
  if (activeType.value === 'custom' && !customPrompt.value.trim()) {
    toast.warning('Tulis instruksi analisis kustom terlebih dahulu.')
    return
  }
  try {
    const payload = { document_id: props.documentId, analysis_type: activeType.value }
    if (activeType.value === 'custom') payload.custom_prompt = customPrompt.value.trim()
    const result = await docsStore.analyzeDocument(payload)
    activeAnalysisId.value = result?.id || null
    toast.success('Analisis selesai.')
  } catch (err) {
    toast.error(err?.response?.data?.detail || 'Gagal menjalankan analisis. Periksa kuota & koneksi backend.')
  }
}

async function copyResult() {
  const text = latestResult.value?.result ?? latestResult.value?.content
  if (!text) return
  const ok = await copy(text)
  if (ok) toast.success('Hasil analisis disalin ke clipboard.')
}
</script>

<template>
  <div class="card flex h-full flex-col">
    <!-- Tabs -->
    <div class="flex gap-1 overflow-x-auto border-b border-ink/8 px-4 pt-3">
      <button v-for="t in ANALYSIS_TYPES" :key="t.value"
        class="shrink-0 rounded-t-lg px-3.5 py-2.5 text-sm font-medium transition" :class="activeType === t.value
          ? 'border-b-2 border-highlight text-ink'
          : 'text-ink/45 hover:text-ink/70'
          " @click="selectType(t.value)">
        {{ t.label }}
      </button>
    </div>

    <div class="flex-1 overflow-y-auto p-5">
      <p class="mb-3 text-xs text-ink/45">{{ANALYSIS_TYPES.find((t) => t.value === activeType)?.description}}</p>

      <textarea v-if="activeType === 'custom'" v-model="customPrompt" rows="2" class="input-field mb-3 resize-none"
        placeholder="Contoh: Buatkan poin-poin aksi untuk tim marketing dari dokumen ini" />

      <div class="mb-4 flex items-center gap-2">
        <button class="btn-accent" :disabled="docsStore.isAnalyzing" @click="runAnalysis">
          {{ docsStore.isAnalyzing ? 'Menganalisis…' : 'Jalankan Analisis' }}
        </button>
        <button v-if="latestResult" class="btn-ghost" @click="copyResult">
          {{ copied ? 'Tersalin ✓' : 'Salin Hasil' }}
        </button>
      </div>

      <div v-if="latestResult" class="rounded-xl bg-paper-dim/70 p-4">
        <div class="mb-2 flex items-center justify-between">
          <Badge tone="neutral">{{ latestResult.provider || 'AI' }}</Badge>
          <span class="text-xs text-ink/40">{{ formatRelativeTime(latestResult.created_at) }}</span>
        </div>
        <p class="whitespace-pre-wrap text-sm leading-relaxed text-ink/85">{{ latestResult.result ??
          latestResult.content }}</p>
      </div>
      <div v-else class="rounded-xl border border-dashed border-ink/15 p-8 text-center">
        <p class="text-sm text-ink/40">Belum ada hasil untuk jenis analisis ini. Klik "Jalankan Analisis".</p>
      </div>

      <!-- Past results for this type -->
      <div v-if="analysesForType.length > 1" class="mt-5">
        <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-ink/40">Riwayat Analisis Ini</p>
        <div class="space-y-1.5">
          <button v-for="a in analysesForType" :key="a.id"
            class="flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-xs transition"
            :class="latestResult?.id === a.id ? 'bg-highlight-soft text-ink' : 'hover:bg-paper-dim text-ink/55'"
            @click="activeAnalysisId = a.id">
            <span class="truncate">{{ (a.result ?? a.content)?.slice(0, 60) }}…</span>
            <span class="shrink-0 pl-2 font-mono text-ink/35">{{ formatRelativeTime(a.created_at) }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
