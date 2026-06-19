<script setup>
import { formatRupiah } from '../../utils/formatters'

const props = defineProps({
  planKey: { type: String, required: true },
  meta: { type: Object, required: true },
  isCurrent: { type: Boolean, default: false },
  highlighted: { type: Boolean, default: false },
})
defineEmits(['select'])
</script>

<template>
  <div
    class="card relative flex flex-col p-6"
    :class="highlighted ? 'border-2 border-highlight shadow-lg' : ''"
  >
    <span
      v-if="highlighted"
      class="absolute -top-3 left-6 rounded-full bg-highlight px-3 py-1 text-xs font-bold text-ink"
    >
      Paling populer
    </span>

    <h3 class="font-display text-xl font-semibold text-ink">{{ meta.label }}</h3>
    <p class="mt-2">
      <span class="font-mono text-3xl font-bold text-ink">{{ formatRupiah(meta.price) }}</span>
      <span v-if="meta.price" class="text-sm text-ink/45"> /bulan</span>
    </p>

    <ul class="mt-5 flex-1 space-y-2.5 text-sm text-ink/70">
      <li v-for="f in meta.features" :key="f" class="flex items-start gap-2">
        <span class="mt-0.5 text-stamp">✓</span>
        <span>{{ f }}</span>
      </li>
    </ul>

    <button
      class="mt-6 w-full"
      :class="isCurrent ? 'btn-ghost' : highlighted ? 'btn-accent' : 'btn-primary'"
      :disabled="isCurrent"
      @click="$emit('select', planKey)"
    >
      {{ isCurrent ? 'Paket Saat Ini' : meta.price === null ? 'Hubungi Kami' : 'Pilih Paket' }}
    </button>
  </div>
</template>
