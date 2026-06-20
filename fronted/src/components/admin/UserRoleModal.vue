<script setup>
import { ref, watch, computed } from 'vue'
import { useAdminStore } from '../../stores/admin'
import { useToast } from '../../composables/useToast'

const props = defineProps({
    open: { type: Boolean, default: false },
    user: { type: Object, default: null },
})
const emit = defineEmits(['close', 'saved'])

const admin = useAdminStore()
const toast = useToast()

const selectedRole = ref('user')
const errorMsg = ref('')
const isSaving = ref(false) // ← local saving state, tidak bergantung pada admin.saving

watch(
    () => props.user,
    (u) => {
        if (!u) return
        selectedRole.value = u.role || 'user'
        errorMsg.value = ''
    },
    { immediate: true }
)

// Deteksi apakah role berubah dari aslinya
const isDirty = computed(() => {
    return props.user && selectedRole.value !== (props.user.role || 'user')
})

async function handleSave() {
    if (!props.user) return
    if (!isDirty.value) {
        emit('close')
        return
    }

    errorMsg.value = ''
    isSaving.value = true

    try {
        await admin.updateUserRole(props.user.id, {
            role: selectedRole.value,
        })

        // Optimistic update — langsung ubah di array users tanpa nunggu refetch
        const target = admin.users.find(u => u.id === props.user.id)
        if (target) {
            target.role = selectedRole.value
        }

        toast.success(
            `Role untuk ${props.user.username || props.user.email} berhasil diperbarui menjadi ${selectedRole.value}`
        )
        emit('saved')
        emit('close')
    } catch (err) {
        errorMsg.value =
            err?.response?.data?.detail ||
            err?.response?.data?.message ||
            'Gagal mengubah role'
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
                    <h2 class="font-display text-lg font-semibold text-ink">Ubah Role Pengguna</h2>
                    <p class="mt-0.5 truncate text-sm text-ink/50">{{ user?.username || user?.email }}</p>
                </div>

                <div class="space-y-4">
                    <div>
                        <label class="mb-1 block text-xs font-semibold uppercase tracking-wide text-ink/50">
                            Role Akses
                        </label>
                        <select v-model="selectedRole"
                            class="w-full rounded-lg border border-ink/10 px-3 py-2 text-sm text-ink focus:border-highlight focus:outline-none bg-white">
                            <option value="user">User</option>
                            <option value="admin">Admin</option>
                        </select>
                        <p class="mt-1.5 text-xs text-ink/50">
                            <span v-if="selectedRole === 'admin'" class="text-orange-500 font-medium">
                                Peringatan: Admin memiliki akses penuh ke sistem!
                            </span>
                            <span v-else>Akses standar pengguna aplikasi.</span>
                        </p>
                    </div>

                    <p v-if="errorMsg" class="text-xs font-medium text-red-500">{{ errorMsg }}</p>
                </div>

                <div class="mt-5 flex justify-end gap-2">
                    <button class="rounded-lg px-3.5 py-2 text-sm font-medium text-ink/60 hover:bg-ink/5"
                        @click="emit('close')">
                        Batal
                    </button>
                    <button
                        class="rounded-lg bg-ink px-3.5 py-2 text-sm font-semibold text-paper hover:bg-ink/90 disabled:opacity-50"
                        :disabled="isSaving" @click="handleSave">
                        {{ isSaving ? 'Menyimpan…' : isDirty ? 'Simpan' : 'Tutup' }}
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