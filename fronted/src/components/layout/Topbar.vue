<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})
const emit = defineEmits(['toggle-sidebar'])

const router = useRouter()
const auth = useAuthStore()

const menuOpen = ref(false)
const menuRef = ref(null)

function toggleMenu() {
  menuOpen.value = !menuOpen.value
}
function closeMenu() {
  menuOpen.value = false
}
function handleClickOutside(e) {
  if (menuRef.value && !menuRef.value.contains(e.target)) closeMenu()
}

function goToProfile() {
  closeMenu()
  router.push({ name: 'profile' })
}
function logout() {
  closeMenu()
  auth.logout()
  router.push({ name: 'login' })
}

onMounted(() => document.addEventListener('click', handleClickOutside))
onBeforeUnmount(() => document.removeEventListener('click', handleClickOutside))
</script>

<template>
  <header
    class="flex items-center justify-between border-b border-ink/8 bg-paper/80 px-4 py-4 backdrop-blur sm:px-8 sm:py-5">
    <div class="flex min-w-0 items-center gap-3">
      <!-- Toggle sidebar, cuma muncul di mobile -->
      <button
        class="-ml-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-ink/60 hover:bg-ink/5 hover:text-ink lg:hidden"
        title="Buka menu" @click="emit('toggle-sidebar')">
        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 6h16M4 12h16M4 18h16" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>

      <div class="min-w-0">
        <h1 class="truncate font-display text-xl font-semibold text-ink sm:text-2xl">{{ title }}</h1>
        <p v-if="subtitle" class="mt-0.5 truncate text-xs text-ink/50 sm:text-sm">{{ subtitle }}</p>
      </div>
    </div>

    <div class="flex shrink-0 items-center gap-3">
      <slot name="actions" />

      <!-- Avatar + dropdown -->
      <div ref="menuRef" class="relative">
        <button
          class="flex h-9 w-9 items-center justify-center rounded-full bg-ink/10 text-sm font-semibold text-ink transition hover:ring-2 hover:ring-ink/15"
          @click="toggleMenu">
          {{ (auth.user?.username || auth.user?.email || '?').charAt(0).toUpperCase() }}
        </button>

        <Transition name="fade">
          <div v-if="menuOpen"
            class="absolute right-0 top-full z-50 mt-2 w-52 rounded-xl border border-ink/8 bg-paper py-1.5 shadow-lg">
            <div class="border-b border-ink/8 px-3.5 py-2.5">
              <p class="truncate text-sm font-medium text-ink">{{ auth.user?.username || auth.user?.email }}</p>
              <p v-if="auth.user?.email && auth.user?.username" class="truncate text-xs text-ink/45">
                {{ auth.user.email }}
              </p>
            </div>
            <button class="flex w-full items-center gap-2.5 px-3.5 py-2 text-left text-sm text-ink/70 hover:bg-ink/5"
              @click="goToProfile">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 11a4 4 0 100-8 4 4 0 000 8z" stroke-linecap="round"
                  stroke-linejoin="round" />
              </svg>
              Profil
            </button>
            <button class="flex w-full items-center gap-2.5 px-3.5 py-2 text-left text-sm text-red-500 hover:bg-red-50"
              @click="logout">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" stroke-linecap="round"
                  stroke-linejoin="round" />
              </svg>
              Keluar
            </button>
          </div>
        </Transition>
      </div>
    </div>
  </header>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>