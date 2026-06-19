<script setup>
import Sidebar from './Sidebar.vue'
import Topbar from './Topbar.vue'

defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-paper-dim">
    <Sidebar />
    <div class="flex flex-1 flex-col overflow-hidden">
      <Topbar :title="title" :subtitle="subtitle">
        <template #actions>
          <slot name="actions" />
        </template>
      </Topbar>
      <main class="flex-1 overflow-y-auto px-8 py-6">
        <slot />
      </main>
    </div>
  </div>
</template>
