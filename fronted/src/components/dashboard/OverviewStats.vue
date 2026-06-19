<script setup>
import { formatBytes } from '../../utils/formatters'

const props = defineProps({
  // Default diubah menjadi fungsi yang mereturn objek kosong untuk mencegah error
  stats: { type: Object, default: () => ({}) },
})
</script>

<template>
  <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">

    <div class="card p-5">
      <p class="text-xs font-semibold uppercase tracking-wide text-ink/45">Total Dokumen</p>
      <p class="mt-2 font-mono text-2xl font-semibold text-ink">
        {{ props.stats?.documents?.total ?? 0 }}
      </p>
    </div>

    <div class="card p-5">
      <p class="text-xs font-semibold uppercase tracking-wide text-ink/45">Analisis Hari Ini</p>
      <p class="mt-2 font-mono text-2xl font-semibold text-ink">
        {{ props.stats?.quota?.daily_used ?? 0 }}
      </p>
    </div>

    <div class="card p-5">
      <p class="text-xs font-semibold uppercase tracking-wide text-ink/45">Token Terpakai</p>
      <p class="mt-2 font-mono text-2xl font-semibold text-ink">
        {{ (props.stats?.quota?.total_tokens_used ?? 0).toLocaleString('id-ID') }}
      </p>
    </div>

    <div class="card p-5">
      <p class="text-xs font-semibold uppercase tracking-wide text-ink/45">Penyimpanan Terpakai</p>
      <p class="mt-2 font-mono text-2xl font-semibold text-ink">
        {{ formatBytes((props.stats?.quota?.storage_used_mb ?? 0) * 1024 * 1024) }}
      </p>
    </div>

  </div>
</template>