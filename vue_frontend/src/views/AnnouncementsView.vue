<template>
  <div class="page-wrap">

    <div class="page-header">
      <div>
        <h1 class="page-title">Announcements</h1>
        <p class="page-sub">Manage company announcements visible to employees.</p>
      </div>
    </div>

    <!-- Company selector (super_admin sees all, accountant sees assigned) -->
    <div class="card filter-bar">
      <div class="form-group">
        <label class="form-label">Company</label>
        <select v-model="selectedCompanyId" @change="load" class="form-input" style="max-width:300px">
          <option value="">Select a company…</option>
          <option v-for="c in companies" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </div>
    </div>

    <div v-if="selectedCompanyId" class="main-layout">

      <!-- Announcement list -->
      <div class="card list-card">
        <div class="list-header">
          <p class="list-title">{{ announcements.length }} announcement{{ announcements.length !== 1 ? 's' : '' }}</p>
          <button @click="openCreate" class="btn-primary btn-sm">+ New Announcement</button>
        </div>

        <div v-if="loading" class="loading-state">
          <div class="spinner"></div> Loading…
        </div>

        <div v-else-if="announcements.length === 0" class="empty-state">
          No announcements yet. Click "New Announcement" to create one.
        </div>

        <div v-else class="ann-list">
          <div v-for="a in announcements" :key="a.id" class="ann-row">
            <div class="ann-meta">
              <span class="ann-title">{{ a.title }}</span>
              <span class="badge" :class="a.is_active ? 'badge-green' : 'badge-gray'">
                {{ a.is_active ? 'Active' : 'Inactive' }}
              </span>
            </div>
            <p class="ann-body-preview">{{ a.body.slice(0, 100) }}{{ a.body.length > 100 ? '…' : '' }}</p>
            <div class="ann-footer">
              <span class="ann-date">{{ fmtDate(a.created_at) }}</span>
              <div class="ann-actions">
                <button @click="openEdit(a)" class="btn-light btn-sm">Edit</button>
                <button @click="confirmDelete(a)" class="btn-danger btn-sm">Delete</button>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>

    <div v-else class="card empty-state" style="padding:32px;text-align:center;color:var(--color-text-muted)">
      Select a company above to manage its announcements.
    </div>

    <!-- Create / Edit modal -->
    <div v-if="showForm" class="modal-overlay" @click.self="closeForm">
      <div class="modal-box">
        <div class="modal-header">
          <h2 class="modal-title">{{ editing ? 'Edit Announcement' : 'New Announcement' }}</h2>
          <button @click="closeForm" class="modal-close">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">Title *</label>
            <input v-model="form.title" type="text" class="form-input" placeholder="Announcement title" maxlength="255" />
          </div>
          <div class="form-group" style="margin-top:12px">
            <label class="form-label">Body *</label>
            <textarea v-model="form.body" class="form-input" rows="6" placeholder="Announcement content…" style="resize:vertical"></textarea>
          </div>
          <div class="form-group" style="margin-top:12px">
            <label class="form-label" style="display:flex;align-items:center;gap:8px;cursor:pointer">
              <input type="checkbox" v-model="form.is_active" style="width:16px;height:16px" />
              Active (visible to employees)
            </label>
          </div>
          <div v-if="formError" class="form-error" style="margin-top:10px">{{ formError }}</div>
        </div>
        <div class="modal-footer">
          <button @click="closeForm" class="btn-light">Cancel</button>
          <button @click="save" :disabled="saving || !form.title || !form.body" class="btn-primary">
            {{ saving ? 'Saving…' : (editing ? 'Save Changes' : 'Create') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Delete confirm modal -->
    <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
      <div class="modal-box" style="max-width:400px">
        <div class="modal-header">
          <h2 class="modal-title">Delete Announcement</h2>
          <button @click="deleteTarget = null" class="modal-close">✕</button>
        </div>
        <div class="modal-body">
          <p>Are you sure you want to delete <strong>{{ deleteTarget.title }}</strong>? This cannot be undone.</p>
        </div>
        <div class="modal-footer">
          <button @click="deleteTarget = null" class="btn-light">Cancel</button>
          <button @click="doDelete" :disabled="deleting" class="btn-danger">{{ deleting ? 'Deleting…' : 'Delete' }}</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'AnnouncementsView',
  setup() {
    const companies = ref([])
    const selectedCompanyId = ref('')
    const announcements = ref([])
    const loading = ref(false)

    const showForm = ref(false)
    const editing = ref(null)
    const form = reactive({ title: '', body: '', is_active: true })
    const saving = ref(false)
    const formError = ref('')

    const deleteTarget = ref(null)
    const deleting = ref(false)

    const loadCompanies = async () => {
      try {
        const { data } = await axios.get('/companies')
        companies.value = data || []
      } catch {}
    }

    const load = async () => {
      if (!selectedCompanyId.value) return
      loading.value = true
      try {
        const { data } = await axios.get('/announcements', { params: { company_id: selectedCompanyId.value } })
        announcements.value = data || []
      } catch {
        announcements.value = []
      } finally {
        loading.value = false
      }
    }

    const openCreate = () => {
      editing.value = null
      form.title = ''
      form.body = ''
      form.is_active = true
      formError.value = ''
      showForm.value = true
    }

    const openEdit = (a) => {
      editing.value = a
      form.title = a.title
      form.body = a.body
      form.is_active = a.is_active
      formError.value = ''
      showForm.value = true
    }

    const closeForm = () => { showForm.value = false; editing.value = null }

    const save = async () => {
      formError.value = ''
      saving.value = true
      try {
        if (editing.value) {
          await axios.patch(`/announcements/${editing.value.id}`, {
            title: form.title,
            body: form.body,
            is_active: form.is_active,
          })
        } else {
          await axios.post('/announcements', {
            company_id: selectedCompanyId.value,
            title: form.title,
            body: form.body,
            is_active: form.is_active,
          })
        }
        closeForm()
        await load()
      } catch (e) {
        formError.value = e?.response?.data?.detail || 'Failed to save.'
      } finally {
        saving.value = false
      }
    }

    const confirmDelete = (a) => { deleteTarget.value = a }

    const doDelete = async () => {
      deleting.value = true
      try {
        await axios.delete(`/announcements/${deleteTarget.value.id}`)
        deleteTarget.value = null
        await load()
      } catch {
        deleteTarget.value = null
      } finally {
        deleting.value = false
      }
    }

    const fmtDate = (s) => {
      if (!s) return '—'
      try { return new Date(s).toLocaleDateString('en-ZA', { year: 'numeric', month: 'short', day: '2-digit' }) }
      catch { return s }
    }

    onMounted(loadCompanies)

    return {
      companies, selectedCompanyId, announcements, loading,
      showForm, editing, form, saving, formError,
      deleteTarget, deleting,
      load, openCreate, openEdit, closeForm, save, confirmDelete, doDelete, fmtDate,
    }
  }
}
</script>

<style scoped>
.page-wrap { padding: 24px; max-width: 860px; display: flex; flex-direction: column; gap: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-title { font-size: 16px; font-weight: 600; color: var(--color-text-base); margin: 0 0 4px; }
.page-sub { font-size: 12px; color: var(--color-text-muted); margin: 0; }

.card { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 10px; padding: 20px; }
.filter-bar { padding: 16px 20px; }
.form-group { display: flex; flex-direction: column; gap: 5px; }
.form-label { font-size: 11.5px; font-weight: 500; color: var(--color-text-muted); }

.main-layout { display: flex; flex-direction: column; gap: 16px; }
.list-card { padding: 0; overflow: hidden; }
.list-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--color-border); }
.list-title { font-size: 13px; font-weight: 600; color: var(--color-text-base); margin: 0; }

