<template>
  <div class="setup-page">
    <div class="setup-card">

      <div class="setup-brand">
        <img src="/OrbitPayfinal.jpeg" alt="OrbitPay" class="setup-logo" />
        <p class="brand-tagline">Payroll &amp; Reports Platform</p>
      </div>

      <!-- Already configured -->
      <div v-if="alreadyDone" class="setup-done">
        <svg class="done-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/><polyline points="9 12 11 14 15 10"/>
        </svg>
        <p class="done-title">System already configured</p>
        <p class="done-sub">A Super Admin account has already been created.</p>
        <router-link to="/login" class="btn-primary setup-btn">Go to Login</router-link>
      </div>

      <!-- Setup complete -->
      <div v-else-if="setupDone" class="setup-done">
        <svg class="done-icon success" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/><polyline points="9 12 11 14 15 10"/>
        </svg>
        <p class="done-title">Setup complete!</p>
        <p class="done-sub">Your Super Admin account has been created. You can now sign in.</p>
        <router-link to="/login" class="btn-primary setup-btn">Go to Login</router-link>
      </div>

      <!-- Setup form -->
      <div v-else class="setup-form">
        <h2 class="form-heading">First-run Setup</h2>
        <p class="form-hint">Create the initial Super Admin account. This can only be done once.</p>

        <div class="form-group">
          <label class="form-label">Full Name</label>
          <input v-model="form.full_name" type="text" class="form-input" placeholder="Jane Smith" autocomplete="name" @keydown.enter="submit" />
        </div>

        <div class="form-group">
          <label class="form-label">Email Address</label>
          <input v-model="form.email" type="email" class="form-input" placeholder="admin@example.com" autocomplete="email" @keydown.enter="submit" />
        </div>

        <div class="form-group">
          <label class="form-label">Password</label>
          <div class="pw-wrap">
            <input v-model="form.password" :type="showPw ? 'text' : 'password'" class="form-input" placeholder="Min. 8 characters" autocomplete="new-password" @keydown.enter="submit" />
            <button type="button" class="pw-toggle" @click="showPw = !showPw">{{ showPw ? 'Hide' : 'Show' }}</button>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Confirm Password</label>
          <input v-model="form.confirm_password" :type="showPw ? 'text' : 'password'" class="form-input" placeholder="Repeat password" autocomplete="new-password" @keydown.enter="submit" />
        </div>

        <div class="form-group">
          <label class="form-label">Setup Secret Key</label>
          <div class="pw-wrap">
            <input v-model="form.secret" :type="showSecret ? 'text' : 'password'" class="form-input" placeholder="Provided by system administrator" @keydown.enter="submit" />
            <button type="button" class="pw-toggle" @click="showSecret = !showSecret">{{ showSecret ? 'Hide' : 'Show' }}</button>
          </div>
          <p class="field-hint">The value of ADMIN_SETUP_SECRET from your server environment.</p>
        </div>

        <div v-if="errorMsg" class="form-error-box">{{ errorMsg }}</div>

        <button @click="submit" :disabled="loading" class="btn-primary w-full setup-btn">
          <svg v-if="loading" class="spin-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
            <path d="M12 2a10 10 0 0110 10" stroke-linecap="round"/>
          </svg>
          {{ loading ? 'Creating account…' : 'Create Super Admin' }}
        </button>
      </div>

    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'AdminSetupView',
  setup() {
    const alreadyDone = ref(false)
    const setupDone = ref(false)
    const loading = ref(false)
    const errorMsg = ref('')
    const showPw = ref(false)
    const showSecret = ref(false)

    const form = reactive({
      full_name: '',
      email: '',
      password: '',
      confirm_password: '',
      secret: '',
    })

    onMounted(async () => {
      try {
        const { data } = await axios.get('/auth/admin/setup-status')
        if (data.setup_complete) alreadyDone.value = true
      } catch {}
    })

    const submit = async () => {
      errorMsg.value = ''
      if (!form.full_name || !form.email || !form.password || !form.confirm_password || !form.secret) {
        errorMsg.value = 'All fields are required.'
        return
      }
      if (form.password !== form.confirm_password) {
        errorMsg.value = 'Passwords do not match.'
        return
      }
      if (form.password.length < 8) {
        errorMsg.value = 'Password must be at least 8 characters.'
        return
      }
      loading.value = true
      try {
        await axios.post('/auth/admin/setup', {
          full_name: form.full_name,
          email: form.email,
          password: form.password,
          confirm_password: form.confirm_password,
        }, {
          headers: { 'X-Setup-Secret': form.secret }
        })
        setupDone.value = true
      } catch (e) {
        const status = e?.response?.status
        const detail = e?.response?.data?.detail
        if (status === 403) {
          errorMsg.value = 'Invalid setup secret key.'
        } else if (status === 410) {
          alreadyDone.value = true
        } else {
          errorMsg.value = detail || 'Setup failed. Please try again.'
        }
      } finally {
        loading.value = false
      }
    }

    return { alreadyDone, setupDone, loading, errorMsg, showPw, showSecret, form, submit }
  }
}
</script>

<style scoped>
.setup-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f172a 0%, #1a2744 60%, #1e3a5f 100%);
  padding: 24px;
}

.setup-card {
  background: #fff;
  border-radius: 16px;
  width: 100%;
  max-width: 440px;
  box-shadow: 0 24px 64px rgba(0,0,0,0.25);
  overflow: hidden;
}

.setup-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 28px 28px 20px;
  border-bottom: 1px solid var(--color-border);
  background: #fafbfd;
}

.setup-logo { height: 52px; width: auto; }
.brand-tagline { font-size: 11.5px; color: var(--color-text-muted); }

.setup-form, .setup-done {
  padding: 28px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.setup-done {
  align-items: center;
  text-align: center;
  gap: 10px;
}

.form-heading {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-base);
  margin-bottom: 0;
}

.form-hint { font-size: 12.5px; color: var(--color-text-muted); margin-top: -4px; }
.form-group { display: flex; flex-direction: column; gap: 5px; }
.form-label { font-size: 11.5px; font-weight: 500; color: var(--color-text-muted); }
.field-hint { font-size: 11px; color: var(--color-text-muted); margin: 0; }

.pw-wrap { position: relative; display: flex; }
.pw-wrap .form-input { padding-right: 52px; flex: 1; }
.pw-toggle {
  position: absolute; right: 10px; top: 50%;
  transform: translateY(-50%);
  background: none; border: none; font-size: 12px; font-weight: 500;
  color: var(--color-accent); cursor: pointer; padding: 0; font-family: inherit;
}
.pw-toggle:hover { text-decoration: underline; }

.form-error-box {
  padding: 10px 12px;
  background: var(--color-error-bg);
  border: 1px solid var(--color-error-border);
  border-radius: 6px;
  font-size: 13px;
  color: #b91c1c;
}

.setup-btn { height: 38px; font-size: 14px; margin-top: 4px; text-decoration: none; display: flex; align-items: center; justify-content: center; }

.done-icon {
  width: 48px; height: 48px;
  color: var(--color-text-muted);
  margin-bottom: 4px;
}
.done-icon.success { color: #16a34a; }

.done-title { font-size: 15px; font-weight: 600; color: var(--color-text-base); margin: 0; }
.done-sub { font-size: 13px; color: var(--color-text-muted); margin: 0; }

.spin-icon {
  width: 16px; height: 16px;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
  margin-right: 6px;
}
@keyframes spin { to { transform: rotate(360deg); } }

.w-full { width: 100%; }
</style>
