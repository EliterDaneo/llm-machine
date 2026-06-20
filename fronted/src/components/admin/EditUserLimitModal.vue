<script setup>
import { ref, watch, computed } from 'vue'
import { useAdminStore } from '../../stores/admin'
import { useToast } from '../../composables/useToast'
import { PLAN_LIMITS, DEFAULT_DAILY_ANALYSIS_LIMIT, DEFAULT_DAILY_TOKEN_LIMIT } from '../../utils/constants'

const props = defineProps({
    open: { type: Boolean, default: false },
    user: { type: Object, default: null },
})
const emit = defineEmits(['close', 'saved'])

const admin = useAdminStore()
const toast = useToast()

const selectedPlan = ref('free')
const dailyAnalysisLimit = ref(null)
const dailyTokenLimit = ref(null)
const errorMsg = ref('')
const isSaving = ref(false)

// ✅ FIX: baca dari quota nested object sesuai shape response backend
function resolveLimit(user, quotaKey, planKey) {
    // 1. Cek di quota nested (shape backend baru)
    const fromQuota = user?.quota?.[quotaKey]
    if (fromQuota !== null && fromQuota !== undefined) return fromQuota
    // 2. Cek di root user object (fallback kalau shape beda)
    const fromRoot = user?.[quotaKey]
    if (fromRoot !== null && fromRoot !== undefined) return fromRoot
    // 3. Default dari PLAN_LIMITS
    const plan = PLAN_LIMITS[user?.plan]
    if (plan?.[planKey] !== undefined) return plan[planKey]
    // 4. Global fallback
    return planKey === 'dailyAnalysisLimit' ? DEFAULT_DAILY_ANALYSIS_LIMIT : DEFAULT_DAILY_TOKEN_LIMIT
}

watch(
    () => props.user,
    (u) => {
        if (!u) return
        selectedPlan.value = u.plan || 'free'
        // ✅ FIX: gunakan resolveLimit yang baca quota.daily_limit & quota.daily_token_limit
        dailyAnalysisLimit.value = resolveLimit(u, 'daily_limit', 'dailyAnalysisLimit')
        dailyTokenLimit.value = resolveLimit(u, 'daily_token_limit', 'dailyTokenLimit')
        errorMsg.value = ''
    },
    { immediate: true }
)

// Saat plan dropdown berubah, update input hanya kalau user memang belum punya override
watch(selectedPlan, (newPlan) => {
    if (!props.user) return
    const planConfig = PLAN_LIMITS[newPlan] || {}
    // Hanya auto-update kalau nilai sekarang persis sama dengan default plan lama
    // (artinya user belum kustom, jadi ikutin plan baru)
    const oldPlanConfig = PLAN_LIMITS[props.user.plan] || {}
    if (dailyAnalysisLimit.value === (oldPlanConfig.dailyAnalysisLimit ?? DEFAULT_DAILY_ANALYSIS_LIMIT)) {
        dailyAnalysisLimit.value = planConfig.dailyAnalysisLimit ?? DEFAULT_DAILY_ANALYSIS_LIMIT
    }
    if (dailyTokenLimit.value === (oldPlanConfig.dailyTokenLimit ?? DEFAULT_DAILY_TOKEN_LIMIT)) {
        dailyTokenLimit.value = planConfig.dailyTokenLimit ?? DEFAULT_DAILY_TOKEN_LIMIT
    }
})

function resetToDefault() {
    const cfg = PLAN_LIMITS[selectedPlan.value] || {}
    dailyAnalysisLimit.value = cfg.dailyAnalysisLimit ?? DEFAULT_DAILY_ANALYSIS_LIMIT
    dailyTokenLimit.value = cfg.dailyTokenLimit ?? DEFAULT_DAILY_TOKEN_LIMIT
}

const isDirty = computed(() => {
    if (!props.user) return false
    return (
        selectedPlan.value !== (props.user.plan || 'free') ||
        dailyAnalysisLimit.value !== resolveLimit(props.user, 'daily_limit', 'dailyAnalysisLimit') ||
        dailyTokenLimit.value !== resolveLimit(props.user, 'daily_token_limit', 'dailyTokenLimit')
    )
})

