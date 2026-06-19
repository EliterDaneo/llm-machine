<script setup>
import { computed } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useToast } from '../composables/useToast'
import { PLAN_LIMITS } from '../utils/constants'
import DashboardLayout from '../components/layout/DashboardLayout.vue'
import PricingCard from '../components/pricing/PricingCard.vue'

const auth = useAuthStore()
const toast = useToast()

const currentPlan = computed(() => auth.plan || 'free')

function onSelect(planKey) {
  if (planKey === 'enterprise') {
    toast.info('Hubungi tim kami untuk paket Enterprise.')
    return
  }
  // TODO: integrasikan dengan gateway pembayaran (mis. Midtrans/Xendit) lalu panggil
  // endpoint backend untuk mengubah `plan` user setelah pembayaran berhasil.
  toast.info(`Integrasi pembayaran untuk paket "${PLAN_LIMITS[planKey].label}" belum terhubung ke backend.`)
}
</script>

<template>
  <DashboardLayout title="Paket & Kuota" subtitle="Pilih paket sesuai kebutuhan analisis dokumen Anda">
    <div class="mb-6 rounded-xl border border-highlight/40 bg-highlight-soft px-4 py-3 text-sm text-ink/70">
      Paket menentukan jumlah analisis harian, batas halaman per PDF, dan ukuran file maksimum. Anda berada di paket
      <span class="font-semibold">{{ PLAN_LIMITS[currentPlan].label }}</span> saat ini.
    </div>

    <div class="grid grid-cols-1 gap-6 md:grid-cols-3">
      <PricingCard v-for="(meta, key) in PLAN_LIMITS" :key="key" :plan-key="key" :meta="meta"
        :is-current="currentPlan === key" :highlighted="key === 'pro'" @select="onSelect" />
    </div>
  </DashboardLayout>
</template>
