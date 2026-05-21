<template>
  <div class="page-content">

    <div class="page-header">
      <div>
        <h1 class="page-title">User Management</h1>
        <div class="breadcrumb">
          <span>Admin</span><span class="sep">/</span><span>Users</span>
        </div>
      </div>
      <button @click="showCreateForm = !showCreateForm" class="btn-primary">
        {{ showCreateForm ? 'Cancel' : '+ New User' }}
      </button>
    </div>

    <!-- Create user form -->
    <div v-if="showCreateForm" class="card create-form">
      <h3 class="card-section-title">Create User</h3>

      <div class="form-row">
        <div class="form-group">
          <label class="form-label">First Name</label>
          <input v-model="newUser.first_name" type="text" class="form-input" placeholder="Jane" />
        </div>
        <div class="form-group">
          <label class="form-label">Last Name</label>
          <input v-model="newUser.last_name" type="text" class="form-input" placeholder="Smith" />
        </div>
        <div class="form-group">
          <label class="form-label">Email Address</label>
          <input v-model="newUser.email" type="email" class="form-input" placeholder="jane@example.com" />
        </div>
        <div class="form-group">
          <label class="form-label">Role</label>
          <select v-model="newUser.role" class="form-input">
            <option value="">Select role</option>
            <option value="accountant">Accountant</option>
            <option value="manager">Manager</option>
            <option value="super_admin">Super Admin</option>
          </select>
        </div>
      </div>

      <!-- Password fields — only for super_admin -->
      <template v-if="newUser.role === 'super_admin'">
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Password</label>
            <div class="pw-wrap">
              <input v-model="newUser.password" :type="showNewPw ? 'text' : 'password'" class="form-input" placeholder="Min. 8 characters" />
              <button type="button" class="pw-toggle" @click="showNewPw = !showNewPw">{{ showNewPw ? 'Hide' : 'Show' }}</button>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Confirm Password</label>
            <input v-model="newUser.confirm_password" :type="showNewPw ? 'text' : 'password'" class="form-input" placeholder="Repeat password" />
          </div>
        </div>
        <p class="role-hint">Super Admin accounts are activated immediately. A welcome email with credentials will be sent.</p>
      </template>
      <template v-else-if="newUser.role">
        <p class="role-hint">An activation email will be sent to the user. They will set their own password when activating.</p>
      </template>

      <div v-if="createError" class="form-error-box">{{ createError }}</div>
      <div v-if="createSuccess" class="form-success-box">{{ createSuccess }}</div>

      <div class="form-actions">
        <button @click="createUser" :disabled="creating" class="btn-primary">
          {{ creating ? 'Creating…' : 'Create User' }}
        </button>
      </div>
    </div>

    <!-- User list -->
    <div class="card">
      <div v-if="loadingUsers" class="loading-state">
        <div class="spinner"></div>
        <span>Loading users…</span>
      </div>

      <div v-else-if="users.length === 0" class="empty-state">No users found.</div>

      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td class="name-cell">{{ u.first_name }} {{ u.last_name }}</td>
              <td>{{ u.email }}</td>
              <td>
                <span v-for="r in u.roles" :key="r" class="role-badge">{{ formatRole(r) }}</span>
              </td>
              <td>
                <span v-if="u.is_active" class="badge badge-green">Active</span>
                <span v-else class="badge badge-yellow">Pending activation</span>
              </td>
              <td class="action-cell">
                <button
                  v-if="!u.is_active && !isSuperAdmin(u)"
                  @click="resendInvitation(u)"
                  :disabled="resending === u.id"
                  class="btn-light btn-sm"
                >
                  {{ resending === u.id ? 'Sending…' : 'Resend invitation' }}
                </button>
                <span v-if="resendResult[u.id]" class="resend-result" :class="resendResult[u.id].ok ? 'result-ok' : 'result-err'">
                  {{ resendResult[u.id].msg }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'UserManagementView',
  setup() {
    const users = ref([])
    const loadingUsers = ref(true)
    const showCreateForm = ref(false)
    const creating = ref(false)
    const createError = ref('')
    const createSuccess = ref('')
    const showNewPw = ref(false)
    const resending = ref(null)
    const resendResult = reactive({})

    const newUser = reactive({
      first_name: '',
      last_name: '',
      email: '',
      role: '',
      password: '',
      confirm_password: '',
    })

    const resetForm = () => {
      newUser.first_name = ''
      newUser.last_name = ''
      newUser.email = ''
      newUser.role = ''
      newUser.password = ''
      newUser.confirm_password = ''
      createError.value = ''
      createSuccess.value = ''
    }

    const loadUsers = async () => {
      loadingUsers.value = true
      try {
        const { data } = await axios.get('/users')
        users.value = data || []
      } catch {
        users.value = []
      } finally {
        loadingUsers.value = false
      }
    }

    const createUser = async () => {
      createError.value = ''
      createSuccess.value = ''
      if (!newUser.first_name || !newUser.last_name || !newUser.email || !newUser.role) {
        createError.value = 'First name, last name, email, and role are required.'
        return
      }
      if (newUser.role === 'super_admin') {
        if (!newUser.password || !newUser.confirm_password) {
          createError.value = 'Password is required for Super Admin accounts.'
          return
        }
        if (newUser.password !== newUser.confirm_password) {
          createError.value = 'Passwords do not match.'
          return
        }
      }
      creating.value = true
      try {
        const payload = {
          first_name: newUser.first_name,
          last_name: newUser.last_name,
          email: newUser.email,
          role: newUser.role,
        }
        if (newUser.role === 'super_admin') {
          payload.password = newUser.password
          payload.confirm_password = newUser.confirm_password
        }
        await axios.post('/users', payload)
        createSuccess.value = newUser.role === 'super_admin'
          ? 'Super Admin created. A welcome email has been sent.'
          : `Invitation sent to ${newUser.email}. The user will receive an activation link.`
        resetForm()
        await loadUsers()
      } catch (e) {
        createError.value = e?.response?.data?.detail || 'Failed to create user.'
      } finally {
        creating.value = false
      }
    }

    const resendInvitation = async (user) => {
      resending.value = user.id
      delete resendResult[user.id]
      try {
        await axios.post(`/users/${user.id}/resend-activation`)
        resendResult[user.id] = { ok: true, msg: 'Invitation resent.' }
      } catch (e) {
        resendResult[user.id] = { ok: false, msg: e?.response?.data?.detail || 'Failed to resend.' }
      } finally {
        resending.value = null
      }
    }

    const formatRole = (r) => {
      const map = { super_admin: 'Super Admin', accountant: 'Accountant', manager: 'Manager', employee: 'Employee' }
      return map[r] || r
    }

    const isSuperAdmin = (u) => u.roles?.includes('super_admin')

    onMounted(loadUsers)

    return {
      users, loadingUsers, showCreateForm,
      newUser, creating, createError, createSuccess, showNewPw,
      resending, resendResult,
      createUser, resendInvitation, formatRole, isSuperAdmin,
    }
  }
}
</script>

