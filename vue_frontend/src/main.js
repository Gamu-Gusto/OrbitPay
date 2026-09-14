import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'
import axios from 'axios'
import { useAuthStore } from './stores/auth'

// Render injects VITE_* variables at build time. Use the production API as a
// safe fallback so a missing dashboard variable cannot make API requests hit
// the static site's SPA rewrite and appear to succeed with HTML.
axios.defaults.baseURL = import.meta.env.VITE_API_URL || 'https://payroll-api-6ov2.onrender.com'

axios.defaults.timeout = 15000
// SECURITY TODO: JWT stored in localStorage is vulnerable to XSS.
// Migrate to httpOnly cookies when backend session handling is updated.
// Do not change storage without updating the full auth flow.
axios.defaults.withCredentials = false  // Keep false — using Bearer tokens, not cookies

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)

function showToast(message, type = 'error') {
  const existing = document.getElementById('orbit-toast')
  if (existing) existing.remove()
  const el = document.createElement('div')
  el.id = 'orbit-toast'
  el.style.cssText = [
    'position:fixed', 'bottom:24px', 'right:24px', 'z-index:9999',
    'padding:12px 16px', 'border-radius:8px', 'font-size:13px',
    'font-family:Inter,system-ui,sans-serif', 'max-width:320px',
    'line-height:1.4', 'pointer-events:none',
    'box-shadow:0 4px 16px rgba(0,0,0,0.15)',
    type === 'warning'
      ? 'background:#F79009;color:#fff'
      : 'background:#F04438;color:#fff'
  ].join(';')
  el.textContent = message
  document.body.appendChild(el)
  setTimeout(() => el.remove(), 5000)
}

// Attach Authorization header to every outgoing request
axios.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.accessToken) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${auth.accessToken}`
  }
  return config
})

// Silent token refresh on 401 — queues concurrent requests while refreshing
let isRefreshing = false
let refreshQueue = []

const processQueue = (token) => {
  refreshQueue.forEach(({ resolve, reject, config }) => {
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
      resolve(axios(config))
    } else {
      reject(new Error('Session expired'))
    }
  })
  refreshQueue = []
}

axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    const status = error.response?.status

    // Don't retry refresh or login endpoints — just clear and redirect
    if (status === 401 && (original.url?.includes('/auth/refresh') || original.url?.includes('/auth/login'))) {
      const auth = useAuthStore()
      auth.clear()
      if (window.location.pathname !== '/login') window.location.href = '/login'
      return Promise.reject(error)
    }

    if (status === 401 && !original._retry) {
      original._retry = true

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          refreshQueue.push({ resolve, reject, config: original })
        })
      }

      isRefreshing = true
      const auth = useAuthStore()
      const success = await auth.refreshAccessToken()
      isRefreshing = false

      if (success) {
        processQueue(auth.accessToken)
        original.headers.Authorization = `Bearer ${auth.accessToken}`
        return axios(original)
      } else {
        processQueue(null)
        auth.clear()
        if (window.location.pathname !== '/login') window.location.href = '/login'
        return Promise.reject(error)
      }
    }

    // 403 — authenticated but not authorised
    // The public first-run setup form handles an invalid secret locally. Let
    // that request reach its component instead of redirecting to /forbidden.
    const isAdminSetupRequest = original.url?.includes('/auth/admin/setup')
    if (status === 403 && !isAdminSetupRequest) {
      if (window.location.pathname !== '/forbidden') {
        window.location.href = '/forbidden'
      }
      return Promise.reject(error)
    }

    // 429 — rate limited
    if (status === 429) {
      showToast('Too many requests — please wait a moment.', 'warning')
      return Promise.reject(error)
    }

    // 5xx — server error
    if (status >= 500) {
      console.error('[OrbitPay] Server error:', error.response?.data)
      showToast('Something went wrong. Please try again.')
      return Promise.reject(error)
    }

    return Promise.reject(error)
  }
)

async function initializeApp() {
  const auth = useAuthStore()
  await auth.initializeAuth()
  app.mount('#app')
}

initializeApp()
