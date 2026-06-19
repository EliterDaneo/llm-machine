<script setup>
import { computed } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { PLAN_LIMITS } from '../../utils/constants'
import { formatBytes } from '../../utils/formatters'
import ProgressBar from '../ui/ProgressBar.vue'
import Badge from '../ui/Badge.vue'

const auth = useAuthStore()

const planKey = computed(() => auth.plan || 'free')
const planMeta = computed(() => PLAN_LIMITS[planKey.value])

const used = computed(() => auth.quota?.daily_used ?? 0)
const limit = computed(() => auth.quota?.daily_limit ?? planMeta.value.dailyAnalysisLimit)
const pct = computed(() => (limit.value === Infinity ? 0 : Math.round((used.value / limit.value) * 100)))

// PERBAIKAN: Baca key 'storage_used_mb' dari backend, lalu kalikan agar menjadi Bytes
const storageUsed = computed(() => {
  const mb = auth.quota?.storage_used_mb ?? 0
  return mb * 1024 * 1024 // Konversi MB ke Bytes untuk formatBytes()
})

const storageLimit = computed(() => planMeta.value.maxStorageMB * 1024 * 1024)
const storagePct = computed(() => {
  if (storageLimit.value === 0) return 0
  return Math.round((storageUsed.value / storageLimit.value) * 100)
})

const nearLimit = computed(() => pct.value >= 80)
</script>

<template>
  <div class="card p-5">
    <div class="mb-4 flex items-center justify-between">
      <h3 class="font-display text-base font-semibold text-ink">Kuota Paket {{ planMeta.label }}</h3>
      <Badge :tone="planKey === 'free' ? 'neutral' : 'stamp'">{{ planMeta.label }}</Badge>
    </div>

    <div class="space-y-4">
      <div>
        <div class="mb-1.5 flex items-center justify-between text-sm">
          <span class="text-ink/60">Analisis hari ini</span>
          <span class="font-mono font-medium text-ink">{{ used }} / {{ limit === Infinity ? '∞' : limit }}</span>
        </div>
        <ProgressBar :value="pct" :tone="nearLimit ? 'rubric' : 'highlight'" />
        <p v-if="nearLimit" class="mt-1.5 text-xs text-rubric">Kuota harian hampir habis.</p>
      </div>

      <div>
        <div class="mb-1.5 flex items-center justify-between text-sm">
          <span class="text-ink/60">Penyimpanan</span>
          <span class="font-mono font-medium text-ink">
            {{ formatBytes(storageUsed) }} / {{ planMeta.maxStorageMB >= 1024 ? `${planMeta.maxStorageMB / 1024} GB` :
              `${planMeta.maxStorageMB} MB` }}
          </span>
        </div>
        <ProgressBar :value="storagePct" tone="ink" />
      </div>

      <div class="grid grid-cols-2 gap-3 border-t border-ink/8 pt-4 text-sm">
        <div>
          <p class="text-ink/45">Maks. halaman / PDF</p>
          <p class="font-mono font-medium text-ink">{{ planMeta.maxPagesPerDocument === Infinity ? 'Tanpa batas' :
            planMeta.maxPagesPerDocument }}</p>
        </div>
        <div>
          <p class="text-ink/45">Maks. ukuran file</p>
          <p class="font-mono font-medium text-ink">{{ planMeta.maxFileSizeMB }} MB</p>
        </div>
      </div>
    </div>

    <router-link v-if="planKey === 'free'" :to="{ name: 'pricing' }" class="btn-accent mt-5 w-full">
      Upgrade ke Pro
    </router-link>
  </div>
</template>
