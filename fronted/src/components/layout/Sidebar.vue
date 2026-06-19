<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { PLAN_LIMITS } from '../../utils/constants'
import ProgressBar from '../ui/ProgressBar.vue'
import Badge from '../ui/Badge.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const navItems = [
  { name: 'dashboard', label: 'Dashboard', icon: 'M3 12l2-2 7-7 7 7 2 2M5 10v9a1 1 0 001 1h3v-6h6v6h3a1 1 0 001-1v-9' },
  { name: 'documents', label: 'Dokumen', icon: 'M7 3h7l5 5v13a1 1 0 01-1 1H7a1 1 0 01-1-1V4a1 1 0 011-1zM14 3v5h5' },
  { name: 'chat-history', label: 'Riwayat Chat', icon: 'M21 11.5a8.38 8.38 0 01-9 8.4A8.5 8.5 0 113 11.5 8.38 8.38 0 0111.5 3a8.38 8.38 0 019.5 8.5z' },
  { name: 'pricing', label: 'Paket & Kuota', icon: 'M12 1v22M5 7h9a3 3 0 010 6H8a3 3 0 000 6h11' },
]

const planKey = computed(() => auth.plan || 'free')
const planMeta = computed(() => PLAN_LIMITS[planKey.value])

const quotaUsed = computed(() => auth.quota?.daily_used ?? 0)
const quotaLimit = computed(() => auth.quota?.daily_limit ?? planMeta.value.dailyAnalysisLimit)
const quotaPct = computed(() => {
  if (!quotaLimit.value || quotaLimit.value === Infinity) return 0
  return Math.round((quotaUsed.value / quotaLimit.value) * 100)
})

function isActive(name) {
  return route.name === name
}

function logout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <aside class="flex h-screen w-64 shrink-0 flex-col bg-ink text-paper">
    <div class="flex items-center gap-2 px-6 py-6">
      <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-highlight text-base font-bold text-ink">
        📄
      </div>
      <div>
        <p class="font-display text-base font-semibold leading-none">PDF Intelligence</p>
        <p class="mt-1 text-[11px] uppercase tracking-wide text-paper/40">Document AI Console</p>
      </div>
    </div>

    <nav class="flex-1 space-y-1 px-3">
      <router-link
        v-for="item in navItems"
        :key="item.name"
        :to="{ name: item.name }"
        class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition"
        :class="
          isActive(item.name)
            ? 'bg-paper/10 text-highlight'
            : 'text-paper/65 hover:bg-paper/5 hover:text-paper'
        "
      >
        <svg class="h-4.5 w-4.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path :d="item.icon" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        {{ item.label }}
      </router-link>
    </nav>

    <div class="mx-3 mb-3 rounded-xl bg-paper/5 p-3.5">
      <div class="mb-2 flex items-center justify-between">
        <span class="text-xs font-semibold uppercase tracking-wide text-paper/50">Kuota Harian</span>
        <Badge tone="highlight">{{ planMeta.label }}</Badge>
      </div>
      <ProgressBar :value="quotaPct" tone="highlight" />
      <p class="mt-1.5 text-xs text-paper/55">
        {{ quotaUsed }} / {{ quotaLimit === Infinity ? '∞' : quotaLimit }} analisis hari ini
      </p>
      <router-link
        :to="{ name: 'pricing' }"
        class="mt-2 block text-center text-xs font-semibold text-highlight hover:underline"
      >
        Upgrade paket →
      </router-link>
    </div>

    <div class="flex items-center gap-3 border-t border-paper/10 px-4 py-4">
      <div class="flex h-9 w-9 items-center justify-center rounded-full bg-paper/10 text-sm font-semibold">
        {{ (auth.user?.username || auth.user?.email || '?').charAt(0).toUpperCase() }}
      </div>
      <div class="min-w-0 flex-1">
        <p class="truncate text-sm font-medium">{{ auth.user?.username || auth.user?.email }}</p>
        <router-link :to="{ name: 'profile' }" class="text-xs text-paper/50 hover:text-paper">Profil</router-link>
      </div>
      <button title="Keluar" class="text-paper/50 hover:text-highlight" @click="logout">
        <svg class="h-4.5 w-4.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
    </div>
  </aside>
</template>
