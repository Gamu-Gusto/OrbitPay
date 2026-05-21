<template>
  <div class="auth-page">
    <div class="auth-card">

      <div class="auth-brand">
        <img src="/OrbitPayfinal.jpeg" alt="OrbitPay" class="auth-logo" />
        <p class="brand-tagline">Payroll &amp; Reports Platform</p>
      </div>

      <!-- No token in URL -->
      <div v-if="!token" class="status-block">
        <svg class="status-icon error" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
        </svg>
        <p class="status-title">Invalid activation link</p>
        <p class="status-sub">This link is missing required information. Please request a new invitation from your administrator.</p>
        <router-link to="/login" class="link-btn">← Back to login</router-link>
      </div>

      <!-- Activation succeeded -->
      <div v-else-if="activated" class="status-block">
        <svg class="status-icon success" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/><polyline points="9 12 11 14 15 10"/>
        </svg>
        <p class="status-title">Account activated!</p>
        <p class="status-sub">Redirecting you to the login page…</p>
      </div>

      <!-- Activation failed -->
      <div v-else-if="activationError" class="status-block">
        <svg class="status-icon error" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
        </svg>
        <p class="status-title">Activation link expired</p>
        <p class="status-sub">{{ activationError }}</p>
        <router-link to="/login" class="link-btn">← Back to login</router-link>
      </div>

      <!-- Set password form -->
      <div v-else class="auth-form">
        <h2 class="form-heading">Activate your account</h2>
        <p class="form-hint">Set a password to complete your account setup.</p>

        <div class="form-group">
          <label class="form-label">New Password</label>
          <div class="pw-wrap">
            <input
              v-model="password"
              :type="showPw ? 'text' : 'password'"
              class="form-input"
              placeholder="Min. 8 characters"
              autocomplete="new-password"
              @keydown.enter="activate"
              @input="updateStrength"
            />
            <button type="button" class="pw-toggle" @click="showPw = !showPw">
              {{ showPw ? 'Hide' : 'Show' }}
            </button>
          </div>
          <div v-if="password" class="strength-bar-wrap">
            <div class="strength-bar">
              <div class="strength-fill" :class="strengthClass" :style="{ width: strengthWidth }"></div>
            </div>
            <span class="strength-label" :class="strengthClass">{{ strengthLabel }}</span>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Confirm Password</label>
          <input
            v-model="confirmPassword"
            :type="showPw ? 'text' : 'password'"
            class="form-input"
            placeholder="Repeat password"
            autocomplete="new-password"
            @keydown.enter="activate"
          />
        </div>

        <div v-if="errorMsg" class="auth-error">{{ errorMsg }}</div>

        <button @click="activate" :disabled="loading" class="btn-primary w-full auth-submit">
          <svg v-if="loading" class="spin-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
            <path d="M12 2a10 10 0 0110 10" stroke-linecap="round"/>
          </svg>
          {{ loading ? 'Activating…' : 'Activate Account' }}
        </button>

        <p class="auth-footer">
          <router-link to="/login" class="link-btn">← Back to login</router-link>
        </p>
      </div>

    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useRouter, useRoute } from 'vue-router'