async function handleSave() {
    if (!props.user) return
    if ((dailyAnalysisLimit.value ?? 0) < 0 || (dailyTokenLimit.value ?? 0) < 0) {
        errorMsg.value = 'Limit tidak boleh negatif'
        return
    }
    errorMsg.value = ''
    isSaving.value = true
    try {
        const updated = await admin.updateUserLimits(props.user.id, {
            plan: selectedPlan.value,
            daily_analysis_limit: dailyAnalysisLimit.value,
            daily_token_limit: dailyTokenLimit.value,
        })

        // ✅ Optimistic update — tempel response backend langsung ke array store
        // supaya tabel update seketika tanpa tunggu polling
        if (updated) {
            const target = admin.users.find(u => u.id === props.user.id)
            if (target) Object.assign(target, updated)
        }

        toast.success(`Plan & limit untuk ${props.user.username || props.user.email} berhasil diperbarui`)
        emit('saved')
        emit('close')
    } catch (err) {
        errorMsg.value =
            err?.response?.data?.detail ||
            err?.response?.data?.message ||
            'Gagal menyimpan perubahan'
    } finally {
        isSaving.value = false
    }
}
</script>

<template>
    <Transition name="fade">
        <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 px-4"
            @click.self="emit('close')">
            <div class="w-full max-w-sm rounded-2xl bg-paper p-5 shadow-xl">

                <div class="mb-4">
                    <h2 class="font-display text-lg font-semibold text-ink">Ubah Plan & Limit Pengguna</h2>
                    <p class="mt-0.5 truncate text-sm text-ink/50">{{ user?.username || user?.email }}</p>
                </div>

                <div class="space-y-4">
                    <div>
                        <label class="mb-1 block text-xs font-semibold uppercase tracking-wide text-ink/50">
                            Plan Pengguna
                        </label>
                        <select v-model="selectedPlan"
                            class="w-full rounded-lg border border-ink/10 px-3 py-2 text-sm text-ink focus:border-highlight focus:outline-none bg-white">
                            <option value="free">Free</option>
                            <option value="pro">Pro</option>
                            <option value="enterprise">Enterprise</option>
                        </select>
                    </div>

                    <div>
                        <label class="mb-1 block text-xs font-semibold uppercase tracking-wide text-ink/50">
                            Limit Analisis / Hari
                        </label>
                        <input v-model.number="dailyAnalysisLimit" type="number" min="0"
                            :placeholder="`Default: ${PLAN_LIMITS[selectedPlan]?.dailyAnalysisLimit ?? DEFAULT_DAILY_ANALYSIS_LIMIT}`"
                            class="w-full rounded-lg border border-ink/10 px-3 py-2 text-sm text-ink focus:border-highlight focus:outline-none" />
                    </div>

                    <div>
                        <label class="mb-1 block text-xs font-semibold uppercase tracking-wide text-ink/50">
                            Limit Token / Hari
                        </label>
                        <input v-model.number="dailyTokenLimit" type="number" min="0" step="1000"
                            :placeholder="`Default: ${PLAN_LIMITS[selectedPlan]?.dailyTokenLimit ?? DEFAULT_DAILY_TOKEN_LIMIT}`"
                            class="w-full rounded-lg border border-ink/10 px-3 py-2 text-sm text-ink focus:border-highlight focus:outline-none" />
                    </div>

                    <p v-if="errorMsg" class="text-xs font-medium text-red-500">{{ errorMsg }}</p>

                    <button type="button" class="text-xs font-semibold text-ink/50 hover:text-ink text-left block"
                        @click="resetToDefault">
                        ↺ Reset ke default plan ({{ selectedPlan }})
                    </button>
                </div>

                <div class="mt-5 flex justify-end gap-2">
                    <button class="rounded-lg px-3.5 py-2 text-sm font-medium text-ink/60 hover:bg-ink/5"
                        @click="emit('close')">
                        Batal
                    </button>
                    <button
                        class="rounded-lg bg-ink px-3.5 py-2 text-sm font-semibold text-paper hover:bg-ink/90 disabled:opacity-50"
                        :disabled="isSaving || !isDirty" @click="handleSave">
                        {{ isSaving ? 'Menyimpan…' : isDirty ? 'Simpan' : 'Tidak ada perubahan' }}
                    </button>
                </div>

            </div>
        </div>
    </Transition>
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