<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useToast } from '../../composables/useToast'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const toast = useToast()

const form = ref({ email: '', password: '' })
const isSubmitting = ref(false)
const errorMsg = ref('')

async function onSubmit() {
  errorMsg.value = ''
  isSubmitting.value = true
  try {
    await auth.login(form.value)
    toast.success('Berhasil masuk. Selamat datang kembali!')
    router.push(route.query.redirect || { name: 'dashboard' })
  } catch (err) {
    errorMsg.value = err?.response?.data?.detail || 'Email atau password salah.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen">
    <!-- Left: brand panel -->
    <div class="relative hidden w-1/2 flex-col justify-between bg-ink p-12 text-paper lg:flex">
      <div class="flex items-center gap-2">
        <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-highlight text-base font-bold text-ink">📄</div>
        <span class="font-display text-lg font-semibold">PDF Intelligence</span>
      </div>
      <div class="max-w-md">
        <h1 class="font-display text-4xl font-semibold leading-tight">
          Baca lebih sedikit,
          <span class="mark-highlight text-ink">pahami lebih cepat.</span>
        </h1>
        <p class="mt-4 text-sm leading-relaxed text-paper/60">
          Unggah dokumen PDF dan biarkan AI menandai poin penting, merangkum, serta menjawab pertanyaan Anda
          langsung dari isi dokumen.
        </p>
      </div>
      <p class="text-xs text-paper/40">© 2026 PDF Intelligence App — internal testing console</p>
    </div>

    <!-- Right: form -->
    <div class="flex w-full flex-col items-center justify-center bg-paper px-6 py-12 lg:w-1/2">
      <div class="w-full max-w-sm">
        <h2 class="font-display text-2xl font-semibold text-ink">Masuk ke akun Anda</h2>
        <p class="mt-1 text-sm text-ink/50">Gunakan kredensial yang terdaftar di backend.</p>

        <form class="mt-7 space-y-4" @submit.prevent="onSubmit">
          <div>
            <label class="mb-1.5 block text-sm font-medium text-ink/80">Email</label>
            <input v-model="form.email" type="email" required class="input-field" placeholder="nama@email.com" />
          </div>
          <div>
            <label class="mb-1.5 block text-sm font-medium text-ink/80">Password</label>
            <input v-model="form.password" type="password" required class="input-field" placeholder="••••••••" />
          </div>

          <p v-if="errorMsg" class="rounded-lg bg-rubric-soft px-3 py-2 text-sm text-rubric">{{ errorMsg }}</p>

          <button type="submit" class="btn-accent w-full" :disabled="isSubmitting">
            {{ isSubmitting ? 'Memproses…' : 'Masuk' }}
          </button>
        </form>

        <p class="mt-6 text-center text-sm text-ink/50">
          Belum punya akun?
          <router-link :to="{ name: 'register' }" class="font-semibold text-ink hover:underline">Daftar di sini</router-link>
        </p>
      </div>
    </div>
  </div>
</template>
