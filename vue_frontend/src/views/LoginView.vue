<template>
  <div class="auth-shell">

    <!-- ── Left panel (brand) ─────────────────────────────────────────────── -->
    <aside class="auth-panel-left" aria-hidden="true">
      <div class="left-inner">
        <div class="left-brand">
          <img src="/OrbitPayfinal.jpeg" alt="OrbitPay" class="left-logo" />
          <span class="left-product-name">OrbitPay</span>
        </div>

        <div class="left-copy">
          <p class="left-tagline">Payroll &amp; HR for<br>South Africa</p>
        </div>

        <div class="left-trust">
          <span class="trust-pill">PAYE</span>
          <span class="trust-sep">·</span>
          <span class="trust-pill">UIF</span>
          <span class="trust-sep">·</span>
          <span class="trust-pill">IRP5</span>
          <span class="trust-sep">·</span>
          <span class="trust-pill">SDL</span>
        </div>
      </div>
    </aside>

    <!-- ── Right panel (form) ─────────────────────────────────────────────── -->
    <main class="auth-panel-right">

      <!-- Mobile-only logo -->
      <div class="mobile-logo" aria-hidden="true">
        <img src="/OrbitPayfinal.jpeg" alt="OrbitPay" class="mobile-logo-img" />
      </div>

      <div class="auth-form-wrap">

        <!-- ── Login form ──────────────────────────────────────────────────── -->
        <transition name="form-fade" mode="out-in">
          <div v-if="!showForgot" key="login">

            <div class="form-header">
              <h1 class="form-heading">Sign in to your workspace</h1>
            </div>

            <div class="field-stack">

              <div class="form-group">
                <label class="form-label" for="login-email">Email address</label>
                <input
                  id="login-email"
                  v-model="email"
                  type="email"
                  class="form-input"
                  placeholder="you@example.com"
                  autocomplete="email"
                  :disabled="loading"
                  @keydown.enter="login"
                />
              </div>

              <div class="form-group">
                <div class="pw-label-row">
                  <label class="form-label" for="login-password">Password</label>
                  <button
                    type="button"
                    class="forgot-inline"
                    tabindex="-1"
                    @click="showForgot = true"
                  >Forgot password?</button>
                </div>
                <div class="pw-wrap">
                  <input
                    id="login-password"
                    v-model="password"
                    :type="showPw ? 'text' : 'password'"
                    class="form-input pw-input"
                    placeholder="••••••••"
                    autocomplete="current-password"
                    :disabled="loading"
                    @keydown.enter="login"
                  />
                  <button
                    type="button"
                    class="pw-toggle"
                    :aria-label="showPw ? 'Hide password' : 'Show password'"
                    @click="showPw = !showPw"
                  >{{ showPw ? 'Hide' : 'Show' }}</button>
                </div>
              </div>

            </div>

            <transition name="banner-fade">
              <div v-if="errorMsg" class="auth-error" role="alert">
                <svg class="error-icon" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                  <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
                  <path d="M8 5v3.5M8 11h.01" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
                {{ errorMsg }}
              </div>
            </transition>

            <button
              type="button"
              class="btn-submit"
              :disabled="loading"
              @click="login"
            >
              <svg
                v-if="loading"
                class="spin-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                aria-hidden="true"
              >
                <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
                <path d="M12 2a10 10 0 0110 10" stroke-linecap="round"/>
              </svg>
              <span>{{ loading ? 'Signing in…' : 'Sign in' }}</span>
            </button>

          </div>

          <!-- ── Forgot password form ────────────────────────────────────── -->
          <div v-else key="forgot">

            <div class="form-header">
              <button type="button" class="back-link" @click="showForgot = false">
                <svg viewBox="0 0 16 16" fill="none" aria-hidden="true">
                  <path d="M10 3L5 8l5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Back to sign in
              </button>
              <h1 class="form-heading">Reset your password</h1>
              <p class="form-subtext">Enter your email and we'll send a reset link if your account exists.</p>
            </div>

            <div class="field-stack">
              <div class="form-group">
                <label class="form-label" for="forgot-email">Email address</label>
                <input
                  id="forgot-email"
                  v-model="forgotEmail"
                  type="email"
                  class="form-input"
                  placeholder="you@example.com"
                  autocomplete="email"
                  :disabled="forgotLoading"
                  @keydown.enter="sendReset"
                />
              </div>
            </div>

            <transition name="banner-fade">
              <div v-if="forgotMsg" class="auth-success" role="status">
                <svg class="error-icon" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                  <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
                  <path d="M5.5 8.5l1.75 1.75L10.5 6.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                {{ forgotMsg }}
              </div>
            </transition>

            <transition name="banner-fade">
              <div v-if="forgotError" class="auth-error" role="alert">
                <svg class="error-icon" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                  <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
                  <path d="M8 5v3.5M8 11h.01" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
                {{ forgotError }}
              </div>
            </transition>

            <button
              type="button"
              class="btn-submit"
              :disabled="forgotLoading"
              @click="sendReset"
            >
              <svg
                v-if="forgotLoading"
                class="spin-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                aria-hidden="true"
              >
                <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
                <path d="M12 2a10 10 0 0110 10" stroke-linecap="round"/>
              </svg>
              <span>{{ forgotLoading ? 'Sending…' : 'Send reset link' }}</span>
            </button>

          </div>
        </transition>

      </div><!-- /auth-form-wrap -->
    </main>

  </div><!-- /auth-shell -->
