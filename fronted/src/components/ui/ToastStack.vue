<script setup>
import { useToast } from '../../composables/useToast'

const { toasts, dismiss } = useToast()

const styles = {
  success: 'border-stamp/30 bg-stamp-soft text-stamp',
  error: 'border-rubric/30 bg-rubric-soft text-rubric',
  warning: 'border-highlight/40 bg-highlight-soft text-ink',
  info: 'border-ink/15 bg-white text-ink',
}
</script>

<template>
  <div class="pointer-events-none fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2">
    <transition-group name="toast">
      <div
        v-for="t in toasts"
        :key="t.id"
        class="pointer-events-auto flex items-start justify-between gap-3 rounded-xl border px-4 py-3 text-sm font-medium shadow-card"
        :class="styles[t.type] || styles.info"
      >
        <span>{{ t.message }}</span>
        <button class="shrink-0 text-xs opacity-60 hover:opacity-100" @click="dismiss(t.id)">✕</button>
      </div>
    </transition-group>
  </div>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.2s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(8px);
}
</style>
