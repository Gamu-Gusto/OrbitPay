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
    roles: (state) => state.user?.roles || [],
    forcePasswordChange: (state) => !!state.user?.force_password_change,
    hasPermission: (state) => (permission) => {
      const ROLE_PERMISSIONS = {
        super_admin: [
          'MANAGE_COMPANIES', 'DELETE_COMPANY', 'VIEW_COMPANIES',
          'CREATE_EMPLOYEE', 'EDIT_EMPLOYEE', 'DELETE_EMPLOYEE', 'VIEW_EMPLOYEES', 'IMPORT_EMPLOYEES',
          'RUN_PAYROLL', 'APPROVE_PAYROLL', 'VIEW_PAYROLL', 'VIEW_PAYROLL_REPORTS', 'VIEW_HR_REPORTS',
          'APPROVE_LEAVE', 'VIEW_LEAVE_REQUESTS', 'REQUEST_DOCUMENTATION', 'MANAGE_LEAVE_BALANCES',
          'REVIEW_DOCUMENTS', 'APPROVE_DOCUMENTS', 'VIEW_DOCUMENTS',
          'APPROVE_BANKING', 'VIEW_BANKING',
          'ASSIGN_ACCOUNTANTS', 'MANAGE_ASSIGNMENTS',
          'VIEW_AUDIT_LOGS', 'VIEW_ALL_REPORTS',
          'CREATE_USER', 'DEACTIVATE_USER',
        ],
        accountant: [
          'MANAGE_COMPANIES', 'VIEW_COMPANIES',
          'CREATE_EMPLOYEE', 'EDIT_EMPLOYEE', 'DELETE_EMPLOYEE', 'VIEW_EMPLOYEES', 'IMPORT_EMPLOYEES',
          'RUN_PAYROLL', 'VIEW_PAYROLL', 'VIEW_PAYROLL_REPORTS',
          'VIEW_LEAVE_REQUESTS', 'MANAGE_LEAVE_BALANCES',
          'VIEW_DOCUMENTS', 'VIEW_BANKING',
          'VIEW_HR_REPORTS', 'VIEW_AUDIT_LOGS',
        ],
        employee: [
          'VIEW_OWN_PAYSLIPS', 'VIEW_OWN_LEAVE', 'APPLY_LEAVE',
          'UPLOAD_DOCUMENTS', 'SUBMIT_BANKING_CHANGE',
          'UPDATE_PASSWORD', 'VIEW_OWN_PAYROLL_HISTORY',
        ],
      }
      const userRoles = state.user?.roles || []
      return userRoles.some(role => (ROLE_PERMISSIONS[role] || []).includes(permission))
    }
  },
  actions: {
    async initializeAuth() {
      if (!this.accessToken) return false
      try {
        const { data } = await axios.get('/auth/me', {
          headers: { Authorization: `Bearer ${this.accessToken}` }
        })
        // Merge fresh data (force_password_change may have changed)
        this.user = { ...this.user, ...data }
        try {
          if (typeof window !== 'undefined') {
            localStorage.setItem('user', JSON.stringify(this.user))
          }
        } catch {}
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
