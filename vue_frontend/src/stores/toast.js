import { defineStore } from 'pinia'

let nextId = 1

export const useToastStore = defineStore('toast', {
  state: () => ({
    toasts: [] // { id, type: 'success'|'error'|'info', message, timeout }
  }),
  actions: {
    show(type, message, duration = 3000) {
      const id = nextId++
      const toast = { id, type, message }
      this.toasts.push(toast)
      if (duration > 0) {
        setTimeout(() => this.remove(id), duration)
      }
      return id
    },
    success(message, duration) { return this.show('success', message, duration) },
    error(message, duration) { return this.show('error', message, duration) },
    info(message, duration) { return this.show('info', message, duration) },
    remove(id) {
      this.toasts = this.toasts.filter(t => t.id !== id)
    }
  }
})
