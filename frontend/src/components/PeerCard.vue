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

      <div class="space-y-2">
        <div class="text-sm">
          <span class="font-semibold">Public Key:</span>
          <div class="font-mono text-xs mt-1 break-all">{{ peer.public_key }}</div>
        </div>

        <div class="text-sm">
          <span class="font-semibold">Allowed IPs:</span>
          <div class="mt-1">{{ formatAllowedIPs(peer.allowed_ips) }}</div>
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
        <button @click="$emit('delete', peer.public_key)" class="btn btn-sm btn-error">
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
    emit('update', props.peer.public_key, { name: trimmedName })
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
</script>
