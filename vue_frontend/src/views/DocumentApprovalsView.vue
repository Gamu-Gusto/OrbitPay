<template>
  <div class="page-content">

    <div class="page-header">
      <div>
        <h1 class="page-title">Document Approvals</h1>
        <div class="breadcrumb"><span>Approvals</span><span class="sep">/</span><span>Documents</span></div>
      </div>
      <button @click="load" :disabled="loading" class="btn-secondary">
        {{ loading ? 'Loading…' : 'Refresh' }}
      </button>
    </div>

    <div v-if="loading" class="loading-state"><div class="spinner"></div><span>Loading pending documents…</span></div>

    <div v-else-if="docs.length === 0" class="card empty-state">No documents pending review.</div>

    <div v-else class="card">
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Employee</th>
              <th>Company</th>
              <th>Type</th>
              <th>File</th>
              <th>Size</th>
              <th>Uploaded</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="doc in docs" :key="doc.id">
              <td class="name-cell">{{ doc.uploaded_by_name || '—' }}</td>
              <td class="muted-text">{{ doc.company_name || '—' }}</td>
              <td>{{ doc.document_type }}</td>
              <td class="muted-text">{{ doc.file_name }}</td>
              <td class="muted-text">{{ fmtSize(doc.file_size) }}</td>
              <td class="muted-text">{{ fmtDate(doc.uploaded_at) }}</td>
              <td>
                <div class="action-cell">
                  <button @click="download(doc)" class="btn-light btn-sm">Download</button>
                  <button @click="approve(doc)" :disabled="doc._acting" class="btn-primary btn-sm">Approve</button>
                  <button @click="startReject(doc)" :disabled="doc._acting" class="btn-light btn-sm">Reject</button>
                </div>
                <div v-if="doc._rejecting" class="reject-inline">
                  <input v-model="doc._rejectNote" type="text" class="form-input reject-input" placeholder="Rejection reason…" />
                  <button @click="confirmReject(doc)" :disabled="doc._acting" class="btn-secondary btn-sm">Confirm</button>
                  <button @click="doc._rejecting = false" class="btn-light btn-sm">Cancel</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'DocumentApprovalsView',
  setup() {
    const loading = ref(false)
    const docs = ref([])

    const load = async () => {
      loading.value = true
      try {
        const { data } = await axios.get('/documents/pending')
        docs.value = (data || []).map(d => ({ ...d, _rejecting: false, _rejectNote: '', _acting: false }))
      } catch {}
      loading.value = false
    }

    const download = async (doc) => {
      try {
        const { data } = await axios.get(`/documents/${doc.id}/download`)
        const a = document.createElement('a')
        a.href = data.url
        a.setAttribute('download', doc.file_name)
        document.body.appendChild(a)
        a.click()
        a.remove()
      } catch { alert('Failed to download document.') }
    }

    const approve = async (doc) => {
      doc._acting = true
      try {
        await axios.patch(`/documents/${doc.id}/review`, { status: 'approved' })
        await load()
      } catch { doc._acting = false }
    }

    const startReject = (doc) => {
      docs.value.forEach(x => { x._rejecting = false })
      doc._rejecting = true
      doc._rejectNote = ''
    }

    const confirmReject = async (doc) => {
      doc._acting = true
      try {
        await axios.patch(`/documents/${doc.id}/review`, { status: 'rejected', reason: doc._rejectNote })
        await load()
      } catch { doc._acting = false; doc._rejecting = false }
    }

    const fmtDate = (s) => {
      if (!s) return '—'
      try { return new Date(s).toLocaleDateString('en-ZA', { year: 'numeric', month: 'short', day: '2-digit' }) }
      catch { return s }
    }

    const fmtSize = (bytes) => {
      if (!bytes) return '—'
      if (bytes < 1024) return bytes + ' B'
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
      return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
    }

    onMounted(load)
    return { loading, docs, load, download, approve, startReject, confirmReject, fmtDate, fmtSize }
  }
}
</script>

<style scoped>
.page-content { padding: 24px; max-width: 1200px; display: flex; flex-direction: column; gap: 24px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-title { font-size: 16px; font-weight: 500; color: var(--color-text-base); margin: 0 0 4px; }
.breadcrumb { font-size: 11px; color: var(--color-text-muted); }
.sep { margin: 0 6px; }

.loading-state { display: flex; align-items: center; gap: 10px; color: var(--color-text-muted); font-size: 13px; }
.spinner { width: 18px; height: 18px; border: 2px solid var(--color-border); border-top-color: var(--color-accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.card { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 10px; padding: 20px; }
.empty-state { font-size: 13px; color: var(--color-text-muted); text-align: center; padding: 32px; }

.table-wrap { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 10px 14px; font-size: 11px; font-weight: 600; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.04em; border-bottom: 1px solid var(--color-border); white-space: nowrap; }
.data-table td { padding: 10px 14px; color: var(--color-text-base); border-bottom: 1px solid var(--color-border); vertical-align: top; }
.data-table tbody tr:last-child td { border-bottom: none; }
.data-table tbody tr:hover td { background: var(--color-bg-page); }

.name-cell { font-weight: 500; white-space: nowrap; }
.muted-text { color: var(--color-text-muted); font-size: 12px; }

.action-cell { display: flex; gap: 6px; flex-wrap: wrap; }
.reject-inline { display: flex; gap: 6px; margin-top: 6px; align-items: center; flex-wrap: wrap; }
.reject-input { flex: 1; min-width: 120px; font-size: 12px; padding: 4px 8px; }
.btn-sm { padding: 4px 12px; font-size: 12px; white-space: nowrap; }
.form-input { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 6px; padding: 7px 10px; font-size: 13px; color: var(--color-text-base); width: 100%; box-sizing: border-box; }
</style>
