<template>
  <div class="view-content">

    <!-- Page Header -->
    <div class="page-header" style="margin-bottom:0">
      <div>
        <h1 class="page-title">Announcements</h1>
        <p class="page-subtitle">Manage company announcements visible to employees.</p>
      </div>
    </div>

    <!-- Company selector -->
    <div class="card card-sm">
      <div class="form-group" style="max-width:320px">
        <label class="form-label">Company</label>
        <select v-model="selectedCompanyId" @change="load" class="form-input">
          <option value="">Select a company…</option>
          <option v-for="c in companies" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </div>
    </div>

    <!-- No company selected -->
    <div v-if="!selectedCompanyId" class="card">
      <div class="empty-state">
        <p>Select a company above to manage its announcements.</p>
      </div>
    </div>

    <!-- Announcements list card -->
    <div v-else class="card" style="padding:0;overflow:hidden">
      <!-- List header -->
      <div class="card-header" style="padding:16px 20px;margin-bottom:0">
        <span class="card-title">
          {{ announcements.length }} announcement{{ announcements.length !== 1 ? 's' : '' }}
        </span>
        <button @click="openCreate" class="btn btn-primary btn-sm">+ New Announcement</button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="loading-state" style="padding:32px 20px">
        <div class="spinner"></div>
        Loading…
      </div>

      <!-- Empty -->
      <div v-else-if="announcements.length === 0" class="empty-state" style="padding:48px 24px">
        <p>No announcements yet. Click "New Announcement" to create one.</p>
      </div>

      <!-- Announcement rows -->
      <div v-else class="ann-list">
        <div v-for="a in announcements" :key="a.id" class="ann-row">
          <div class="ann-meta">
            <span class="ann-title">{{ a.title }}</span>
            <span class="badge" :class="a.is_active ? 'badge-success' : 'badge-neutral'">
              {{ a.is_active ? 'Active' : 'Inactive' }}
            </span>
          </div>
          <p class="ann-preview">{{ a.body.slice(0, 120) }}{{ a.body.length > 120 ? '…' : '' }}</p>
          <div class="ann-footer">
            <span class="ann-date">{{ fmtDate(a.created_at) }}</span>
            <div style="display:flex;gap:8px">
              <button @click="openEdit(a)" class="btn btn-light btn-sm">Edit</button>
              <button @click="confirmDelete(a)" class="btn btn-danger btn-sm">Delete</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create / Edit modal -->
    <teleport to="body">
      <div v-if="showForm" class="modal-overlay" @click.self="closeForm">
        <div class="modal modal-wide" role="dialog">
          <div class="modal-header">
            <h2>{{ editing ? 'Edit Announcement' : 'New Announcement' }}</h2>
            <button @click="closeForm" class="modal-close" aria-label="Close">✕</button>
          </div>
          <div class="modal-body">
            <div class="form-grid">
              <div class="form-group span-2">
                <label class="form-label">Title *</label>
                <input
                  v-model="form.title"
                  type="text"
                  class="form-input"
                  placeholder="Announcement title"
                  maxlength="255"
                />
              </div>
              <div class="form-group span-2">
                <label class="form-label">Body *</label>
                <textarea
                  v-model="form.body"
                  class="form-input"
                  rows="6"
                  placeholder="Announcement content…"
                  style="resize:vertical"
                ></textarea>
              </div>
              <div class="form-group span-2">
                <label class="form-label" style="display:flex;align-items:center;gap:8px;cursor:pointer;flex-direction:row">
                  <input type="checkbox" v-model="form.is_active" style="width:15px;height:15px;flex-shrink:0" />
                  Active (visible to employees)
                </label>
              </div>
            </div>
            <div v-if="formError" class="form-error" style="margin-top:10px">{{ formError }}</div>
          </div>
          <div class="modal-footer">
            <button @click="closeForm" class="btn btn-light">Cancel</button>
            <button
              @click="save"
              :disabled="saving || !form.title || !form.body"
              class="btn btn-primary"
            >
              {{ saving ? 'Saving…' : (editing ? 'Save Changes' : 'Create') }}
            </button>
          </div>
        </div>
      </div>
    </teleport>

    <!-- Delete confirmation modal -->
    <teleport to="body">
      <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
        <div class="modal modal-narrow" role="dialog">
          <div class="modal-header">
            <h2>Delete Announcement</h2>
            <button @click="deleteTarget = null" class="modal-close" aria-label="Close">✕</button>
          </div>
          <div class="modal-body">
            <p style="font-size:13px;color:var(--color-text-base);line-height:1.6">
              Are you sure you want to delete <strong>{{ deleteTarget.title }}</strong>? This cannot be undone.
            </p>
          </div>
          <div class="modal-footer">
            <button @click="deleteTarget = null" class="btn btn-light">Cancel</button>
            <button @click="doDelete" :disabled="deleting" class="btn btn-danger">
              {{ deleting ? 'Deleting…' : 'Delete' }}
            </button>
          </div>
        </div>
      </div>
    </teleport>

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
.view-content {
  padding: 24px;
  max-width: 860px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Announcement list rows */
.ann-list {
  display: flex;
  flex-direction: column;
}

.ann-row {
  padding: 14px 20px;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.ann-row:last-child { border-bottom: none; }

.ann-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ann-title {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--color-text-base);
}

.ann-preview {
  font-size: 12.5px;
  color: var(--color-text-muted);
  margin: 0;
  line-height: 1.5;
}

.ann-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.ann-date {
  font-size: 11px;
  color: var(--color-text-muted);
}

@media (max-width: 640px) {
  .view-content { padding: 16px; }
}
</style>
