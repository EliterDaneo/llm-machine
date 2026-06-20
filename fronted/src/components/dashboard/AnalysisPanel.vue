<script setup>
import { ref, computed } from 'vue'
import { useDocumentsStore } from '../../stores/documents'
import { useToast } from '../../composables/useToast'
import { useClipboard } from '../../composables/useClipboard'
import { ANALYSIS_TYPES, AI_ASSISTANT_NAME } from '../../utils/constants'
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

    <div class="min-h-0 flex-1 overflow-y-auto p-5">
      <p class="mb-3 text-xs text-ink/45">{{ANALYSIS_TYPES.find((t) => t.value === activeType)?.description}}</p>

      <textarea v-if="activeType === 'custom'" v-model="customPrompt" rows="2" class="input-field mb-3 resize-none"
        placeholder="Contoh: Buatkan poin-poin aksi untuk tim marketing dari dokumen ini" />

      <div class="mb-4 flex items-center gap-2">
        <button class="btn-accent inline-flex items-center gap-2" :disabled="docsStore.isAnalyzing"
          @click="runAnalysis">
          <svg v-if="docsStore.isAnalyzing" class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          {{ docsStore.isAnalyzing ? 'Menganalisis…' : 'Jalankan Analisis' }}
        </button>
        <button v-if="latestResult && !docsStore.isAnalyzing" class="btn-ghost" @click="copyResult">
          {{ copied ? 'Tersalin ✓' : 'Salin Hasil' }}
        </button>
      </div>

      <Transition name="fade" mode="out-in">
        <!-- Loading state -->
        <div v-if="docsStore.isAnalyzing" key="loading" class="rounded-xl bg-paper-dim/70 p-5">
          <div class="mb-3 flex items-center gap-1.5 text-sm text-ink/55">
            <span class="font-medium text-ink/75">{{ AI_ASSISTANT_NAME }}</span>
            <span>sedang menganalisis dokumen</span>
            <span class="ml-0.5 flex gap-1">
              <span class="h-1.5 w-1.5 animate-bounce rounded-full bg-ink/40" style="animation-delay: 0ms" />
              <span class="h-1.5 w-1.5 animate-bounce rounded-full bg-ink/40" style="animation-delay: 150ms" />
              <span class="h-1.5 w-1.5 animate-bounce rounded-full bg-ink/40" style="animation-delay: 300ms" />
            </span>
          </div>
          <div class="space-y-2">
            <div class="h-3 w-full animate-pulse rounded bg-ink/10" />
            <div class="h-3 w-5/6 animate-pulse rounded bg-ink/10" />
            <div class="h-3 w-4/6 animate-pulse rounded bg-ink/10" />
            <div class="h-3 w-3/6 animate-pulse rounded bg-ink/10" />
          </div>
        </div>

        <!-- Result -->
        <div v-else-if="latestResult" key="result" class="rounded-xl bg-paper-dim/70 p-4">
          <div class="mb-2 flex items-center justify-between">
            <Badge tone="neutral">{{ AI_ASSISTANT_NAME }}</Badge>
            <span class="text-xs text-ink/40">{{ formatRelativeTime(latestResult.created_at) }}</span>
          </div>
          <p class="whitespace-pre-wrap text-sm leading-relaxed text-ink/85">{{ latestResult.result ??
            latestResult.content }}</p>
        </div>

        <!-- Empty state -->
        <div v-else key="empty" class="rounded-xl border border-dashed border-ink/15 p-8 text-center">
          <p class="text-sm text-ink/40">Belum ada hasil untuk jenis analisis ini. Klik "Jalankan Analisis".</p>
        </div>
      </Transition>

      <!-- Riwayat analisis untuk tab ini, dalam bentuk tabel -->
      <div v-if="analysesForType.length > 1" class="mt-5">
        <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-ink/40">Riwayat Analisis Ini</p>
        <div class="overflow-hidden rounded-xl border border-ink/8">
          <table class="w-full text-left text-xs">
            <thead class="border-b border-ink/8 bg-paper-dim/60 uppercase tracking-wide text-ink/40">
              <tr>
                <th class="px-3 py-2 font-semibold">Cuplikan Hasil</th>
                <th class="px-3 py-2 font-semibold">Waktu</th>
                <th class="px-3 py-2 font-semibold text-right">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in analysesForType" :key="a.id"
                class="cursor-pointer border-b border-ink/6 transition last:border-0 hover:bg-paper-dim/50"
                :class="latestResult?.id === a.id ? 'bg-highlight-soft' : ''" @click="activeAnalysisId = a.id">
                <td class="max-w-[220px] truncate px-3 py-2 text-ink/70">
                  {{ (a.result ?? a.content)?.slice(0, 80) }}…
                </td>
                <td class="whitespace-nowrap px-3 py-2 text-ink/40">{{ formatRelativeTime(a.created_at) }}</td>
                <td class="px-3 py-2 text-right">
                  <span v-if="latestResult?.id === a.id" class="font-medium text-highlight">Aktif</span>
                  <span v-else class="text-ink/30">Lihat</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>