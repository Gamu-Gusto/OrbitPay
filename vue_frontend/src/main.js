import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'
import axios from 'axios'
import { useAuthStore } from './stores/auth'

if (import.meta.env.VITE_API_URL) {
  axios.defaults.baseURL = import.meta.env.VITE_API_URL
}

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)

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

    return Promise.reject(error)
  }
)

async function initializeApp() {
  const auth = useAuthStore()
  await auth.initializeAuth()
  app.mount('#app')
}

initializeApp()
