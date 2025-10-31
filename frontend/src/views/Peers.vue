<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-3xl font-bold">Peer Management</h1>
      <button @click="showAddModal = true" class="btn btn-primary">
        Add New Peer
      </button>
    </div>

    <!-- Peers list -->
    <div v-if="loading" class="text-center py-8">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <div v-else-if="peers.length === 0" class="card bg-base-100 shadow-xl">
      <div class="card-body text-center">
        <p class="text-gray-500">No peers configured. Add your first peer to get started.</p>
      </div>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <PeerCard
        v-for="peer in peers"
        :key="peer.id"
        :peer="peer"
        @delete="deletePeer"
        @config="downloadConfig"
      />
    </div>

    <!-- Add peer modal -->
    <dialog :class="{ 'modal modal-open': showAddModal }" class="modal">
      <div class="modal-box w-11/12 max-w-2xl">
        <h3 class="font-bold text-lg mb-4">Add New Peer</h3>

        <form @submit.prevent="addPeer">
          <div class="form-control mb-4">
            <label class="label"><span class="label-text">Peer Name</span></label>
            <input v-model="newPeer.name" type="text" class="input input-bordered" required />
          </div>

          <div class="form-control mb-4">
            <label class="label"><span class="label-text">Public Key</span></label>
            <div class="join w-full">
              <input v-model="newPeer.public_key" type="text" class="input input-bordered join-item flex-1" required />
              <button type="button" @click="generateKeys" class="btn btn-primary join-item">Generate</button>
            </div>
            <label v-if="generatedKeys.private_key" class="label">
              <span class="label-text-alt text-success">Private key: {{ generatedKeys.private_key }}</span>
            </label>
          </div>

          <div class="form-control mb-4">
            <label class="label"><span class="label-text">Allowed IPs</span></label>
            <input v-model="newPeer.allowed_ips" type="text" class="input input-bordered" placeholder="10.0.0.2/32" required />
            <label class="label"><span class="label-text-alt">Comma-separated list of IP addresses/ranges</span></label>
          </div>

          <div class="form-control mb-6">
            <label class="label"><span class="label-text">Description (optional)</span></label>
            <textarea v-model="newPeer.description" class="textarea textarea-bordered"></textarea>
          </div>

          <div class="modal-action">
            <button type="button" @click="closeAddModal" class="btn">Cancel</button>
            <button type="submit" class="btn btn-primary" :disabled="submitting">
              {{ submitting ? 'Adding...' : 'Add Peer' }}
            </button>
          </div>
        </form>
      </div>
      <form method="dialog" class="modal-backdrop">
        <button @click="closeAddModal">close</button>
      </form>
    </dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'
import PeerCard from '../components/PeerCard.vue'

const peers = ref([])
const loading = ref(false)
const showAddModal = ref(false)
const submitting = ref(false)
const generatedKeys = ref({})
const newPeer = ref({
  name: '',
  public_key: '',
  allowed_ips: '',
  description: ''
})

const fetchPeers = async () => {
  loading.value = true
  try {
    const response = await api.listPeers()
    peers.value = response.data
  } catch (error) {
    console.error('Error fetching peers:', error)
    alert('Failed to fetch peers')
  } finally {
    loading.value = false
  }
}

const generateKeys = async () => {
  try {
    const response = await api.generateKeys()
    generatedKeys.value = response.data
    newPeer.value.public_key = response.data.public_key
  } catch (error) {
    console.error('Error generating keys:', error)
    alert('Failed to generate keys')
  }
}

const addPeer = async () => {
  submitting.value = true
  try {
    await api.createPeer(newPeer.value)
    closeAddModal()
    fetchPeers()
  } catch (error) {
    console.error('Error adding peer:', error)
    alert(error.response?.data?.error || 'Failed to add peer')
  } finally {
    submitting.value = false
  }
}

const deletePeer = async (publicKey) => {
  if (!confirm('Are you sure you want to delete this peer?')) return

  try {
    await api.deletePeer(publicKey)
    fetchPeers()
  } catch (error) {
    console.error('Error deleting peer:', error)
    alert('Failed to delete peer')
  }
}

const downloadConfig = async (peer) => {
  if (!generatedKeys.value.private_key) {
    alert('Please generate keys for this peer first')
    return
  }

  try {
    const response = await api.getPeerConfig(peer.public_key, generatedKeys.value.private_key)
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `${peer.name}.conf`)
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch (error) {
    console.error('Error downloading config:', error)
    alert('Failed to download config')
  }
}

const closeAddModal = () => {
  showAddModal.value = false
  newPeer.value = { name: '', public_key: '', allowed_ips: '', description: '' }
  generatedKeys.value = {}
}

onMounted(fetchPeers)
</script>
