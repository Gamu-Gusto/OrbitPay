<template>
  <div class="register-container">
    <div class="register-card">
      <div class="register-header">
        <img src="/OrbitPayfinal.jpeg" alt="OrbitPay" class="register-logo" />
        <p class="register-subtitle">Create a new account</p>
      </div>
      <div class="register-form">
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Email</label>
            <input v-model="form.email" type="email" class="form-input" placeholder="Enter email" />
          </div>
          <div class="form-group">
            <label class="form-label">Password</label>
            <input v-model="form.password" type="password" class="form-input" maxlength="72" placeholder="Min 8 characters" />
            <p v-if="form.password.length > 72" class="error-text">Password must be 72 characters or less</p>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">First Name</label>
            <input v-model="form.first_name" type="text" class="form-input" placeholder="Enter first name" />
          </div>
          <div class="form-group">
            <label class="form-label">Last Name</label>
            <input v-model="form.last_name" type="text" class="form-input" placeholder="Enter last name" />
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Role</label>
          <select v-model="form.role" class="form-input">
            <option value="super_admin">Super Admin</option>
            <option value="accountant">Accountant</option>
            <option value="employee">Employee</option>
          </select>
        </div>
        <div class="form-group" v-if="form.role === 'employee'">
          <label class="form-label">Company (optional for employee)</label>
          <select v-model.number="form.company_id" class="form-input">
            <option :value="0">Select company</option>
            <option v-for="c in companies" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
        <div class="form-group" v-if="form.role === 'employee' && employees.length">
          <label class="form-label">Link to Employee (optional)</label>
          <select v-model.number="form.employee_id" class="form-input">
            <option :value="0">Select employee</option>
            <option v-for="e in employees" :key="e.id" :value="e.id">{{ e.first_names }} {{ e.last_name }}</option>
          </select>
        </div>
        <button @click="register" :disabled="loading || form.password.length > 72" class="btn-primary w-full">{{ loading ? 'Creating...' : 'Create account' }}</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f172a 0%, #1a2744 60%, #1e3a5f 100%);
  padding: 24px;
}

.register-card {
  background: #fff;
  border-radius: 16px;
  width: 100%;
  max-width: 500px;
  box-shadow: 0 24px 64px rgba(0,0,0,0.25);
  overflow: hidden;
}

.register-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 24px 28px 18px;
  border-bottom: 1px solid var(--color-border);
  background: #fafbfd;
}

.register-logo {
  height: 48px;
  width: auto;
}

.register-subtitle {
  font-size: 11.5px;
  color: var(--color-text-muted);
  margin: 0;
}

.register-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 24px 28px 28px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.error-text {
  font-size: 11px;
  color: var(--color-error);
}

.w-full { width: 100%; }

@media (max-width: 540px) {
  .form-row { grid-template-columns: 1fr; }
  .register-card { border-radius: 12px; }
}
</style>

<script>
import { reactive, ref, watch, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'RegisterView',
  setup() {
    const API = ''
    const companies = ref([])
    const employees = ref([])
    const loading = ref(false)
    const form = reactive({ email: '', password: '', first_name: '', last_name: '', role: 'accountant', company_id: 0, employee_id: 0 })

    const loadCompanies = async () => {
      try { const { data } = await axios.get(`${API}/companies`) ; companies.value = data } catch {}
    }
    const loadEmployees = async () => {
      employees.value = []
      if (form.company_id) {
        try { const { data } = await axios.get(`${API}/companies/${form.company_id}/employees`); employees.value = data } catch {}
      }
    }
    watch(() => form.company_id, loadEmployees)

    const register = async () => {
      if (form.password.length > 64) {
        alert('Password must be 64 characters or less for security reasons')
        return
      }
      if (form.password.length < 8) {
        alert('Password must be at least 8 characters long')
        return
      }

      loading.value = true
      try {
        const body = { ...form, role: String(form.role || '').toLowerCase(), company_id: form.company_id || undefined, employee_id: form.employee_id || undefined }
        await axios.post(`${API}/auth/register`, body)
        alert('Account created. You can now log in.')
        window.location.href = '/login'
      } catch (e) {
        const detail = e?.response?.data?.detail || e?.message || 'Registration failed'
        alert(detail)
      } finally { loading.value = false }
    }

    onMounted(loadCompanies)
    return { form, companies, employees, loading, register }
  }
}
</script>