.loading-state { display: flex; align-items: center; gap: 8px; padding: 24px 20px; color: var(--color-text-muted); font-size: 13px; }
.spinner { width: 16px; height: 16px; border: 2px solid var(--color-border); border-top-color: var(--color-accent); border-radius: 50%; animation: spin 0.8s linear infinite; flex-shrink: 0; }
@keyframes spin { to { transform: rotate(360deg); } }

.empty-state { padding: 24px 20px; font-size: 13px; color: var(--color-text-muted); text-align: center; }

.ann-list { display: flex; flex-direction: column; }
.ann-row { padding: 14px 20px; border-bottom: 1px solid var(--color-border); display: flex; flex-direction: column; gap: 6px; }
.ann-row:last-child { border-bottom: none; }
.ann-meta { display: flex; align-items: center; gap: 10px; }
.ann-title { font-size: 13.5px; font-weight: 600; color: var(--color-text-base); }
.ann-body-preview { font-size: 12.5px; color: var(--color-text-muted); margin: 0; line-height: 1.5; }
.ann-footer { display: flex; align-items: center; justify-content: space-between; }
.ann-date { font-size: 11px; color: var(--color-text-muted); }
.ann-actions { display: flex; gap: 8px; }

.badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.badge-green { background: #dcfce7; color: #15803d; }
.badge-gray { background: var(--color-bg-page); color: var(--color-text-muted); }

.btn-sm { padding: 4px 12px; font-size: 12px; }
.btn-danger { background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; border-radius: 7px; padding: 7px 16px; font-size: 13px; font-weight: 500; cursor: pointer; font-family: inherit; transition: background 0.12s; }
.btn-danger:hover { background: #fecaca; }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }
.form-error { font-size: 12px; color: #dc2626; }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.45); display: flex; align-items: center; justify-content: center; z-index: 500; padding: 20px; }
.modal-box { background: var(--color-bg-card); border-radius: 12px; width: 100%; max-width: 560px; box-shadow: 0 20px 60px rgba(0,0,0,0.25); display: flex; flex-direction: column; max-height: 90vh; overflow: hidden; }
.modal-header { display: flex; align-items: center; justify-content: space-between; padding: 18px 20px; border-bottom: 1px solid var(--color-border); flex-shrink: 0; }
.modal-title { font-size: 14px; font-weight: 600; color: var(--color-text-base); margin: 0; }
.modal-close { background: none; border: none; color: var(--color-text-muted); cursor: pointer; font-size: 16px; padding: 2px 6px; border-radius: 4px; }
.modal-close:hover { background: var(--color-bg-page); }
.modal-body { padding: 20px; overflow-y: auto; flex: 1; }
.modal-footer { display: flex; gap: 10px; justify-content: flex-end; padding: 16px 20px; border-top: 1px solid var(--color-border); flex-shrink: 0; }
</style>
