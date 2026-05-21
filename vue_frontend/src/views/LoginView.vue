<template>
  <div class="auth-page">
    <div class="auth-card">

      <!-- Brand -->
      <div class="auth-brand">
        <img src="/OrbitPayfinal.jpeg" alt="OrbitPay" class="auth-logo" />
        <p class="brand-tagline">Payroll &amp; Reports Platform</p>
      </div>

      <!-- Tab switcher -->
      <div class="auth-tabs">
        <button
          class="auth-tab"
          :class="{ active: activeTab === 'employee' }"
          @click="switchTab('employee')"
        >Employee Login</button>
        <button
          class="auth-tab"
          :class="{ active: activeTab === 'staff' }"
          @click="switchTab('staff')"
        >Staff Access</button>
      </div>

      <!-- ── Employee Login tab ── -->
      <div v-if="activeTab === 'employee'" class="auth-form">
        <div v-if="!showForgot">
          <h2 class="form-heading">Employee sign in</h2>

          <div class="form-group">
            <label class="form-label">Email address</label>
            <input v-model="email" type="email" class="form-input" placeholder="you@example.com"
              autocomplete="email" @keydown.enter="login('employee')" />
          </div>
          <div class="form-group">
            <label class="form-label">Password</label>
            <input v-model="password" type="password" class="form-input" placeholder="••••••••"
              autocomplete="current-password" @keydown.enter="login('employee')" />
          </div>

          <div v-if="errorMsg" class="auth-error">{{ errorMsg }}</div>

          <button @click="login('employee')" :disabled="loading" class="btn-primary w-full auth-submit">
            <svg v-if="loading" class="spin-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
              <path d="M12 2a10 10 0 0110 10" stroke-linecap="round"/>
            </svg>
            {{ loading ? 'Signing in…' : 'Sign in' }}
          </button>

          <p class="auth-footer">
            <button class="link-btn" @click="showForgot = true">Forgot your password?</button>
          </p>
        </div>

        <!-- Forgot password (shared) -->
        <div v-else>
          <h2 class="form-heading">Reset your password</h2>
          <p class="form-hint">Enter your email and we'll send a reset link if your account exists.</p>
          <div class="form-group">
            <label class="form-label">Email address</label>
            <input v-model="forgotEmail" type="email" class="form-input" placeholder="you@example.com"
              autocomplete="email" @keydown.enter="sendReset" />
          </div>
          <div v-if="forgotMsg" class="auth-success">{{ forgotMsg }}</div>
          <div v-if="forgotError" class="auth-error">{{ forgotError }}</div>
          <button @click="sendReset" :disabled="forgotLoading" class="btn-primary w-full auth-submit">
            {{ forgotLoading ? 'Sending…' : 'Send reset link' }}
          </button>
          <p class="auth-footer">
            <button class="link-btn" @click="showForgot = false">← Back to sign in</button>
          </p>
        </div>
      </div>

      <!-- ── Staff Access tab ── -->
      <div v-if="activeTab === 'staff'" class="auth-form">
        <div v-if="!showForgot && !showRegister">
          <h2 class="form-heading">Staff sign in</h2>

          <div class="form-group">
            <label class="form-label">Email address</label>
            <input v-model="email" type="email" class="form-input" placeholder="you@example.com"
              autocomplete="email" @keydown.enter="login('staff')" />
          </div>
          <div class="form-group">
            <label class="form-label">Password</label>
            <input v-model="password" type="password" class="form-input" placeholder="••••••••"
              autocomplete="current-password" @keydown.enter="login('staff')" />
          </div>

          <div v-if="errorMsg" class="auth-error">{{ errorMsg }}</div>

          <button @click="login('staff')" :disabled="loading" class="btn-primary w-full auth-submit">
            <svg v-if="loading" class="spin-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
              <path d="M12 2a10 10 0 0110 10" stroke-linecap="round"/>
            </svg>
            {{ loading ? 'Signing in…' : 'Sign in' }}
          </button>

          <p class="auth-footer">
            <button class="link-btn" @click="showForgot = true">Forgot your password?</button>
            &nbsp;·&nbsp;
            <button class="link-btn" @click="showRegister = true">Register as Accountant</button>
          </p>
        </div>

        <!-- Forgot password (shared) -->
        <div v-else-if="showForgot">
          <h2 class="form-heading">Reset your password</h2>
          <p class="form-hint">Enter your email and we'll send a reset link if your account exists.</p>
          <div class="form-group">
            <label class="form-label">Email address</label>
            <input v-model="forgotEmail" type="email" class="form-input" placeholder="you@example.com"
              autocomplete="email" @keydown.enter="sendReset" />
          </div>
          <div v-if="forgotMsg" class="auth-success">{{ forgotMsg }}</div>
          <div v-if="forgotError" class="auth-error">{{ forgotError }}</div>
          <button @click="sendReset" :disabled="forgotLoading" class="btn-primary w-full auth-submit">
            {{ forgotLoading ? 'Sending…' : 'Send reset link' }}
          </button>
          <p class="auth-footer">
            <button class="link-btn" @click="showForgot = false">← Back to sign in</button>
          </p>
        </div>

        <!-- Accountant registration form -->
        <div v-else-if="showRegister">
          <h2 class="form-heading">Register as Accountant</h2>
          <p class="form-hint">Your request will be reviewed by a Super Admin before your account is activated.</p>

          <div v-if="regSubmitted" class="auth-success">
            Your request has been submitted. You will receive an email once your account is approved.
            Returning to login…
          </div>

          <template v-else>
            <div class="form-group">
              <label class="form-label">Full Name <span class="req">*</span></label>
              <input v-model="reg.full_name" type="text" class="form-input" placeholder="Jane Doe" />
            </div>
            <div class="form-group">
              <label class="form-label">Email Address <span class="req">*</span></label>
              <input v-model="reg.email" type="email" class="form-input" placeholder="you@example.com" autocomplete="email" />
            </div>
            <div class="form-group">
              <label class="form-label">Password <span class="req">*</span></label>
              <input v-model="reg.password" type="password" class="form-input" placeholder="Min 8 characters" autocomplete="new-password" />
            </div>
            <div class="form-group">
              <label class="form-label">Confirm Password <span class="req">*</span></label>
              <input v-model="reg.password_confirm" type="password" class="form-input" placeholder="Repeat password" autocomplete="new-password" />
            </div>
            <div class="form-group">
              <label class="form-label">Firm / Practice Name</label>
              <input v-model="reg.firm_name" type="text" class="form-input" placeholder="Optional" />
            </div>
            <div class="form-group">
              <label class="form-label">Phone</label>
              <input v-model="reg.phone" type="tel" class="form-input" placeholder="Optional" />
            </div>

            <div v-if="regError" class="auth-error" style="margin-top:4px">{{ regError }}</div>

            <button @click="submitRegistration" :disabled="regLoading" class="btn-primary w-full auth-submit" style="margin-top:8px">
              {{ regLoading ? 'Submitting…' : 'Submit Registration' }}
            </button>
            <p class="auth-footer">
              <button class="link-btn" @click="showRegister = false">← Back to sign in</button>
            </p>
          </template>
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { useRouter, useRoute } from 'vue-router'

