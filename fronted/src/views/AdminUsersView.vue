<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import DashboardLayout from '../components/layout/DashboardLayout.vue'
import Badge from '../components/ui/Badge.vue'
import ProgressBar from '../components/ui/ProgressBar.vue'
import EditUserLimitModal from '../components/admin/EditUserLimitModal.vue'
import UserRoleModal from '../components/admin/UserRoleModal.vue' // Tambahkan import ini
import { useAdminStore } from '../stores/admin'
import { PLAN_LIMITS, DEFAULT_DAILY_ANALYSIS_LIMIT, DEFAULT_DAILY_TOKEN_LIMIT } from '../utils/constants'

const admin = useAdminStore()

// ─── Search dengan debounce ─────────────────────────────────────────────────
const searchInput = ref('')
let debounceTimer = null
watch(searchInput, (val) => {
    clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => admin.setSearch(val), 400)
})

// ─── State Modal ────────────────────────────────────────────────────────────
const selectedUser = ref(null) // Digunakan bersama untuk kedua modal

// Modal Limit
const modalOpen = ref(false)
function openEdit(user) {
    selectedUser.value = user
    modalOpen.value = true
}

// Modal Role
const roleModalOpen = ref(false)
function openRoleEdit(user) {
    selectedUser.value = user
    roleModalOpen.value = true
}

// ─── Polling lifecycle ───────────────────────────────────────────────────────
onMounted(() => admin.startPolling())
onUnmounted(() => admin.stopPolling())

// ─── Helpers ────────────────────────────────────────────────────────────────
function formatNumber(n) {
    if (n === null || n === undefined || n === Infinity) return '∞'
    return Number(n).toLocaleString('id-ID')
}

function pct(used, limit) {
    if (!limit || limit === Infinity) return 0
    return Math.min(100, Math.round((used / limit) * 100))
}

/**
 * Resolusi limit:
 * 1. Override di user object (dari quota backend)
 * 2. Default dari PLAN_LIMITS[user.plan]
 * 3. Fallback global DEFAULT_*
 */
function resolveLimit(user, overrideKey, planKey) {
    const override = user[overrideKey]
    if (override !== null && override !== undefined) return override
    const plan = PLAN_LIMITS?.[user.plan]
    if (plan?.[planKey] !== undefined) return plan[planKey]
    return planKey === 'dailyAnalysisLimit' ? DEFAULT_DAILY_ANALYSIS_LIMIT : DEFAULT_DAILY_TOKEN_LIMIT
}

// Ambil data quota dari nested object kalau backend return { quota: { ... } }
function getQuotaField(user, field, fallback = 0) {
    return user?.quota?.[field] ?? user?.[field] ?? fallback
}

function analysisUsed(user) { return getQuotaField(user, 'daily_used') }
function analysisLimit(user) {
    // return getQuotaField(user, 'daily_limit') || resolveLimit(user, 'daily_analysis_limit', 'dailyAnalysisLimit') 
    return getQuotaField(user, 'daily_limit') || resolveLimit(user, 'daily_limit', 'dailyAnalysisLimit')
}
function tokenUsed(user) { return getQuotaField(user, 'total_tokens_used') }
function tokenLimit(user) {
    // return resolveLimit(user, 'daily_token_limit', 'dailyTokenLimit') 
    return getQuotaField(user, 'daily_token_limit') || resolveLimit(user, 'daily_token_limit', 'dailyTokenLimit')
}

function isAnalysisExhausted(user) { return analysisUsed(user) >= analysisLimit(user) }
function isTokenExhausted(user) { return tokenUsed(user) >= tokenLimit(user) }

function quotaStatus(user) {
    if (isAnalysisExhausted(user) && isTokenExhausted(user)) return 'exhausted'
    if (isAnalysisExhausted(user)) return 'token-mode'  // lanjut pakai token
    return 'ok'
}
</script>

