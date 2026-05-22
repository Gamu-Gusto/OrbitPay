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

      <template v-if="newUser.role">
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
        <p class="role-hint">The account will be activated immediately. Provide these credentials directly to the user — no email is sent.</p>
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
                <span v-else class="badge badge-gray">Inactive</span>
              </td>
              <td class="action-cell">
                <button @click="openEditCreds(u)" class="btn-light btn-sm">Edit credentials</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Edit credentials modal -->
    <div v-if="editTarget" class="modal-overlay" @click.self="closeEditCreds">
      <div class="modal-card">
        <div class="modal-header">
          <h3 class="modal-title">Edit credentials — {{ editTarget.first_name }} {{ editTarget.last_name }}</h3>
          <button class="modal-close" @click="closeEditCreds">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">New Email (leave blank to keep current)</label>
            <input v-model="editCreds.email" type="email" class="form-input" :placeholder="editTarget.email" />
          </div>
          <div class="form-group">
            <label class="form-label">New Password (leave blank to keep current)</label>
            <div class="pw-wrap">
              <input v-model="editCreds.password" :type="showEditPw ? 'text' : 'password'" class="form-input" placeholder="Min. 8 characters" />
              <button type="button" class="pw-toggle" @click="showEditPw = !showEditPw">{{ showEditPw ? 'Hide' : 'Show' }}</button>
            </div>
          </div>
          <div v-if="editError" class="form-error-box">{{ editError }}</div>
          <div v-if="editSuccess" class="form-success-box">{{ editSuccess }}</div>
        </div>
        <div class="modal-footer">
          <button class="btn-light" @click="closeEditCreds">Cancel</button>
          <button class="btn-primary" @click="saveEditCreds" :disabled="editSaving">
            {{ editSaving ? 'Saving…' : 'Save' }}
          </button>
        </div>
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

    const newUser = reactive({
      first_name: '',
      last_name: '',
      email: '',
      role: '',
      password: '',
      confirm_password: '',
    })

    // Edit credentials state
    const editTarget = ref(null)
    const editCreds = reactive({ email: '', password: '' })
    const showEditPw = ref(false)
    const editSaving = ref(false)
    const editError = ref('')
    const editSuccess = ref('')

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
      if (!newUser.password || !newUser.confirm_password) {
        createError.value = 'Password is required.'
        return
      }
      if (newUser.password !== newUser.confirm_password) {
        createError.value = 'Passwords do not match.'
        return
      }
      creating.value = true
      try {
        await axios.post('/users', {
          first_name: newUser.first_name,
          last_name: newUser.last_name,
          email: newUser.email,
          role: newUser.role,
          password: newUser.password,
          confirm_password: newUser.confirm_password,
        })
        createSuccess.value = `User created. Provide the credentials directly to ${newUser.email}.`
        resetForm()
        await loadUsers()
      } catch (e) {
        createError.value = e?.response?.data?.detail || 'Failed to create user.'
      } finally {
        creating.value = false
      }
    }

    const openEditCreds = (u) => {
      editTarget.value = u
      editCreds.email = ''
      editCreds.password = ''
      editError.value = ''
      editSuccess.value = ''
      showEditPw.value = false
    }

    const closeEditCreds = () => {
      editTarget.value = null
    }

    const saveEditCreds = async () => {
      editError.value = ''
      editSuccess.value = ''
      if (!editCreds.email && !editCreds.password) {
        editError.value = 'Enter a new email or password to update.'
        return
      }
      editSaving.value = true
      try {
        const payload = {}
        if (editCreds.email) payload.email = editCreds.email
        if (editCreds.password) payload.password = editCreds.password
        await axios.patch(`/users/${editTarget.value.id}`, payload)
        editSuccess.value = 'Credentials updated successfully.'
        await loadUsers()
        const updated = users.value.find(u => u.id === editTarget.value.id)
        if (updated) editTarget.value = updated
      } catch (e) {
        editError.value = e?.response?.data?.detail || 'Failed to update credentials.'
      } finally {
        editSaving.value = false
      }
    }

    const formatRole = (r) => {
      const map = { super_admin: 'Super Admin', accountant: 'Accountant', manager: 'Manager', employee: 'Employee' }
      return map[r] || r
    }

    onMounted(loadUsers)

    return {
      users, loadingUsers, showCreateForm,
      newUser, creating, createError, createSuccess, showNewPw,
      editTarget, editCreds, showEditPw, editSaving, editError, editSuccess,
      createUser, openEditCreds, closeEditCreds, saveEditCreds, formatRole,
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
.badge-gray { background: var(--color-bg-page); color: var(--color-text-muted); }

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

/* Modal */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center;
  z-index: 500;
}

.modal-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  width: 440px;
  max-width: 95vw;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0,0,0,0.18);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border);
}

.modal-title { font-size: 14px; font-weight: 600; color: var(--color-text-base); margin: 0; }

.modal-close {
  background: none; border: none; font-size: 16px;
  color: var(--color-text-muted); cursor: pointer; padding: 2px 4px; line-height: 1;
}
.modal-close:hover { color: var(--color-text-base); }

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid var(--color-border);
}
</style>
