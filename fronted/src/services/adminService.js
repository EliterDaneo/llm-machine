// src/services/adminService.js
import api from './api' // sesuaikan nama file kalau beda

export const adminService = {
    fetchUsers({ search = '', page = 1, pageSize = 15 } = {}) {
        return api.get('/admin/users', {
            params: { search, page, page_size: pageSize },
        })
    },

    // ✅ FIX 3: forward seluruh payload termasuk 'plan'
    updateUserLimits(userId, payload) {
        // payload: { plan?, daily_analysis_limit?, daily_token_limit? }
        return api.patch(`/admin/users/${userId}/limits`, payload)
    },

    // ✅ FIX 2: tambah method updateUserRole
    updateUserRole(userId, payload) {
        // payload: { role: 'user' | 'admin' }
        return api.patch(`/admin/users/${userId}/role`, payload)
    },
}