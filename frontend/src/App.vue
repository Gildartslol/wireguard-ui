<template>
  <div class="min-h-screen bg-base-200">
    <!-- Navbar (only shown when logged in) -->
    <nav v-if="isAuthenticated" class="navbar bg-base-100 shadow-lg">
      <div class="flex-1">
        <router-link to="/" class="btn btn-ghost normal-case text-xl">
          WireGuard UI
        </router-link>
      </div>
      <div class="flex-none">
        <ul class="menu menu-horizontal px-1">
          <li>
            <router-link to="/" active-class="active">Dashboard</router-link>
          </li>
          <li>
            <router-link to="/peers" active-class="active">Peers</router-link>
          </li>
          <li>
            <router-link to="/history" active-class="active">History</router-link>
          </li>
          <li>
            <button @click="handleLogout" class="btn btn-ghost">Logout</button>
          </li>
        </ul>
      </div>
    </nav>

    <!-- Main content -->
    <main class="container mx-auto p-4">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from './services/api'

const router = useRouter()
const route = useRoute()
const isAuthenticated = ref(false)

// Check authentication on mount and route changes
const checkAuth = async () => {
  try {
    await api.checkAuth()
    isAuthenticated.value = true
  } catch (error) {
    isAuthenticated.value = false
  }
}

// Handle logout
const handleLogout = async () => {
  try {
    await api.logout()
    isAuthenticated.value = false
    router.push('/login')
  } catch (error) {
    console.error('Logout error:', error)
  }
}

onMounted(checkAuth)
watch(() => route.path, checkAuth)
</script>
