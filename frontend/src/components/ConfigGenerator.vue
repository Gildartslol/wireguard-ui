<template>
  <div class="card bg-base-100 shadow-xl">
    <div class="card-body">
      <h2 class="card-title">Generate Peer Configuration</h2>

      <form @submit.prevent="generateConfig">
        <div class="form-control mb-4">
          <label class="label"><span class="label-text">Peer Name</span></label>
          <input v-model="config.name" type="text" class="input input-bordered" required />
        </div>

        <div class="form-control mb-4">
          <label class="label"><span class="label-text">Private Key</span></label>
          <div class="join w-full">
            <input v-model="config.privateKey" type="text" class="input input-bordered join-item flex-1" readonly required />
            <button type="button" @click="generateKeys" class="btn btn-primary join-item">Generate</button>
          </div>
        </div>

        <div class="form-control mb-4">
          <label class="label"><span class="label-text">IP Address</span></label>
          <input v-model="config.address" type="text" class="input input-bordered" placeholder="10.0.0.2/32" required />
        </div>

        <div class="form-control mb-6">
          <label class="label"><span class="label-text">Server Endpoint</span></label>
          <input v-model="config.endpoint" type="text" class="input input-bordered" placeholder="your-server.com:51820" required />
        </div>

        <button type="submit" class="btn btn-primary w-full" :disabled="!config.privateKey">
          Generate Configuration
        </button>
      </form>

      <div v-if="generatedConfig" class="mt-6">
        <div class="divider">Generated Configuration</div>
        <textarea
          v-model="generatedConfig"
          class="textarea textarea-bordered w-full font-mono text-xs"
          rows="12"
          readonly
        ></textarea>

        <div class="flex gap-2 mt-4">
          <button @click="copyConfig" class="btn btn-sm btn-primary flex-1">
            Copy to Clipboard
          </button>
          <button @click="downloadConfig" class="btn btn-sm btn-secondary flex-1">
            Download .conf
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useToast } from '../composables/useToast'
import api from '../services/api'

const toast = useToast()

const config = ref({
  name: '',
  privateKey: '',
  address: '',
  endpoint: ''
})

const generatedConfig = ref('')
const publicKey = ref('')

const generateKeys = async () => {
  try {
    const response = await api.generateKeys()
    config.value.privateKey = response.data.private_key
    publicKey.value = response.data.public_key
    toast.success('Keys generated successfully')
  } catch (error) {
    console.error('Error generating keys:', error)
    toast.error('Failed to generate keys')
  }
}

const generateConfig = () => {
  const configText = `[Interface]
PrivateKey = ${config.value.privateKey}
Address = ${config.value.address}
DNS = 1.1.1.1

[Peer]
PublicKey = <SERVER_PUBLIC_KEY>
Endpoint = ${config.value.endpoint}
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
`
  generatedConfig.value = configText
}

const copyConfig = () => {
  navigator.clipboard.writeText(generatedConfig.value)
  toast.success('Configuration copied to clipboard!')
}

const downloadConfig = () => {
  const blob = new Blob([generatedConfig.value], { type: 'text/plain' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${config.value.name}.conf`
  document.body.appendChild(link)
  link.click()
  link.remove()
}
</script>
