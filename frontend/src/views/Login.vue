<template>
  <div class="flex items-center justify-center min-h-[80vh]">
    <div class="card w-96 bg-base-100 shadow-xl">
      <div class="card-body">
        <h2 class="card-title text-center justify-center mb-4">WireGuard UI Login</h2>

        <!-- Error alert -->
        <div v-if="error" class="alert alert-error mb-4">
          <span>{{ error }}</span>
        </div>

        <form @submit.prevent="handleLogin">
          <!-- Username input -->
          <div class="form-control w-full mb-4">
            <label class="label">
              <span class="label-text">Username</span>
            </label>
            <input
              v-model="username"
              type="text"
              placeholder="Enter username"
              class="input input-bordered w-full"
              required
              :disabled="loading"
            />
          </div>

          <!-- Password input -->
          <div class="form-control w-full mb-6">
            <label class="label">
              <span class="label-text">Password</span>
            </label>
            <input
              v-model="password"
              type="password"
              placeholder="Enter password"
              class="input input-bordered w-full"
              required
              :disabled="loading"
            />
          </div>

          <!-- Login button -->
          <div class="form-control">
            <button
              type="submit"
              class="btn btn-primary w-full"
              :class="{ 'loading': loading }"
              :disabled="loading"
            >
              {{ loading ? 'Logging in...' : 'Login' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'

const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  error.value = ''
  loading.value = true

  try {
    await api.login(username.value, password.value)
    router.push('/')
  } catch (err) {
    error.value = err.response?.data?.error || 'Login failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>
