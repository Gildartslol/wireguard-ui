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
    // Don't auto-redirect on 401 - let router handle it
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

  getPeer(peerId) {
    return api.get(`/peers/${peerId}`)
  },

  updatePeer(peerId, peerData) {
    return api.put(`/peers/${peerId}`, peerData)
  },

  deletePeer(peerId) {
    return api.delete(`/peers/${peerId}`)
  },

  generateKeys() {
    return api.post('/peers/generate-keys')
  },

  getPeerConfig(peerId, privateKey) {
    return api.get(`/peers/${peerId}/config`, {
      params: { private_key: privateKey },
      responseType: 'blob'
    })
  },

  // Client endpoints
  listClients() {
    return api.get('/clients')
  },

  createClient(clientData) {
    return api.post('/clients', clientData)
  },

  getClient(clientId) {
    return api.get(`/clients/${clientId}`)
  },

  updateClient(clientId, clientData) {
    return api.put(`/clients/${clientId}`, clientData)
  },

  deleteClient(clientId) {
    return api.delete(`/clients/${clientId}`)
  }
}
