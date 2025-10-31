import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Redirect to login on unauthorized
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default {
  // Auth endpoints
  login(username, password) {
    return api.post('/auth/login', { username, password })
  },

  logout() {
    return api.post('/auth/logout')
  },

  checkAuth() {
    return api.get('/auth/check')
  },

  changePassword(oldPassword, newPassword) {
    return api.post('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword
    })
  },

  // Dashboard endpoints
  getStats() {
    return api.get('/dashboard/stats')
  },

  getActivePeers() {
    return api.get('/dashboard/peers')
  },

  getHistory(params = {}) {
    return api.get('/dashboard/history', { params })
  },

  getInterfaceInfo() {
    return api.get('/dashboard/interface')
  },

  // Peers endpoints
  listPeers() {
    return api.get('/peers')
  },

  createPeer(peerData) {
    return api.post('/peers', peerData)
  },

  getPeer(publicKey) {
    return api.get(`/peers/${publicKey}`)
  },

  updatePeer(publicKey, peerData) {
    return api.put(`/peers/${publicKey}`, peerData)
  },

  deletePeer(publicKey) {
    return api.delete(`/peers/${publicKey}`)
  },

  generateKeys() {
    return api.post('/peers/generate-keys')
  },

  getPeerConfig(publicKey, privateKey) {
    return api.get(`/peers/${publicKey}/config`, {
      params: { private_key: privateKey },
      responseType: 'blob'
    })
  }
}
