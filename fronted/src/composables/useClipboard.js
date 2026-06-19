import { ref } from 'vue'

export function useClipboard() {
  const copied = ref(false)

  async function copy(text) {
    try {
      await navigator.clipboard.writeText(text)
      copied.value = true
      setTimeout(() => (copied.value = false), 1800)
      return true
    } catch (err) {
      console.error('Gagal menyalin ke clipboard', err)
      return false
    }
  }

  return { copied, copy }
}
