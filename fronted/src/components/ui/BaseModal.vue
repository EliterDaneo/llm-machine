<script setup>
defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

function close() {
  emit('update:modelValue', false)
}
</script>

<template>
  <transition name="fade">
    <div v-if="modelValue" class="fixed inset-0 z-40 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-ink/40 backdrop-blur-sm" @click="close" />
      <div class="card relative w-full max-w-md p-6">
        <div class="mb-4 flex items-start justify-between">
          <h3 class="font-display text-lg font-semibold text-ink">{{ title }}</h3>
          <button class="text-ink/40 hover:text-ink" @click="close">✕</button>
        </div>
        <slot />
      </div>
    </div>
  </transition>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
