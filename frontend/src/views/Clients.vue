<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-3xl font-bold">Client Management</h1>
      <button @click="showAddModal = true" class="btn btn-primary">
        Add New Client
      </button>
    </div>

    <!-- Clients list -->
    <div v-if="loading" class="text-center py-8">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <div v-else-if="clients.length === 0" class="card bg-base-100 shadow-xl">
      <div class="card-body text-center">
        <p class="text-gray-500">No clients configured. Add your first client to get started.</p>
      </div>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <!-- Client cards -->
      <div v-for="client in clients" :key="client.id" class="card bg-base-100 shadow-xl">
        <div class="card-body">
          <!-- Editable Name -->
          <div v-if="!editingClient[client.id]" class="flex items-center justify-between">
            <h2 class="card-title">{{ client.name }}</h2>
            <button
              v-if="!client.is_system"
              @click="startEdit(client)"
              class="btn btn-xs btn-ghost"
              title="Edit client"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
            </button>
          </div>

          <!-- Edit Form -->
          <div v-else class="space-y-3">
            <div>
              <label class="label label-text text-xs">Name</label>
              <input
                v-model="editForm.name"
                type="text"
                class="input input-bordered input-sm w-full"
                :disabled="client.is_system"
                placeholder="Client name"
              />
            </div>
            <div>
              <label class="label label-text text-xs">Subnet Range</label>
              <input
                v-model="editForm.subnet_range"
                type="text"
                class="input input-bordered input-sm w-full"
                placeholder="10.200.0.0/24"
              />
            </div>
            <div>
              <label class="label label-text text-xs">Location</label>
              <input
                v-model="editForm.location"
                type="text"
                class="input input-bordered input-sm w-full"
                placeholder="City, State"
              />
            </div>
            <div>
              <label class="label label-text text-xs">Description</label>
              <textarea
                v-model="editForm.description"
                class="textarea textarea-bordered textarea-sm w-full"
                rows="2"
                placeholder="Description"
              ></textarea>
            </div>
            <div class="flex gap-2">
              <button @click="saveEdit(client)" class="btn btn-xs btn-success">Save</button>
              <button @click="cancelEdit(client)" class="btn btn-xs btn-ghost">Cancel</button>
            </div>
          </div>

          <!-- Badges -->
          <div class="flex flex-wrap gap-2 mt-2">
            <span v-if="client.is_system" class="badge badge-neutral">System</span>
            <span v-if="!client.is_active" class="badge badge-warning">Inactive</span>
            <span class="badge badge-primary">{{ client.peer_count }} peer{{ client.peer_count !== 1 ? 's' : '' }}</span>
          </div>

          <!-- Client Info -->
          <div class="space-y-2 mt-3">
            <div v-if="client.subnet_range" class="text-sm">
              <span class="font-semibold">Subnet:</span>
              <div class="mt-1">{{ client.subnet_range }}</div>
            </div>

            <div v-if="client.location" class="text-sm">
              <span class="font-semibold">Location:</span>
              <div class="mt-1">{{ client.location }}</div>
            </div>

            <div v-if="client.description" class="text-sm">
              <span class="font-semibold">Description:</span>
              <div class="mt-1">{{ client.description }}</div>
            </div>

            <div class="text-sm">
              <span class="font-semibold">Created:</span>
              <div class="mt-1">{{ formatDate(client.created_at) }}</div>
            </div>
          </div>

          <!-- Actions -->
          <div class="card-actions justify-end mt-4">
            <button
              v-if="!client.is_system"
              @click="toggleActive(client)"
              class="btn btn-sm"
              :class="client.is_active ? 'btn-warning' : 'btn-success'"
            >
              {{ client.is_active ? 'Deactivate' : 'Activate' }}
            </button>
            <button
              v-if="!client.is_system"
              @click="deleteClient(client.id)"
              class="btn btn-sm btn-error"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Add client modal -->
    <dialog :class="{ 'modal modal-open': showAddModal }" class="modal">
      <div class="modal-box w-11/12 max-w-2xl">
        <h3 class="font-bold text-lg mb-4">Add New Client</h3>

        <form @submit.prevent="addClient">
          <div class="form-control mb-4">
            <label class="label"><span class="label-text">Client Name *</span></label>
            <input v-model="newClient.name" type="text" class="input input-bordered" required />
          </div>

          <div class="form-control mb-4">
            <label class="label"><span class="label-text">Subnet Range</span></label>
            <input v-model="newClient.subnet_range" type="text" class="input input-bordered" placeholder="10.200.0.0/24" />
            <label class="label"><span class="label-text-alt">CIDR notation for this client's network</span></label>
          </div>

          <div class="form-control mb-4">
            <label class="label"><span class="label-text">Location</span></label>
            <input v-model="newClient.location" type="text" class="input input-bordered" placeholder="City, State" />
          </div>

          <div class="form-control mb-6">
            <label class="label"><span class="label-text">Description</span></label>
            <textarea v-model="newClient.description" class="textarea textarea-bordered" rows="3"></textarea>
          </div>

          <div class="modal-action">
            <button type="button" @click="closeAddModal" class="btn">Cancel</button>
            <button type="submit" class="btn btn-primary" :disabled="submitting">
              {{ submitting ? 'Adding...' : 'Add Client' }}
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
import { ref, reactive, onMounted } from 'vue'
import api from '../services/api'

