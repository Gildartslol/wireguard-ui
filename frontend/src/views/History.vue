<template>
  <div>
    <h1 class="text-3xl font-bold mb-6">Connection History</h1>

    <!-- Filters -->
    <div class="card bg-base-100 shadow-xl mb-6">
      <div class="card-body">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="form-control">
            <label class="label"><span class="label-text">Time Range (hours)</span></label>
            <select v-model="filters.hours" class="select select-bordered" @change="fetchHistory">
              <option :value="1">Last Hour</option>
              <option :value="6">Last 6 Hours</option>
              <option :value="24">Last 24 Hours</option>
              <option :value="168">Last Week</option>
            </select>
          </div>

          <div class="form-control">
            <label class="label"><span class="label-text">Limit</span></label>
            <select v-model="filters.limit" class="select select-bordered" @change="fetchHistory">
              <option :value="50">50 records</option>
              <option :value="100">100 records</option>
              <option :value="200">200 records</option>
              <option :value="500">500 records</option>
            </select>
          </div>

          <div class="form-control">
            <label class="label"><span class="label-text">&nbsp;</span></label>
            <button @click="fetchHistory" class="btn btn-primary" :class="{ 'loading': loading }">
              Refresh
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- History table -->
    <div class="card bg-base-100 shadow-xl">
      <div class="card-body">
        <div v-if="loading" class="text-center py-8">
          <span class="loading loading-spinner loading-lg"></span>
        </div>

        <div v-else-if="history.length === 0" class="text-center py-8 text-gray-500">
          No connection history found
        </div>

        <div v-else class="overflow-x-auto">
          <table class="table table-zebra">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Public Key</th>
                <th>Status</th>
                <th>Endpoint</th>
                <th>Last Handshake</th>
                <th>Transfer RX / TX</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="record in history" :key="record.id">
                <td>{{ formatDateTime(record.recorded_at) }}</td>
                <td>
                  <span class="font-mono text-sm">{{ record.public_key.substring(0, 16) }}...</span>
                </td>
                <td>
                  <div class="badge" :class="record.status === 'connected' ? 'badge-success' : 'badge-error'">
                    {{ record.status }}
                  </div>
                </td>
                <td>{{ record.endpoint || 'N/A' }}</td>
                <td>{{ formatDateTime(record.latest_handshake) }}</td>
                <td>
                  <div class="text-sm">
                    {{ formatBytes(record.transfer_rx) }} / {{ formatBytes(record.transfer_tx) }}
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
import { ref, onMounted } from 'vue'
import api from '../services/api'

const history = ref([])
const loading = ref(false)
const filters = ref({
  hours: 24,
  limit: 100
})

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const formatDateTime = (isoString) => {
  if (!isoString) return 'N/A'
  return new Date(isoString).toLocaleString()
}

const fetchHistory = async () => {
  loading.value = true
  try {
    const response = await api.getHistory(filters.value)
    history.value = response.data
  } catch (error) {
    console.error('Error fetching history:', error)
  } finally {
    loading.value = false
  }
}

onMounted(fetchHistory)
</script>
