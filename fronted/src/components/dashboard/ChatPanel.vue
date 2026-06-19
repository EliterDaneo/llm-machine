<script setup>
import { ref, nextTick, watch } from 'vue'
import { useChatStore } from '../../stores/chat'
import { useToast } from '../../composables/useToast'
import { formatRelativeTime } from '../../utils/formatters'

const props = defineProps({
  documentId: { type: [String, Number], required: true },
})

const chatStore = useChatStore()
const toast = useToast()

const input = ref('')
const scrollEl = ref(null)

function scrollToBottom() {
  nextTick(() => {
    if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight
  })
}

watch(() => chatStore.messages.length, scrollToBottom)

async function send() {
  const text = input.value.trim()
  if (!text || chatStore.isSending) return
  input.value = ''
  try {
    await chatStore.sendMessage({ documentId: props.documentId, message: text })
  } catch (err) {
    toast.error(err?.response?.data?.detail || 'Gagal mengirim pesan. Periksa kuota chat harian Anda.')
  }
}

async function react(msg, feedback) {
  const next = msg.feedback === feedback ? null : feedback
  try {
    await chatStore.giveFeedback(msg.id, next)
  } catch (err) {
    toast.error('Gagal menyimpan feedback.')
  }
}
</script>

<template>
  <div class="card flex h-full flex-col">
    <div class="border-b border-ink/8 px-5 py-3.5">
      <h3 class="font-display text-base font-semibold text-ink">Chat dengan Dokumen</h3>
      <p class="text-xs text-ink/45">Tanyakan apa pun tentang isi dokumen ini.</p>
    </div>

    <div ref="scrollEl" class="flex-1 space-y-3 overflow-y-auto p-5">
      <div v-if="!chatStore.messages.length" class="flex h-full items-center justify-center text-center">
        <p class="max-w-[220px] text-sm text-ink/40">
          Mulai percakapan — misalnya "Apa kesimpulan utama dokumen ini?"
        </p>
      </div>

      <div v-for="msg in chatStore.messages" :key="msg.id" class="flex"
        :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
        <div class="max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed" :class="msg.role === 'user'
          ? 'rounded-br-sm bg-ink text-paper'
          : 'rounded-bl-sm bg-paper-dim text-ink/85'
          ">
          <p class="whitespace-pre-wrap">{{ msg.content }}</p>
          <div class="mt-1.5 flex items-center gap-2 text-[11px] opacity-50">
            <span>{{ formatRelativeTime(msg.created_at) }}</span>
          </div>
          <div v-if="msg.role === 'assistant'" class="mt-1.5 flex items-center gap-2">
            <button class="rounded px-1.5 py-0.5 text-xs transition"
              :class="msg.feedback === 'like' ? 'bg-stamp-soft text-stamp' : 'text-ink/30 hover:text-ink/60'"
              title="Suka" @click="react(msg, 'like')">
              👍
            </button>
            <button class="rounded px-1.5 py-0.5 text-xs transition"
              :class="msg.feedback === 'dislike' ? 'bg-rubric-soft text-rubric' : 'text-ink/30 hover:text-ink/60'"
              title="Tidak suka" @click="react(msg, 'dislike')">
              👎
            </button>
          </div>
        </div>
      </div>

      <div v-if="chatStore.isSending" class="flex justify-start">
        <div class="rounded-2xl rounded-bl-sm bg-paper-dim px-4 py-2.5 text-sm text-ink/40">Mengetik…</div>
      </div>
    </div>

    <form class="flex items-center gap-2 border-t border-ink/8 p-3.5" @submit.prevent="send">
      <input v-model="input" type="text" class="input-field flex-1" placeholder="Tulis pertanyaan tentang dokumen…" />
      <button type="submit" class="btn-accent" :disabled="!input.trim() || chatStore.isSending">Kirim</button>
    </form>
  </div>
</template>
