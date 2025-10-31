<template>
  <div>
    <h1 class="text-3xl font-bold mb-6">Dashboard</h1>

    <!-- Stats cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
      <div class="stats shadow">
        <div class="stat">
          <div class="stat-title">Total Peers</div>
          <div class="stat-value text-primary">{{ stats.total_peers || 0 }}</div>
        </div>
      </div>

      <div class="stats shadow">
        <div class="stat">
          <div class="stat-title">Connected</div>
          <div class="stat-value text-success">{{ stats.connected_peers || 0 }}</div>
        </div>
      </div>

      <div class="stats shadow">
        <div class="stat">
          <div class="stat-title">Disconnected</div>
          <div class="stat-value text-error">{{ stats.disconnected_peers || 0 }}</div>
        </div>
      </div>

      <div class="stats shadow">
        <div class="stat">
          <div class="stat-title">Total Transfer</div>
          <div class="stat-value text-sm">{{ formatBytes(stats.total_transfer || 0) }}</div>
        </div>
      </div>
    </div>

    <!-- Active peers table -->
    <div class="card bg-base-100 shadow-xl">
      <div class="card-body">
        <div class="flex justify-between items-center mb-4">
          <h2 class="card-title">Active Connections</h2>
          <button @click="refreshPeers" class="btn btn-sm btn-primary" :class="{ 'loading': loading }">
            {{ loading ? 'Refreshing...' : 'Refresh' }}
          </button>
        </div>

        <div v-if="loading && peers.length === 0" class="text-center py-8">
          <span class="loading loading-spinner loading-lg"></span>
        </div>

        <div v-else-if="peers.length === 0" class="text-center py-8 text-gray-500">
          No active peers
        </div>

        <div v-else class="overflow-x-auto">
          <table class="table table-zebra">
            <thead>
              <tr>
                <th>Status</th>
                <th>Name</th>
                <th>Endpoint</th>
                <th>Last Handshake</th>
                <th>RX / TX</th>
                <th>Allowed IPs</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="peer in peers" :key="peer.public_key">
                <td>
                  <div class="badge" :class="peer.connected ? 'badge-success' : 'badge-error'">
                    {{ peer.connected ? 'Connected' : 'Disconnected' }}
                  </div>
                </td>
                <td>
                  <div class="font-bold">{{ peer.name }}</div>
                  <div class="text-sm opacity-50">{{ peer.public_key.substring(0, 16) }}...</div>
                </td>
                <td>{{ peer.endpoint || 'N/A' }}</td>
                <td>{{ formatTime(peer.latest_handshake) }}</td>
                <td>
                  <div class="text-sm">
                    <div>↓ {{ formatBytes(peer.transfer_rx) }}</div>
                    <div>↑ {{ formatBytes(peer.transfer_tx) }}</div>
                  </div>
                </td>
                <td>
                  <div class="text-sm">
                    {{ peer.allowed_ips.join(', ') }}
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import api from '../services/api'

const stats = ref({})
const peers = ref([])
const loading = ref(false)
let refreshInterval = null

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const formatTime = (isoString) => {
  if (!isoString) return 'Never'
  const date = new Date(isoString)
  const now = new Date()
  const diff = Math.floor((now - date) / 1000)

  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

const fetchStats = async () => {
  try {
    const response = await api.getStats()
    stats.value = response.data
  } catch (error) {
    console.error('Error fetching stats:', error)
  }
}

const fetchPeers = async () => {
  try {
    const response = await api.getActivePeers()
    peers.value = response.data
  } catch (error) {
    console.error('Error fetching peers:', error)
  }
}

const refreshPeers = async () => {
  loading.value = true
  await Promise.all([fetchStats(), fetchPeers()])
  loading.value = false
}

onMounted(() => {
  refreshPeers()
  // Auto-refresh every 10 seconds
  refreshInterval = setInterval(refreshPeers, 10000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>
