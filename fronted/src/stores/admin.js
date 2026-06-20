// src/stores/admin.js
import { defineStore } from 'pinia'
import { adminService } from '../services/adminService'

const POLL_INTERVAL_MS = 15_000

export const useAdminStore = defineStore('admin', {
    state: () => ({
        users: [],
        total: 0,
        page: 1,
        pageSize: 15,
        search: '',
        loading: false,
        saving: false,
        error: null,
        _pollTimer: null,
    }),

    getters: {
        totalPages: (state) => Math.max(1, Math.ceil(state.total / state.pageSize)),
    },

    actions: {
        async fetchUsers() {
            if (!this.loading) this.loading = this.users.length === 0
            this.error = null
            try {
                const { data } = await adminService.fetchUsers({
                    search: this.search,
                    page: this.page,
                    pageSize: this.pageSize,
                })
                this.users = data.items ?? data.data ?? data
                this.total = data.total ?? this.users.length
            } catch (err) {
                this.error =
                    err?.response?.data?.detail ??
                    err?.response?.data?.message ??
                    'Gagal memuat data pengguna'
            } finally {
                this.loading = false
            }
        },

        setSearch(value) {
            this.search = value
            this.page = 1
            this.fetchUsers()
        },

        setPage(page) {
            if (page < 1 || page > this.totalPages) return
            this.page = page
            this.fetchUsers()
        },

        // ✅ FIX 1 & 3: terima snake_case payload langsung, teruskan ke service apa adanya
        async updateUserLimits(userId, payload) {
            // payload = { plan, daily_analysis_limit, daily_token_limit }
            this.saving = true
            try {
                const { data } = await adminService.updateUserLimits(userId, payload)
                // Update in-place dengan data terbaru dari backend
                const idx = this.users.findIndex((u) => u.id === userId)
                if (idx !== -1) this.users[idx] = { ...this.users[idx], ...data }
                return data
            } catch (err) {
                throw err // biarkan modal yang handle error display
            } finally {
                this.saving = false
            }
        },

        // ✅ FIX 2: tambah action updateUserRole yang sebelumnya tidak ada
        async updateUserRole(userId, payload) {
            // payload = { role: 'user' | 'admin' }
            this.saving = true
            try {
                const { data } = await adminService.updateUserRole(userId, payload)
                // Update in-place
                const idx = this.users.findIndex((u) => u.id === userId)
                if (idx !== -1) this.users[idx] = { ...this.users[idx], ...data }
                return data
            } catch (err) {
                throw err
            } finally {
                this.saving = false
            }
        },

        startPolling() {
            this.stopPolling()
            this.fetchUsers()
            this._pollTimer = setInterval(() => {
                if (!this.saving) this.fetchUsers()
            }, POLL_INTERVAL_MS)
        },

        stopPolling() {
            if (this._pollTimer) {
                clearInterval(this._pollTimer)
                this._pollTimer = null
            }
        },

        async refresh() {
            this.loading = true
            await this.fetchUsers()
        },
    },
})