const clients = ref([])
const loading = ref(false)
const showAddModal = ref(false)
const submitting = ref(false)
const editingClient = ref({})
const editForm = reactive({
  name: '',
  subnet_range: '',
  location: '',
  description: ''
})
const newClient = ref({
  name: '',
  subnet_range: '',
  location: '',
  description: '',
  is_active: true
})

const fetchClients = async () => {
  loading.value = true
  try {
    const response = await api.listClients()
    clients.value = response.data
  } catch (error) {
    console.error('Error fetching clients:', error)
    alert('Failed to fetch clients')
  } finally {
    loading.value = false
  }
}

const startEdit = (client) => {
  editingClient.value[client.id] = true
  editForm.name = client.name
  editForm.subnet_range = client.subnet_range || ''
  editForm.location = client.location || ''
  editForm.description = client.description || ''
}

const cancelEdit = (client) => {
  delete editingClient.value[client.id]
  editForm.name = ''
  editForm.subnet_range = ''
  editForm.location = ''
  editForm.description = ''
}

const saveEdit = async (client) => {
  try {
    await api.updateClient(client.id, {
      name: editForm.name,
      subnet_range: editForm.subnet_range,
      location: editForm.location,
      description: editForm.description
    })
    cancelEdit(client)
    await fetchClients()
  } catch (error) {
    console.error('Error updating client:', error)
    alert(error.response?.data?.error || 'Failed to update client')
  }
}

const toggleActive = async (client) => {
  try {
    await api.updateClient(client.id, {
      is_active: !client.is_active
    })
    await fetchClients()
  } catch (error) {
    console.error('Error toggling client active status:', error)
    alert('Failed to update client status')
  }
}

const addClient = async () => {
  submitting.value = true
  try {
    await api.createClient(newClient.value)
    closeAddModal()
    fetchClients()
  } catch (error) {
    console.error('Error adding client:', error)
    alert(error.response?.data?.error || 'Failed to add client')
  } finally {
    submitting.value = false
  }
}

const deleteClient = async (clientId) => {
  if (!confirm('Are you sure you want to delete this client? Associated peers will become unassigned.')) return

  try {
    await api.deleteClient(clientId)
    fetchClients()
  } catch (error) {
    console.error('Error deleting client:', error)
    alert(error.response?.data?.error || 'Failed to delete client')
  }
}

const closeAddModal = () => {
  showAddModal.value = false
  newClient.value = {
    name: '',
    subnet_range: '',
    location: '',
    description: '',
    is_active: true
  }
}

const formatDate = (isoString) => {
  if (!isoString) return 'N/A'
  return new Date(isoString).toLocaleDateString()
}

onMounted(() => {
  fetchClients()
})
</script>