export default {
  name: 'LoginView',
  setup() {
    const router = useRouter()
    const route  = useRoute()
    const auth   = useAuthStore()

    const activeTab  = ref(route.query.tab === 'staff' ? 'staff' : 'employee')
    const showForgot  = ref(false)
    const showRegister = ref(false)

    const email    = ref('')
    const password = ref('')
    const loading  = ref(false)
    const errorMsg = ref('')

    const forgotEmail   = ref('')
    const forgotLoading = ref(false)
    const forgotMsg     = ref('')
    const forgotError   = ref('')

    const reg = reactive({ full_name: '', email: '', password: '', password_confirm: '', firm_name: '', phone: '' })
    const regLoading   = ref(false)
    const regError     = ref('')
    const regSubmitted = ref(false)

    const switchTab = (tab) => {
      activeTab.value = tab
      errorMsg.value  = ''
      showForgot.value  = false
      showRegister.value = false
      router.replace({ query: { tab } })
    }

    onMounted(() => {
      if (route.query.tab === 'staff') activeTab.value = 'staff'
    })

    const login = async (context) => {
      if (!email.value || !password.value) {
        errorMsg.value = 'Please enter your email and password.'
        return
      }
      loading.value  = true
      errorMsg.value = ''
      try {
        const { data } = await axios.post('/auth/login', {
          email: email.value,
          password: password.value,
          login_context: context,
        })
        auth.setAuth(data.access_token, data.user, data.refresh_token)
        const roles = data.user?.roles || []
        const isEmployeeOnly = roles.includes('employee') &&
          !roles.some(r => ['super_admin', 'accountant', 'manager'].includes(r))
        if (isEmployeeOnly) {
          router.push('/portal')
        } else if (roles.includes('manager')) {
          router.push('/manager')
        } else {
          router.push('/')
        }
      } catch (e) {
        errorMsg.value = e.response?.data?.detail || 'Login failed. Please try again.'
      } finally {
        loading.value = false
      }
    }

    const sendReset = async () => {
      forgotMsg.value   = ''
      forgotError.value = ''
      if (!forgotEmail.value) { forgotError.value = 'Please enter your email address.'; return }
      forgotLoading.value = true
      try {
        await axios.post('/auth/forgot-password', { email: forgotEmail.value })
        forgotMsg.value = 'If that email exists, a reset link has been sent.'
      } catch {
        forgotError.value = 'Failed to send reset link. Please try again.'
      } finally {
        forgotLoading.value = false
      }
    }

    const submitRegistration = async () => {
      regError.value = ''
      if (!reg.full_name || !reg.email || !reg.password || !reg.password_confirm) {
        regError.value = 'Full name, email, and password are required.'
        return
      }
      if (reg.password.length < 8) {
        regError.value = 'Password must be at least 8 characters.'
        return
      }
      if (reg.password !== reg.password_confirm) {
        regError.value = 'Passwords do not match.'
        return
      }
      regLoading.value = true
      try {
        await axios.post('/auth/register/accountant', {
          full_name: reg.full_name,
          email: reg.email,
          password: reg.password,
          firm_name: reg.firm_name || undefined,
          phone: reg.phone || undefined,
        })
        regSubmitted.value = true
        setTimeout(() => { showRegister.value = false; regSubmitted.value = false }, 3000)
      } catch (e) {
        regError.value = e.response?.data?.detail || 'Failed to submit registration.'
      } finally {
        regLoading.value = false
      }
    }

    return {
      activeTab, switchTab, showForgot, showRegister,
      email, password, loading, errorMsg, login,
      forgotEmail, forgotLoading, forgotMsg, forgotError, sendReset,
      reg, regLoading, regError, regSubmitted, submitRegistration,
    }
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
  max-width: 440px;
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

.auth-logo { height: 52px; width: auto; }

.brand-tagline { font-size: 11.5px; color: var(--color-text-muted); }

/* ── Tabs ── */
.auth-tabs {
  display: flex;
  border-bottom: 1px solid var(--color-border);
}

.auth-tab {
  flex: 1;
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 500;
  font-family: inherit;
  color: var(--color-text-muted);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}
.auth-tab.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}
.auth-tab:hover:not(.active) { color: var(--color-text-base); }

/* ── Form ── */
.auth-form {
  padding: 24px 28px 28px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.form-heading {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-base);
  margin-bottom: 2px;
}

.form-hint {
  font-size: 12.5px;
  color: var(--color-text-muted);
  margin-top: -6px;
}

.form-group { display: flex; flex-direction: column; gap: 5px; }

.auth-error {
  padding: 10px 12px;
  background: var(--color-error-bg);
  border: 1px solid var(--color-error-border);
  border-radius: 6px;
  font-size: 13px;
  color: #b91c1c;
}

.auth-success {
  padding: 10px 12px;
  background: #dcfce7;
  border: 1px solid #86efac;
  border-radius: 6px;
  font-size: 13px;
  color: #15803d;
}

.auth-submit { height: 38px; font-size: 14px; }

.spin-icon {
  width: 16px; height: 16px;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }

.auth-footer {
  text-align: center;
  font-size: 13px;
  color: var(--color-text-muted);
  margin: 0;
}

.link-btn {
  background: none; border: none; padding: 0;
  font-size: 13px; color: var(--color-accent);
  cursor: pointer; font-family: inherit; font-weight: 500;
}
.link-btn:hover { text-decoration: underline; }

.req { color: var(--color-error); margin-left: 2px; }
</style>