<style scoped>
.page-content {
  padding: 24px;
  max-width: 1000px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.page-title { font-size: 16px; font-weight: 500; color: var(--color-text-base); margin: 0 0 4px; }
.breadcrumb { font-size: 11px; color: var(--color-text-muted); }
.sep { margin: 0 6px; }

.card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 20px;
}

.create-form { display: flex; flex-direction: column; gap: 16px; }

.card-section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-base);
  margin: 0;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 14px;
}

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

.role-hint { font-size: 12px; color: var(--color-text-muted); margin: 0; }

.form-error-box {
  padding: 10px 12px;
  background: var(--color-error-bg);
  border: 1px solid var(--color-error-border);
  border-radius: 6px;
  font-size: 13px;
  color: #b91c1c;
}

.form-success-box {
  padding: 10px 12px;
  background: #dcfce7;
  border: 1px solid #86efac;
  border-radius: 6px;
  font-size: 13px;
  color: #15803d;
}

.form-actions { display: flex; justify-content: flex-end; }

.loading-state {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--color-text-muted);
  font-size: 13px;
  padding: 16px 0;
}

.spinner {
  width: 18px; height: 18px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.empty-state { font-size: 13px; color: var(--color-text-muted); padding: 24px 0; text-align: center; }

.table-wrap { overflow-x: auto; }

.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }

.data-table th {
  text-align: left;
  padding: 10px 14px;
  font-size: 11px; font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase; letter-spacing: 0.04em;
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}

.data-table td {
  padding: 10px 14px;
  color: var(--color-text-base);
  border-bottom: 1px solid var(--color-border);
}

.data-table tbody tr:last-child td { border-bottom: none; }
.data-table tbody tr:hover td { background: var(--color-bg-page); }

.name-cell { font-weight: 500; }

.badge {
  display: inline-block;
  padding: 2px 9px;
  border-radius: 10px;
  font-size: 11px; font-weight: 600;
}
.badge-green { background: #dcfce7; color: #15803d; }
.badge-yellow { background: #fef9c3; color: #854d0e; }

.role-badge {
  display: inline-block;
  padding: 1px 7px;
  border-radius: 8px;
  font-size: 11px; font-weight: 500;
  background: var(--color-bg-page);
  color: var(--color-text-muted);
  margin-right: 4px;
}

.action-cell { white-space: nowrap; }

.btn-sm { padding: 4px 12px; font-size: 12px; }

.resend-result { font-size: 12px; margin-left: 8px; }
.result-ok { color: #15803d; }
.result-err { color: #dc2626; }
</style>
