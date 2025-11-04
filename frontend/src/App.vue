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
            <router-link to="/clients" active-class="active">Clients</router-link>
          </li>
          <li>
            <router-link to="/history" active-class="active">History</router-link>
          </li>
          <li>
            <button @click="toggleTheme" class="btn btn-ghost btn-circle" title="Toggle theme">
              <svg v-if="isDark()" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            </button>
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
import { useTheme } from './composables/useTheme'
import api from './services/api'

const router = useRouter()
const route = useRoute()
const isAuthenticated = ref(false)

// Theme management
const { toggleTheme, isDark, initTheme } = useTheme()

// Check authentication status
const checkAuth = async () => {
  // Only check auth if not on login page
  if (route.path === '/login') {
    isAuthenticated.value = false
    return
  }

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

// Initialize theme and check auth on mount
onMounted(() => {
  initTheme()
  checkAuth()
})

// Check auth when navigating to protected routes
watch(() => route.path, () => {
  checkAuth()
})
</script>
