<template>
  <div class="auth-page">
    <div class="auth-card">

      <!-- Brand -->
      <div class="auth-brand">
        <img src="/OrbitPayfinal.jpeg" alt="OrbitPay" class="auth-logo" />
        <p class="brand-tagline">Payroll &amp; Reports Platform</p>
      </div>

      <!-- Form -->
      <div class="auth-form">
        <h2 class="form-heading">Sign in to your account</h2>

        <div class="form-group">
          <label class="form-label">Email address</label>
          <input
            v-model="email"
            type="email"
            class="form-input"
            placeholder="you@example.com"
            autocomplete="email"
            @keydown.enter="login"
          />
        </div>

        <div class="form-group">
          <label class="form-label">Password</label>
          <input
            v-model="password"
            type="password"
            class="form-input"
            placeholder="••••••••"
            autocomplete="current-password"
            @keydown.enter="login"
          />
        </div>

        <div v-if="errorMsg" class="auth-error">{{ errorMsg }}</div>

        <button @click="login" :disabled="loading" class="btn-primary w-full auth-submit">
          <svg v-if="loading" class="spin-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
            <path d="M12 2a10 10 0 0110 10" stroke-linecap="round"/>
          </svg>
          {{ loading ? 'Signing in…' : 'Sign in' }}
        </button>

        <p class="auth-footer">
          Don't have an account?
          <router-link to="/register">Create account</router-link>
        </p>
      </div>

    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

export default {
  name: 'LoginView',
  setup() {
    const email    = ref('')
    const password = ref('')
    const loading  = ref(false)
    const errorMsg = ref('')
    const auth     = useAuthStore()

    const login = async () => {
      if (!email.value || !password.value) {
        errorMsg.value = 'Please enter your email and password.'
        return
      }
      loading.value  = true
      errorMsg.value = ''
      try {
        const { data } = await axios.post('/auth/login', {
          email: email.value,
          password: password.value
        })
        auth.setAuth(data.access_token, data.user, data.refresh_token)
        window.location.href = '/'
      } catch (e) {
        errorMsg.value = e.response?.data?.detail || 'Login failed. Please try again.'
      } finally {
        loading.value = false
      }
    }

    return { email, password, loading, errorMsg, login }
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f172a 0%, #1a2744 60%, #1e3a5f 100%);
  padding: 24px;
}

.auth-card {
  background: #fff;
  border-radius: 16px;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 24px 64px rgba(0,0,0,0.25);
  overflow: hidden;
}

.auth-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 28px 28px 20px;
  border-bottom: 1px solid var(--color-border);
  background: #fafbfd;
}

.auth-logo {
  height: 52px;
  width: auto;
}

.brand-tagline {
  font-size: 11.5px;
  color: var(--color-text-muted);
  line-height: 1.3;
}

.auth-form {
  padding: 28px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-heading {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-base);
  margin-bottom: 4px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.auth-error {
  padding: 10px 12px;
  background: var(--color-error-bg);
  border: 1px solid var(--color-error-border);
  border-radius: 6px;
  font-size: 13px;
  color: #b91c1c;
}

.auth-submit {
  height: 38px;
  font-size: 14px;
  margin-top: 4px;
}

.spin-icon {
  width: 16px;
  height: 16px;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }

.auth-footer {
  text-align: center;
  font-size: 13px;
  color: var(--color-text-muted);
}
.auth-footer a {
  color: var(--color-accent);
  text-decoration: none;
  font-weight: 500;
}
.auth-footer a:hover { text-decoration: underline; }
</style>