</template>

<script>
import { ref } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

export default {
  name: 'LoginView',
  setup() {
    const router = useRouter()
    const auth   = useAuthStore()

    const email    = ref('')
    const password = ref('')
    const showPw   = ref(false)
    const loading  = ref(false)
    const errorMsg = ref('')
    const showForgot = ref(false)

    const forgotEmail   = ref('')
    const forgotLoading = ref(false)
    const forgotMsg     = ref('')
    const forgotError   = ref('')

    const login = async () => {
      if (!email.value || !password.value) {
        errorMsg.value = 'Invalid email or password.'
        return
      }
      loading.value  = true
      errorMsg.value = ''
      try {
        const { data } = await axios.post('/auth/login', {
          email: email.value.trim().toLowerCase(),
          password: password.value,
        })
        auth.setAuth(data.access_token, data.user, data.refresh_token)
        const roles = data.user?.roles || []
        if (roles.includes('employee') && !roles.some(r => ['super_admin', 'accountant', 'manager'].includes(r))) {
          router.push('/portal')
        } else if (roles.includes('manager')) {
          router.push('/manager')
        } else {
          router.push('/')
        }
      } catch (error) {
        const status = error?.response?.status
        if (status === 401) {
          errorMsg.value = 'Invalid email or password.'
        } else if (status === 422) {
          errorMsg.value = 'Please enter a valid email address.'
        } else if (error?.code === 'ECONNABORTED') {
          errorMsg.value = 'The server took too long to respond. Please try again.'
        } else if (!error?.response) {
          errorMsg.value = 'Cannot connect to the server. Please check the deployment configuration.'
        } else {
          errorMsg.value = error.response?.data?.detail || 'Login failed. Please try again.'
        }
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

    return {
      email, password, showPw, loading, errorMsg, showForgot, login,
      forgotEmail, forgotLoading, forgotMsg, forgotError, sendReset,
    }
  },
}
</script>

<style scoped>
/* ── Shell layout ─────────────────────────────────────────────────────────── */
.auth-shell {
  display: grid;
  grid-template-columns: 1fr 1fr;
  min-height: 100vh;
}

/* ── Left panel ───────────────────────────────────────────────────────────── */
.auth-panel-left {
  background: #0F172A;
  padding: 48px;
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  position: relative;
}

.left-inner {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.left-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.left-logo {
  height: 48px;
  width: auto;
  border-radius: 8px;
  object-fit: cover;
  flex-shrink: 0;
}

.left-product-name {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  letter-spacing: -0.02em;
  font-family: var(--font-sans);
}

.left-copy {
  margin-top: auto;
  padding-top: 48px;
}

.left-tagline {
  font-size: 28px;
  font-weight: 600;
  color: #fff;
  line-height: 1.3;
  letter-spacing: -0.02em;
  font-family: var(--font-sans);
}

.left-trust {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 20px;
}

.trust-pill {
  font-size: 11px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.45);
  font-family: var(--font-sans);
  letter-spacing: 0.04em;
}

.trust-sep {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.2);
}

/* ── Right panel ──────────────────────────────────────────────────────────── */
.auth-panel-right {
  background: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
}

/* Mobile logo — hidden on desktop */
.mobile-logo {
  display: none;
}

/* ── Form wrapper ─────────────────────────────────────────────────────────── */
.auth-form-wrap {
  max-width: 380px;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ── Form header ──────────────────────────────────────────────────────────── */
.form-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-heading {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
  line-height: 1.3;
  font-family: var(--font-sans);
  margin: 0;
}

.form-subtext {
  font-size: 13px;
  color: var(--color-text-muted);
  line-height: 1.5;
  margin: 0;
  font-family: var(--font-sans);
}

/* ── Back link ────────────────────────────────────────────────────────────── */
.back-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: none;
  border: none;
  padding: 0;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-muted);
  cursor: pointer;
  font-family: var(--font-sans);
  transition: color var(--transition-fast);
  margin-bottom: 4px;
}

