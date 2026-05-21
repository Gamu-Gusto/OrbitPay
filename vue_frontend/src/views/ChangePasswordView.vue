<template>
  <div class="page-wrapper" style="max-width:480px;margin:40px auto">
    <div class="card" style="padding:28px">
      <h1 class="page-title" style="margin-bottom:4px">Change Password</h1>
      <p style="font-size:13px;color:var(--color-text-muted);margin-bottom:24px">
        Choose a strong password you haven't used before.
      </p>

      <div class="form-group" style="margin-bottom:16px">
        <label class="form-label">Current Password</label>
        <input v-model="current" type="password" class="form-input" placeholder="••••••••" autocomplete="current-password" @keydown.enter="submit" />
      </div>

      <div class="form-group" style="margin-bottom:16px">
        <label class="form-label">New Password</label>
        <div class="pw-wrap">
          <input v-model="newPw" :type="show ? 'text' : 'password'" class="form-input" placeholder="Min 8 characters" autocomplete="new-password" @keydown.enter="submit" />
          <button type="button" class="pw-toggle" @click="show = !show">{{ show ? 'Hide' : 'Show' }}</button>
        </div>
      </div>

      <div class="form-group" style="margin-bottom:24px">
        <label class="form-label">Confirm New Password</label>
        <input v-model="confirm" :type="show ? 'text' : 'password'" class="form-input" placeholder="Repeat new password" autocomplete="new-password" @keydown.enter="submit" />
      </div>

      <div v-if="errorMsg" class="alert-error" style="margin-bottom:16px">{{ errorMsg }}</div>
      <div v-if="successMsg" class="alert-success" style="margin-bottom:16px">{{ successMsg }}</div>

      <div class="flex items-center gap-2" style="justify-content:flex-end">
        <button @click="goBack" class="btn-secondary">Cancel</button>
        <button @click="submit" :disabled="loading" class="btn-primary">
          {{ loading ? 'Saving…' : 'Update Password' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'
import { useRouter } from 'vue-router'

export default {
  name: 'ChangePasswordView',
  setup() {
    const auth    = useAuthStore()
    const toast   = useToastStore()
    const router  = useRouter()

    const current    = ref('')
    const newPw      = ref('')
    const confirm    = ref('')
    const show       = ref(false)
    const loading    = ref(false)
    const errorMsg   = ref('')
    const successMsg = ref('')

    const isEmployeeOnly = auth.roles.includes('employee') &&
      !auth.roles.some(r => ['super_admin', 'accountant'].includes(r))

    const goBack = () => router.push(isEmployeeOnly ? '/portal' : '/')

    const submit = async () => {
      errorMsg.value = ''
      successMsg.value = ''
      if (!current.value || !newPw.value || !confirm.value) {
        errorMsg.value = 'All fields are required.'
        return
      }
      if (newPw.value.length < 8) {
        errorMsg.value = 'New password must be at least 8 characters.'
        return
      }
      if (newPw.value !== confirm.value) {
        errorMsg.value = 'New passwords do not match.'
        return
      }
      loading.value = true
      try {
        await axios.post('/auth/change-password',
          { current_password: current.value, new_password: newPw.value },
          { headers: { Authorization: `Bearer ${auth.accessToken}` } }
        )
        // Refresh auth so force_password_change flag clears
        await auth.initializeAuth()
        toast.success('Password updated successfully.')
        router.push(isEmployeeOnly ? '/portal' : '/')
      } catch (e) {
        errorMsg.value = e.response?.data?.detail || 'Failed to update password. Please try again.'
      } finally {
        loading.value = false
      }
    }

    return { current, newPw, confirm, show, loading, errorMsg, successMsg, submit, goBack }
  }
}
</script>

<style scoped>
.pw-wrap { position: relative; display: flex; }
.pw-wrap .form-input { padding-right: 52px; flex: 1; }
.pw-toggle {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-accent);
  cursor: pointer;
  padding: 0;
  font-family: inherit;
}
.pw-toggle:hover { text-decoration: underline; }

.alert-error {
  padding: 10px 12px;
  background: var(--color-error-bg);
  border: 1px solid var(--color-error-border);
  border-radius: 6px;
  font-size: 13px;
  color: #b91c1c;
}
.alert-success {
  padding: 10px 12px;
  background: #dcfce7;
  border: 1px solid #86efac;
  border-radius: 6px;
  font-size: 13px;
  color: #15803d;
}
</style>
