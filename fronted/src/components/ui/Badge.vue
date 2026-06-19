<script setup>
defineProps({
  tone: { type: String, default: 'neutral' }, // neutral | highlight | stamp | rubric
})

const toneClasses = {
  neutral: 'bg-ink/8 text-ink',
  highlight: 'bg-highlight-soft text-ink',
  stamp: 'bg-stamp-soft text-stamp',
  rubric: 'bg-rubric-soft text-rubric',
}
</script>

<template>
  <span
    class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold"
    :class="toneClasses[tone] || toneClasses.neutral"
  >
    <slot />
  </span>
</template>
