<script setup>
const props = defineProps({
  value: { type: Number, required: true }, // 0-100
  tone: { type: String, default: 'ink' }, // ink | highlight | rubric | stamp
})

const toneClasses = {
  ink: 'bg-ink',
  highlight: 'bg-highlight',
  rubric: 'bg-rubric',
  stamp: 'bg-stamp',
}
</script>

<template>
  <div class="h-2 w-full overflow-hidden rounded-full bg-ink/8">
    <div
      class="h-full rounded-full transition-all duration-500"
      :class="toneClasses[props.tone] || toneClasses.ink"
      :style="{ width: `${Math.min(100, Math.max(0, props.value))}%` }"
    />
  </div>
</template>
