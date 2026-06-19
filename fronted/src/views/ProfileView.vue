<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useToast } from '../composables/useToast'
import DashboardLayout from '../components/layout/DashboardLayout.vue'
import BaseModal from '../components/ui/BaseModal.vue'

const auth = useAuthStore()
const router = useRouter()
const toast = useToast()

const profileForm = reactive({
  username: auth.user?.username || '',
})
const passwordForm = reactive({ current_password: '', new_password: '', confirm: '' })

const isSavingProfile = ref(false)
const isSavingPassword = ref(false)
const showDeactivateConfirm = ref(false)
const isDeactivating = ref(false)

async function saveProfile() {
  isSavingProfile.value = true
  try {
    await auth.updateProfile(profileForm)
    toast.success('Profil berhasil diperbarui.')
  } catch (err) {
    toast.error(err?.response?.data?.detail || 'Gagal memperbarui profil.')
  } finally {
    isSavingProfile.value = false
  }
}

async function savePassword() {
  if (passwordForm.new_password !== passwordForm.confirm) {
    toast.error('Konfirmasi password baru tidak cocok.')
    return
  }
  isSavingPassword.value = true
  try {
    await auth.changePassword({
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password,
    })
    toast.success('Password berhasil diganti.')
    passwordForm.current_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm = ''
  } catch (err) {
    toast.error(err?.response?.data?.detail || 'Gagal mengganti password.')
  } finally {
    isSavingPassword.value = false
  }
}

async function deactivate() {
  isDeactivating.value = true
  try {
    await auth.deactivateAccount()
    toast.success('Akun dinonaktifkan.')
    router.push({ name: 'login' })
  } catch (err) {
    toast.error('Gagal menonaktifkan akun.')
  } finally {
    isDeactivating.value = false
  }
}
</script>

<template>
  <DashboardLayout title="Profil" subtitle="Kelola informasi akun Anda">
    <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <div class="card p-6">
        <h3 class="font-display text-base font-semibold text-ink">Informasi Akun</h3>
        <form class="mt-4 space-y-4" @submit.prevent="saveProfile">
          <div>
            <label class="mb-1.5 block text-sm font-medium text-ink/80">Email</label>
            <input :value="auth.user?.email" type="email" disabled class="input-field bg-paper-dim text-ink/50" />
          </div>
          <div>
            <label class="mb-1.5 block text-sm font-medium text-ink/80">Username</label>
            <input v-model="profileForm.username" type="text" class="input-field" />
          </div>
          <button type="submit" class="btn-primary" :disabled="isSavingProfile">
            {{ isSavingProfile ? 'Menyimpan…' : 'Simpan Perubahan' }}
          </button>
        </form>
      </div>

      <div class="card p-6">
        <h3 class="font-display text-base font-semibold text-ink">Ganti Password</h3>
        <form class="mt-4 space-y-4" @submit.prevent="savePassword">
          <div>
            <label class="mb-1.5 block text-sm font-medium text-ink/80">Password Saat Ini</label>
            <input v-model="passwordForm.current_password" type="password" required class="input-field" />
          </div>
          <div>
            <label class="mb-1.5 block text-sm font-medium text-ink/80">Password Baru</label>
            <input v-model="passwordForm.new_password" type="password" required minlength="8" class="input-field" />
          </div>
          <div>
            <label class="mb-1.5 block text-sm font-medium text-ink/80">Konfirmasi Password Baru</label>
            <input v-model="passwordForm.confirm" type="password" required class="input-field" />
          </div>
          <button type="submit" class="btn-primary" :disabled="isSavingPassword">
            {{ isSavingPassword ? 'Menyimpan…' : 'Ganti Password' }}
          </button>
        </form>
      </div>
    </div>

    <div class="card mt-6 border border-rubric/20 p-6">
      <h3 class="font-display text-base font-semibold text-rubric">Zona Berbahaya</h3>
      <p class="mt-1 text-sm text-ink/55">Menonaktifkan akun akan mencabut akses Anda ke seluruh dokumen dan riwayat.
      </p>
      <button class="btn-danger mt-4" @click="showDeactivateConfirm = true">Nonaktifkan Akun</button>
    </div>

    <BaseModal v-model="showDeactivateConfirm" title="Nonaktifkan akun?">
      <p class="text-sm text-ink/60">Tindakan ini akan menonaktifkan akun Anda. Hubungi admin untuk mengaktifkan
        kembali.</p>
      <div class="mt-5 flex justify-end gap-2.5">
        <button class="btn-ghost" @click="showDeactivateConfirm = false">Batal</button>
        <button class="btn-danger" :disabled="isDeactivating" @click="deactivate">
          {{ isDeactivating ? 'Memproses…' : 'Ya, nonaktifkan' }}
        </button>
      </div>
    </BaseModal>
  </DashboardLayout>
</template>
