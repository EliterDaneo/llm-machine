<script setup>
import { ref } from 'vue'
import Sidebar from './Sidebar.vue'
import Topbar from './Topbar.vue'

defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})

const sidebarOpen = ref(false)
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-paper-dim">
    <!-- Backdrop, cuma aktif di mobile pas drawer kebuka -->
    <Transition name="fade">
      <div v-if="sidebarOpen" class="fixed inset-0 z-30 bg-ink/40 lg:hidden" @click="sidebarOpen = false" />
    </Transition>

    <Sidebar :open="sidebarOpen" @close="sidebarOpen = false" />

    <div class="flex flex-1 flex-col overflow-hidden">
      <Topbar :title="title" :subtitle="subtitle" @toggle-sidebar="sidebarOpen = !sidebarOpen">
        <template #actions>
          <slot name="actions" />
        </template>
      </Topbar>
      <main class="flex-1 overflow-y-auto px-4 py-5 sm:px-6 lg:px-8 lg:py-6">
        <slot />
      </main>
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