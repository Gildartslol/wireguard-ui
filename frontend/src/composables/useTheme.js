import { ref, watch } from 'vue'

const THEME_STORAGE_KEY = 'wireguard-ui-theme'
const THEMES = {
  LIGHT: 'light',
  DARK: 'dark'
}

// Shared state across all component instances
const currentTheme = ref(THEMES.LIGHT)

/**
 * Theme management composable
 * Handles light/dark mode toggle with localStorage persistence
 */
export function useTheme() {
  // Initialize theme from localStorage or default to light
  const initTheme = () => {
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY)
    if (savedTheme && Object.values(THEMES).includes(savedTheme)) {
      currentTheme.value = savedTheme
    } else {
      currentTheme.value = THEMES.LIGHT
    }
    applyTheme(currentTheme.value)
  }

  // Apply theme to HTML element
  const applyTheme = (theme) => {
    document.documentElement.setAttribute('data-theme', theme)
  }

  // Toggle between light and dark
  const toggleTheme = () => {
    currentTheme.value = currentTheme.value === THEMES.LIGHT ? THEMES.DARK : THEMES.LIGHT
    applyTheme(currentTheme.value)
    localStorage.setItem(THEME_STORAGE_KEY, currentTheme.value)
  }

  // Set specific theme
  const setTheme = (theme) => {
    if (Object.values(THEMES).includes(theme)) {
      currentTheme.value = theme
      applyTheme(theme)
      localStorage.setItem(THEME_STORAGE_KEY, theme)
    }
  }

  // Computed property for checking if dark mode is active
  const isDark = () => currentTheme.value === THEMES.DARK

  return {
    currentTheme,
    toggleTheme,
    setTheme,
    initTheme,
    isDark,
    THEMES
  }
}
