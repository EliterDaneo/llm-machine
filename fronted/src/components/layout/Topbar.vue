<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})
</script>

<template>
  <header class="flex items-center justify-between border-b border-ink/8 bg-paper/80 px-8 py-5 backdrop-blur">
    <div>
      <h1 class="font-display text-2xl font-semibold text-ink">{{ title }}</h1>
      <p v-if="subtitle" class="mt-0.5 text-sm text-ink/50">{{ subtitle }}</p>
    </div>
    <div class="flex items-center gap-3">
      <slot name="actions" />
    </div>
  </header>
</template>
