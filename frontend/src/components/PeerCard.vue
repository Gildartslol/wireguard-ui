<template>
  <div class="card bg-base-100 shadow-xl">
    <div class="card-body">
      <!-- Editable Name -->
      <div v-if="!isEditing" class="flex items-center justify-between">
        <h2 class="card-title">{{ peer.name }}</h2>
        <button @click="startEdit" class="btn btn-xs btn-ghost" title="Edit name">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
          </svg>
        </button>
      </div>
      <div v-else class="space-y-2">
        <input
          v-model="editedName"
          type="text"
          class="input input-bordered input-sm w-full"
          :class="{ 'input-error': nameError }"
          placeholder="Enter peer name"
          maxlength="100"
          @keyup.enter="saveEdit"
          @keyup.esc="cancelEdit"
        />
        <div v-if="nameError" class="text-error text-xs">{{ nameError }}</div>
        <div class="flex gap-2">
          <button @click="saveEdit" class="btn btn-xs btn-success" :disabled="isSaving || !!nameError">
            <span v-if="!isSaving">Save</span>
            <span v-else class="loading loading-spinner loading-xs"></span>
          </button>
          <button @click="cancelEdit" class="btn btn-xs btn-ghost" :disabled="isSaving">
            Cancel
          </button>
        </div>
      </div>

      <!-- Status and Badges -->
      <div class="flex flex-wrap gap-2 mt-2">
        <!-- Connection Status -->
        <span v-if="peer.configured === false" class="badge badge-warning" title="Peer exists in database but not in WireGuard">
          ⚠️ Not Configured
        </span>
        <span v-else-if="peer.connected" class="badge badge-success" title="Peer is actively connected">
          ✓ Connected
        </span>
        <span v-else class="badge badge-error" title="Peer is disconnected">
          ✗ Disconnected
        </span>

        <span v-if="peer.is_router" class="badge badge-accent">Router</span>
        <span v-if="peer.client" class="badge badge-info" :title="`Client: ${peer.client.name}`">
          {{ peer.client.name }}
        </span>
      </div>

      <div class="space-y-2">
        <div class="text-sm">
          <span class="font-semibold">Public Key:</span>
          <div class="font-mono text-xs mt-1 break-all">{{ peer.public_key }}</div>
        </div>

        <div class="text-sm">
          <span class="font-semibold">Allowed IPs:</span>
          <div class="mt-1">{{ formatAllowedIPs(peer.allowed_ips) }}</div>
        </div>

        <!-- Real-time Connection Data -->
        <div v-if="peer.endpoint" class="text-sm">
          <span class="font-semibold">Endpoint:</span>
          <div class="mt-1">{{ peer.endpoint }}</div>
        </div>

        <div v-if="peer.latest_handshake" class="text-sm">
          <span class="font-semibold">Last Handshake:</span>
          <div class="mt-1">{{ formatHandshake(peer.latest_handshake) }}</div>
        </div>

        <div v-if="peer.transfer_rx !== undefined || peer.transfer_tx !== undefined" class="text-sm">
          <span class="font-semibold">Transfer:</span>
          <div class="mt-1">
            <span class="text-xs">↓ {{ formatBytes(peer.transfer_rx) }}</span>
            <span class="mx-2">|</span>
            <span class="text-xs">↑ {{ formatBytes(peer.transfer_tx) }}</span>
          </div>
        </div>

        <div v-if="peer.description" class="text-sm">
          <span class="font-semibold">Description:</span>
          <div class="mt-1">{{ peer.description }}</div>
        </div>

        <div class="text-sm">
          <span class="font-semibold">Created:</span>
          <div class="mt-1">{{ formatDate(peer.created_at) }}</div>
        </div>
      </div>

      <div class="card-actions justify-end mt-4">
        <button @click="$emit('config', peer)" class="btn btn-sm btn-primary">
          Download Config
        </button>
        <button @click="$emit('delete', peer.id)" class="btn btn-sm btn-error">
          Delete
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  peer: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['delete', 'config', 'update'])

// Edit state
const isEditing = ref(false)
const editedName = ref('')
const isSaving = ref(false)

// Validation
const nameError = computed(() => {
  if (isEditing.value && editedName.value.trim().length === 0) {
    return 'Name cannot be empty'
  }
  if (isEditing.value && editedName.value.length > 100) {
    return 'Name is too long (max 100 characters)'
  }
  return null
})

// Edit methods
const startEdit = () => {
  editedName.value = props.peer.name
  isEditing.value = true
}

const cancelEdit = () => {
  isEditing.value = false
  editedName.value = ''
}

const saveEdit = async () => {
  if (nameError.value) return

  const trimmedName = editedName.value.trim()
  if (trimmedName === props.peer.name) {
    // No change, just cancel
    cancelEdit()
    return
  }

  isSaving.value = true
  try {
    emit('update', props.peer.id, { name: trimmedName })
    isEditing.value = false
  } catch (error) {
    console.error('Error updating peer name:', error)
  } finally {
    isSaving.value = false
  }
}

const formatAllowedIPs = (ips) => {
  if (Array.isArray(ips)) {
    return ips.join(', ')
  }
  return ips
}

const formatDate = (isoString) => {
  if (!isoString) return 'N/A'
  return new Date(isoString).toLocaleDateString()
}

const formatBytes = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const formatHandshake = (isoString) => {
  if (!isoString) return 'Never'
  const date = new Date(isoString)
  const now = new Date()
  const diffMs = now - date
  const diffSecs = Math.floor(diffMs / 1000)
  const diffMins = Math.floor(diffSecs / 60)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffDays > 0) return `${diffDays}d ago`
  if (diffHours > 0) return `${diffHours}h ago`
  if (diffMins > 0) return `${diffMins}m ago`
  return `${diffSecs}s ago`
}
</script>
