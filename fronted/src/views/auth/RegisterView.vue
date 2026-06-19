<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useToast } from '../../composables/useToast'

const auth = useAuthStore()
const router = useRouter()
const toast = useToast()

const form = ref({ email: '', username: '', full_name: '', password: '', confirmPassword: '' })
const isSubmitting = ref(false)
const errorMsg = ref('')

async function onSubmit() {
  errorMsg.value = ''
  if (form.value.password !== form.value.confirmPassword) {
    errorMsg.value = 'Konfirmasi password tidak cocok.'
    return
  }
  isSubmitting.value = true
  try {
    await auth.register({
      email: form.value.email,
      username: form.value.username,
      full_name: form.value.full_name,
      password: form.value.password,
    })
    toast.success('Akun berhasil dibuat. Silakan masuk.')
    router.push({ name: 'login' })
  } catch (err) {
    errorMsg.value = err?.response?.data?.detail || 'Pendaftaran gagal. Coba periksa kembali data Anda.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-paper-dim px-6 py-12">
    <div class="card w-full max-w-md p-8">
      <div class="mb-1 flex items-center gap-2">
        <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-highlight text-base font-bold text-ink">📄
        </div>
        <span class="font-display text-lg font-semibold text-ink">PDF Intelligence</span>
      </div>
      <h2 class="mt-5 font-display text-2xl font-semibold text-ink">Buat akun baru</h2>
      <p class="mt-1 text-sm text-ink/50">Paket Free aktif otomatis setelah daftar.</p>

      <form class="mt-6 space-y-4" @submit.prevent="onSubmit">
        <div>
          <label class="mb-1.5 block text-sm font-medium text-ink/80">Username</label>
          <input v-model="form.username" type="text" required class="input-field" placeholder="username" />
        </div>
        <div>
          <label class="mb-1.5 block text-sm font-medium text-ink/80">Nama Lengkap</label>
          <input v-model="form.full_name" type="text" required class="input-field" placeholder="Nama Lengkap" />
        </div>
        <div>
          <label class="mb-1.5 block text-sm font-medium text-ink/80">Email</label>
          <input v-model="form.email" type="email" required class="input-field" placeholder="nama@email.com" />
        </div>
        <div>
          <label class="mb-1.5 block text-sm font-medium text-ink/80">Password</label>
          <input v-model="form.password" type="password" required minlength="8" class="input-field"
            placeholder="Minimal 8 karakter" />
        </div>
        <div>
          <label class="mb-1.5 block text-sm font-medium text-ink/80">Konfirmasi Password</label>
          <input v-model="form.confirmPassword" type="password" required class="input-field"
            placeholder="Ulangi password" />
        </div>

        <p v-if="errorMsg" class="rounded-lg bg-rubric-soft px-3 py-2 text-sm text-rubric">{{ errorMsg }}</p>

        <button type="submit" class="btn-accent w-full" :disabled="isSubmitting">
          {{ isSubmitting ? 'Memproses…' : 'Daftar' }}
        </button>
      </form>

      <p class="mt-6 text-center text-sm text-ink/50">
        Sudah punya akun?
        <router-link :to="{ name: 'login' }" class="font-semibold text-ink hover:underline">Masuk</router-link>
      </p>
    </div>
  </div>
</template>
