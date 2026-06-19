import axios from 'axios'

const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api/v1'

const api = axios.create({
  baseURL,
  timeout: 60000,
})

// --- Token storage helpers -------------------------------------------------
const TOKEN_KEY = 'pdfi_access_token'
const REFRESH_KEY = 'pdfi_refresh_token'

export const tokenStorage = {
  getAccess: () => localStorage.getItem(TOKEN_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  set(access, refresh) {
    if (access) localStorage.setItem(TOKEN_KEY, access)
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
}

// --- Request interceptor: attach bearer token -------------------------------
api.interceptors.request.use((config) => {
  const token = tokenStorage.getAccess()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// --- Response interceptor: refresh access token on 401 once ----------------
let isRefreshing = false
let queue = []

function flushQueue(error, token = null) {
  queue.forEach(({ resolve, reject }) => {
    if (error) reject(error)
    else resolve(token)
  })
  queue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const status = error?.response?.status

    if (status !== 401 || originalRequest._retry || originalRequest.url?.includes('/auth/refresh')) {
      return Promise.reject(error)
    }

    const refreshToken = tokenStorage.getRefresh()
    if (!refreshToken) {
      tokenStorage.clear()
      return Promise.reject(error)
    }

    if (isRefreshing) {
      // Antri sampai refresh selesai, lalu ulangi request dengan token baru
      return new Promise((resolve, reject) => {
        queue.push({ resolve, reject })
      }).then((newToken) => {
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return api(originalRequest)
      })
    }

    originalRequest._retry = true
    isRefreshing = true

    try {
      const { data } = await axios.post(`${baseURL}/auth/refresh`, { refresh_token: refreshToken })
      const newAccess = data.access_token
      tokenStorage.set(newAccess, data.refresh_token || refreshToken)
      flushQueue(null, newAccess)
      originalRequest.headers.Authorization = `Bearer ${newAccess}`
      return api(originalRequest)
    } catch (refreshError) {
      flushQueue(refreshError, null)
      tokenStorage.clear()
      window.location.href = '/login'
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  }
)

export default api
