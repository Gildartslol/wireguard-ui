<template>
  <div class="card bg-base-100 shadow-xl">
    <div class="card-body">
      <h2 class="card-title">{{ peer.name }}</h2>

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
defineProps({
  peer: {
    type: Object,
    required: true
  }
})

defineEmits(['delete', 'config'])

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