<template>
    <DashboardLayout title="Manajemen Pengguna" subtitle="Kontrol limit analisis & token harian semua pengguna">
        <div class="space-y-4">

            <div class="flex items-center gap-3">
                <div class="relative max-w-sm flex-1">
                    <input v-model="searchInput" type="text" placeholder="Cari username atau email…"
                        class="w-full rounded-lg border border-ink/10 bg-paper px-3.5 py-2 pr-8 text-sm text-ink focus:border-highlight focus:outline-none" />
                    <button v-if="searchInput"
                        class="absolute right-2.5 top-1/2 -translate-y-1/2 text-ink/40 hover:text-ink"
                        @click="searchInput = ''">✕</button>
                </div>

                <button
                    class="flex items-center gap-1.5 rounded-lg border border-ink/10 px-3.5 py-2 text-sm font-medium text-ink/70 hover:bg-ink/5 disabled:opacity-40"
                    :disabled="admin.loading" @click="admin.refresh()">
                    <svg class="h-3.5 w-3.5 transition-transform" :class="{ 'animate-spin': admin.loading }"
                        viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                        <path
                            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                            stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                    Refresh
                </button>

                <span class="flex items-center gap-1.5 text-xs text-ink/40">
                    <span class="relative flex h-2 w-2">
                        <span
                            class="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75"></span>
                        <span class="relative inline-flex h-2 w-2 rounded-full bg-green-500"></span>
                    </span>
                    Live · setiap 15 detik
                </span>
            </div>

            <div class="overflow-x-auto rounded-xl border border-ink/8 bg-paper">
                <table class="w-full text-left text-sm">
                    <thead
                        class="border-b border-ink/8 bg-ink/[0.03] text-xs font-semibold uppercase tracking-wide text-ink/50">
                        <tr>
                            <th class="px-4 py-3">Pengguna</th>
                            <th class="px-4 py-3">Plan</th>
                            <th class="px-4 py-3">Analisis / Hari</th>
                            <th class="px-4 py-3">Token Terpakai</th>
                            <th class="px-4 py-3">Status</th>
                            <th class="px-4 py-3 text-right">Aksi</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-ink/5">
                        <tr v-if="admin.loading && !admin.users.length">
                            <td colspan="6" class="px-4 py-8 text-center text-ink/40">Memuat data…</td>
                        </tr>

                        <tr v-else-if="admin.error">
                            <td colspan="6" class="px-4 py-8 text-center text-red-500">{{ admin.error }}</td>
                        </tr>

                        <tr v-else-if="!admin.users.length">
                            <td colspan="6" class="px-4 py-8 text-center text-ink/40">Tidak ada pengguna ditemukan</td>
                        </tr>

                        <tr v-for="user in admin.users" :key="user.id" class="hover:bg-ink/[0.02]"
                            :class="{ 'opacity-50': !user.is_active }">
                            <td class="px-4 py-3">
                                <div class="flex items-center gap-2">
                                    <p class="font-medium text-ink">{{ user.username || '—' }}</p>
                                    <span v-if="user.role === 'admin'"
                                        class="rounded bg-highlight/10 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-highlight">
                                        Admin
                                    </span>
                                </div>
                                <p class="text-xs text-ink/45">{{ user.email }}</p>
                            </td>

                            <td class="px-4 py-3">
                                <Badge tone="highlight">{{ user.plan || 'free' }}</Badge>
                            </td>

                            <td class="px-4 py-3">
                                <div class="w-36">
                                    <p class="mb-1 text-xs text-ink/55">
                                        {{ formatNumber(analysisUsed(user)) }}
                                        /
                                        {{ formatNumber(analysisLimit(user)) }}
                                    </p>
                                    <ProgressBar :value="pct(analysisUsed(user), analysisLimit(user))"
                                        :tone="isAnalysisExhausted(user) ? 'danger' : 'highlight'" />
                                </div>
                            </td>

                            <td class="px-4 py-3">
                                <div class="w-36">
                                    <p class="mb-1 text-xs text-ink/55">
                                        {{ formatNumber(tokenUsed(user)) }}
                                        /
                                        {{ formatNumber(tokenLimit(user)) }}
                                    </p>
                                    <ProgressBar :value="pct(tokenUsed(user), tokenLimit(user))"
                                        :tone="isTokenExhausted(user) ? 'danger' : 'highlight'" />
                                </div>
                            </td>

                            <td class="px-4 py-3">
                                <span v-if="quotaStatus(user) === 'exhausted'"
                                    class="inline-flex items-center gap-1 rounded-full bg-red-50 px-2.5 py-0.5 text-xs font-semibold text-red-600">
                                    <span class="h-1.5 w-1.5 rounded-full bg-red-500"></span>
                                    Habis total
                                </span>
                                <span v-else-if="quotaStatus(user) === 'token-mode'"
                                    class="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-600">
                                    <span class="h-1.5 w-1.5 rounded-full bg-amber-400"></span>
                                    Mode token
                                </span>
                                <span v-else
                                    class="inline-flex items-center gap-1 rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-semibold text-green-600">
                                    <span class="h-1.5 w-1.5 rounded-full bg-green-500"></span>
                                    Normal
                                </span>
                            </td>

                            <td class="px-4 py-3 text-right">
                                <div class="flex items-center justify-end gap-2">
                                    <button
                                        class="rounded-lg border border-ink/10 px-3 py-1.5 text-xs font-semibold text-ink/70 hover:bg-ink/5"
                                        @click="openRoleEdit(user)">
                                        Ubah Role
                                    </button>
                                    <button
                                        class="rounded-lg border border-ink/10 px-3 py-1.5 text-xs font-semibold text-ink/70 hover:bg-ink/5"
                                        @click="openEdit(user)">
                                        Ubah Limit
                                    </button>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div v-if="admin.total > admin.pageSize" class="flex items-center justify-between text-sm text-ink/50">
                <p>Halaman {{ admin.page }} dari {{ admin.totalPages }} · {{ admin.total }} pengguna</p>
                <div class="flex gap-2">
                    <button class="rounded-lg border border-ink/10 px-3 py-1.5 disabled:opacity-40"
                        :disabled="admin.page <= 1" @click="admin.setPage(admin.page - 1)">← Sebelumnya</button>
                    <button class="rounded-lg border border-ink/10 px-3 py-1.5 disabled:opacity-40"
                        :disabled="admin.page >= admin.totalPages" @click="admin.setPage(admin.page + 1)">Selanjutnya
                        →</button>
                </div>
            </div>
        </div>

        <EditUserLimitModal :open="modalOpen" :user="selectedUser" @close="modalOpen = false"
            @saved="admin.fetchUsers()" />

        <UserRoleModal :open="roleModalOpen" :user="selectedUser" @close="roleModalOpen = false"
            @saved="admin.fetchUsers()" />

    </DashboardLayout>
</template>