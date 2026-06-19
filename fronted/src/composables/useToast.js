import { reactive } from 'vue'

const state = reactive({
  toasts: [],
})

let counter = 0

function push(message, type = 'info', timeout = 3500) {
  const id = ++counter
  state.toasts.push({ id, message, type })
  if (timeout) {
    setTimeout(() => dismiss(id), timeout)
  }
  return id
}

function dismiss(id) {
  const idx = state.toasts.findIndex((t) => t.id === id)
  if (idx !== -1) state.toasts.splice(idx, 1)
}

export function useToast() {
  return {
    toasts: state.toasts,
    success: (msg, timeout) => push(msg, 'success', timeout),
    error: (msg, timeout) => push(msg, 'error', timeout),
    info: (msg, timeout) => push(msg, 'info', timeout),
    warning: (msg, timeout) => push(msg, 'warning', timeout),
    dismiss,
  }
}