export default {
  name: 'ActivateView',
  setup() {
    const router = useRouter()
    const route = useRoute()

    const token = ref(route.query.token || '')
    const password = ref('')
    const confirmPassword = ref('')
    const showPw = ref(false)
    const loading = ref(false)
    const errorMsg = ref('')
    const activated = ref(false)
    const activationError = ref('')

    const strengthScore = ref(0)

    const updateStrength = () => {
      const pw = password.value
      let score = 0
      if (pw.length >= 8) score++
      if (pw.length >= 12) score++
      if (/[A-Z]/.test(pw)) score++
      if (/[0-9]/.test(pw)) score++
      if (/[^A-Za-z0-9]/.test(pw)) score++
      strengthScore.value = score
    }

    const strengthLabel = computed(() => {
      if (strengthScore.value <= 1) return 'Weak'
      if (strengthScore.value <= 3) return 'Fair'
      return 'Strong'
    })

    const strengthClass = computed(() => {
      if (strengthScore.value <= 1) return 'strength-weak'
      if (strengthScore.value <= 3) return 'strength-fair'
      return 'strength-strong'
    })

    const strengthWidth = computed(() => {
      const pct = Math.min(100, (strengthScore.value / 5) * 100)
      return pct + '%'
    })

    const activate = async () => {
      errorMsg.value = ''
      if (!password.value || !confirmPassword.value) {
        errorMsg.value = 'Both password fields are required.'
        return
      }
      if (password.value.length < 8) {
        errorMsg.value = 'Password must be at least 8 characters.'
        return
      }
      if (password.value !== confirmPassword.value) {
        errorMsg.value = 'Passwords do not match.'
        return
      }
      loading.value = true
      try {
        await axios.post('/auth/activate', {
          token: token.value,
          new_password: password.value,
          confirm_password: confirmPassword.value,
        })
        activated.value = true
        setTimeout(() => router.push('/login'), 2000)
      } catch (e) {
        const detail = e?.response?.data?.detail
        if (e?.response?.status === 400) {
          activationError.value = detail || 'Invalid or expired activation link. Contact your administrator for a new invitation.'
        } else {
          errorMsg.value = detail || 'Activation failed. Please try again.'
        }
      } finally {
        loading.value = false
      }
    }

    return {
      token, password, confirmPassword, showPw, loading, errorMsg,
      activated, activationError,
      strengthLabel, strengthClass, strengthWidth,
      updateStrength, activate,
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

.auth-logo { height: 52px; width: auto; }
.brand-tagline { font-size: 11.5px; color: var(--color-text-muted); }

.auth-form {
  padding: 28px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.status-block {
  padding: 36px 28px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  text-align: center;
}

.form-heading { font-size: 16px; font-weight: 600; color: var(--color-text-base); margin: 0; }
.form-hint { font-size: 12.5px; color: var(--color-text-muted); margin-top: -4px; }
.form-group { display: flex; flex-direction: column; gap: 5px; }
.form-label { font-size: 11.5px; font-weight: 500; color: var(--color-text-muted); }

.pw-wrap { position: relative; display: flex; }
.pw-wrap .form-input { padding-right: 52px; flex: 1; }
.pw-toggle {
  position: absolute; right: 10px; top: 50%;
  transform: translateY(-50%);
  background: none; border: none; font-size: 12px; font-weight: 500;
  color: var(--color-accent); cursor: pointer; padding: 0; font-family: inherit;
}
.pw-toggle:hover { text-decoration: underline; }

.strength-bar-wrap { display: flex; align-items: center; gap: 8px; margin-top: 4px; }
.strength-bar { flex: 1; height: 4px; background: var(--color-border); border-radius: 2px; overflow: hidden; }
.strength-fill { height: 100%; border-radius: 2px; transition: width 0.2s ease, background 0.2s ease; }
.strength-weak { background: #dc2626; color: #dc2626; }
.strength-fair { background: #f59e0b; color: #b45309; }
.strength-strong { background: #16a34a; color: #15803d; }
.strength-label { font-size: 11px; font-weight: 600; white-space: nowrap; }

.auth-error {
  padding: 10px 12px;
  background: var(--color-error-bg);
  border: 1px solid var(--color-error-border);
  border-radius: 6px;
  font-size: 13px;
  color: #b91c1c;
}

.auth-submit { height: 38px; font-size: 14px; display: flex; align-items: center; justify-content: center; }

.auth-footer { text-align: center; font-size: 13px; margin: 0; }

.status-icon { width: 52px; height: 52px; }
.status-icon.success { color: #16a34a; }
.status-icon.error { color: #dc2626; }
.status-title { font-size: 15px; font-weight: 600; color: var(--color-text-base); margin: 0; }
.status-sub { font-size: 13px; color: var(--color-text-muted); margin: 0; max-width: 320px; }

.link-btn {
  background: none; border: none; padding: 0;
  font-size: 13px; color: var(--color-accent);
  cursor: pointer; font-family: inherit; font-weight: 500;
  text-decoration: none;
}
.link-btn:hover { text-decoration: underline; }

.spin-icon {
  width: 16px; height: 16px;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
  margin-right: 6px;
}
@keyframes spin { to { transform: rotate(360deg); } }

.w-full { width: 100%; }
</style>
