import api from './api'

export const authApi = {
  register(payload) {
    // payload: { email, username, full_name, password }
    return api.post('/auth/register', payload)
  },
  login(payload) {
    // payload: { email, password } -> { access_token, refresh_token, token_type }
    return api.post('/auth/login', payload)
  },
  refresh(refreshToken) {
    return api.post('/auth/refresh', { refresh_token: refreshToken })
  },
  me() {
    return api.get('/auth/me')
  },
  updateMe(payload) {
    // payload: { full_name?, username? }
    return api.put('/auth/me', payload)
  },
  changePassword(payload) {
    // payload: { current_password, new_password }
    return api.put('/auth/me/password', payload)
  },
  deactivate() {
    return api.delete('/auth/me')
  },
}