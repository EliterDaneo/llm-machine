import { defineStore } from 'pinia'
import { authApi } from '../services/authService'
import { tokenStorage } from '../services/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null, // { id, email, username, plan, quota: {...} }
    isLoading: false,
    isBootstrapped: false,
  }),

  getters: {
    isAuthenticated: (state) => !!state.user,
    plan: (state) => state.user?.plan || 'free',
    quota: (state) => state.user?.quota || null,
  },

  actions: {
    async register({ email, username, full_name, password }) {
      this.isLoading = true
      try {
        const { data } = await authApi.register({ email, username, full_name, password })
        return data
      } finally {
        this.isLoading = false
      }
    },

    async login({ email, password }) {
      this.isLoading = true
      try {
        const { data } = await authApi.login({ email, password })
        tokenStorage.set(data.access_token, data.refresh_token)
        await this.fetchMe()
        return data
      } finally {
        this.isLoading = false
      }
    },

    async fetchMe() {
      const { data } = await authApi.me()
      this.user = data
      return data
    },

    async bootstrap() {
      // Dipanggil sekali saat app load untuk cek apakah token tersimpan masih valid
      if (this.isBootstrapped) return
      const token = tokenStorage.getAccess()
      if (token) {
        try {
          await this.fetchMe()
        } catch (err) {
          tokenStorage.clear()
          this.user = null
        }
      }
      this.isBootstrapped = true
    },

    async updateProfile(payload) {
      const { data } = await authApi.updateMe(payload)
      this.user = { ...this.user, ...data }
      return data
    },

    async changePassword(payload) {
      return authApi.changePassword(payload)
    },

    async deactivateAccount() {
      await authApi.deactivate()
      this.logout()
    },

    logout() {
      tokenStorage.clear()
      this.user = null
    },
  },
})