.back-link:hover {
  color: var(--color-text-base);
}

.back-link svg {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

/* ── Field stack ──────────────────────────────────────────────────────────── */
.field-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* ── Password row ─────────────────────────────────────────────────────────── */
.pw-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.forgot-inline {
  background: none;
  border: none;
  padding: 0;
  font-size: 11px;
  font-weight: 500;
  color: var(--color-accent);
  cursor: pointer;
  font-family: var(--font-sans);
  line-height: 1;
  transition: color var(--transition-fast);
}

.forgot-inline:hover {
  color: var(--color-accent-hover);
  text-decoration: underline;
}

/* ── Password input wrap ──────────────────────────────────────────────────── */
.pw-wrap {
  position: relative;
  display: flex;
}

.pw-input {
  padding-right: 52px;
}

.pw-toggle {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  padding: 0;
  font-size: 11.5px;
  font-weight: 500;
  color: var(--color-text-muted);
  cursor: pointer;
  font-family: var(--font-sans);
  line-height: 1;
  transition: color var(--transition-fast);
  user-select: none;
}

.pw-toggle:hover {
  color: var(--color-text-base);
}

/* ── Banners ──────────────────────────────────────────────────────────────── */
.auth-error {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  background: var(--color-error-bg);
  border: 1px solid var(--color-error-border);
  border-left: 3px solid var(--color-error);
  border-radius: var(--radius-md);
  font-size: 13px;
  font-family: var(--font-sans);
  color: #991b1b;
  line-height: 1.45;
}

.auth-success {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  background: var(--color-success-bg);
  border: 1px solid var(--color-success-border);
  border-left: 3px solid var(--color-success);
  border-radius: var(--radius-md);
  font-size: 13px;
  font-family: var(--font-sans);
  color: #065f46;
  line-height: 1.45;
}

.error-icon {
  width: 15px;
  height: 15px;
  flex-shrink: 0;
  margin-top: 1px;
}

/* ── Submit button ────────────────────────────────────────────────────────── */
.btn-submit {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  height: 40px;
  padding: 0 16px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  font-family: var(--font-sans);
  cursor: pointer;
  transition: background-color var(--transition-fast);
  margin-top: 4px;
  letter-spacing: -0.01em;
}

.btn-submit:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.btn-submit:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}

.btn-submit:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

/* ── Spinner ──────────────────────────────────────────────────────────────── */
.spin-icon {
  width: 15px;
  height: 15px;
  flex-shrink: 0;
  animation: auth-spin 0.75s linear infinite;
}

@keyframes auth-spin {
  to { transform: rotate(360deg); }
}

/* ── Transitions ──────────────────────────────────────────────────────────── */
.form-fade-enter-active,
.form-fade-leave-active {
  transition: opacity 140ms ease, transform 140ms ease;
}

.form-fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.form-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.banner-fade-enter-active,
.banner-fade-leave-active {
  transition: opacity 120ms ease, transform 120ms ease;
}

.banner-fade-enter-from,
.banner-fade-leave-to {
  opacity: 0;
  transform: translateY(-3px);
}

/* ── Responsive ───────────────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .auth-shell {
    grid-template-columns: 1fr;
  }

  .auth-panel-left {
    display: none;
  }

  .auth-panel-right {
    padding: 32px 24px;
    justify-content: flex-start;
    padding-top: 48px;
  }

  .mobile-logo {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 32px;
  }

  .mobile-logo-img {
    height: 36px;
    width: auto;
    border-radius: 6px;
    object-fit: cover;
  }

  .auth-form-wrap {
    max-width: 100%;
  }
}
</style>
