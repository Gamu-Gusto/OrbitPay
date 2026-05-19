import { defineStore } from 'pinia'
import axios from 'axios'

export const useAuthStore = defineStore('auth', {
  state: () => {
    if (typeof window === 'undefined') {
      return { accessToken: null, refreshToken: null, user: null }
    }
    try {
      return {
        accessToken: localStorage.getItem('accessToken'),
        refreshToken: localStorage.getItem('refreshToken'),
        user: JSON.parse(localStorage.getItem('user') || 'null')
      }
    } catch {
      return { accessToken: null, refreshToken: null, user: null }
    }
  },
  getters: {
    isAuthenticated: (state) => !!state.accessToken,
    roles: (state) => state.user?.roles || []
  },
  actions: {
    async initializeAuth() {
      if (!this.accessToken) return false
      try {
        await axios.get('/auth/me', {
          headers: { Authorization: `Bearer ${this.accessToken}` }
        })
        return true
      } catch {
        this.clear()
        return false
      }
    },
    setAuth(accessToken, user, refreshToken = null) {
      this.accessToken = accessToken
      this.refreshToken = refreshToken
      this.user = user
      try {
        if (typeof window !== 'undefined') {
          localStorage.setItem('accessToken', accessToken)
          if (refreshToken) localStorage.setItem('refreshToken', refreshToken)
          localStorage.setItem('user', JSON.stringify(user))
        }
      } catch {}
    },
    clear() {
      this.accessToken = null
      this.refreshToken = null
      this.user = null
      try {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('accessToken')
          localStorage.removeItem('refreshToken')
          localStorage.removeItem('user')
        }
      } catch {}
    },
    async refreshAccessToken() {
      if (!this.refreshToken) return false
      try {
        const { data } = await axios.post('/auth/refresh', { refresh_token: this.refreshToken })
        this.setAuth(data.access_token, data.user, data.refresh_token)
        return true
      } catch {
        this.clear()
        return false
      }
    },
    async logout() {
      try {
        if (this.accessToken) {
          await axios.post('/auth/logout',
            { refresh_token: this.refreshToken || undefined },
            { headers: { Authorization: `Bearer ${this.accessToken}` } }
          )
        }
      } catch {}
      this.clear()
      window.location.href = '/login'
    }
  }
})
