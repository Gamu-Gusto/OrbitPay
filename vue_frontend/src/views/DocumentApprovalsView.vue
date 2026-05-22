<template>
  <div class="page-content">

    <div class="page-header">
      <div>
        <h1 class="page-title">Documents</h1>
        <div class="breadcrumb"><span>Approvals</span><span class="sep">/</span><span>Documents</span></div>
      </div>
      <button @click="load" :disabled="loading" class="btn btn-secondary btn-sm">
        {{ loading ? 'Loading…' : 'Refresh' }}
      </button>
    </div>

    <div class="tab-bar">
      <button
        v-for="t in TABS" :key="t.key"
        :class="['tab-btn', { active: activeTab === t.key }]"
        @click="switchTab(t.key)"
      >
        {{ t.label }}
        <span v-if="t.key === 'pending' && pendingCount > 0" class="tab-badge">{{ pendingCount }}</span>
      </button>
    </div>

    <SkeletonTable v-if="loading" :rows="5" :cols="activeTab === 'pending' ? 6 : 7" />

    <div v-else-if="docs.length === 0" class="card empty-state">
      No {{ activeTab === 'all' ? '' : activeTab }} documents found.
    </div>

    <div v-else class="card">
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Employee</th>
              <th>Company</th>
              <th>Type</th>
              <th>File</th>
              <th>Uploaded</th>
              <th v-if="activeTab !== 'pending'">Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="doc in docs" :key="doc.id">
              <td class="name-cell">{{ doc.employee_name }}</td>
              <td class="muted-text">{{ doc.company_name }}</td>
              <td>{{ doc.document_type }}</td>
              <td>
                <div class="file-name">{{ doc.file_name }}</div>
                <div class="muted-text">{{ fmtSize(doc.file_size) }}</div>
              </td>
              <td class="muted-text">{{ fmtDate(doc.uploaded_at) }}</td>
              <td v-if="activeTab !== 'pending'">
                <span :class="statusBadgeClass(doc.status)" class="badge">{{ doc.status }}</span>
                <div v-if="doc.rejection_reason" class="rejection-reason">{{ doc.rejection_reason }}</div>
              </td>
              <td>
                <div class="action-cell">
                  <button v-if="isPreviewable(doc)" @click="openPreview(doc)" class="btn btn-sm">View</button>
                  <button @click="download(doc)" class="btn btn-sm">Download</button>
                  <template v-if="activeTab === 'pending'">
                    <button @click="approve(doc)" :disabled="doc._acting" class="btn btn-sm btn-primary">Approve</button>
                    <button @click="startReject(doc)" :disabled="doc._acting" class="btn btn-sm btn-danger">Reject</button>
                  </template>
                </div>
                <div v-if="doc._rejecting" class="reject-inline">
                  <input
                    v-model="doc._rejectNote"
                    type="text"
                    class="form-input reject-input"
                    placeholder="Rejection reason…"
                    @keyup.enter="confirmReject(doc)"
                  />
                  <button @click="confirmReject(doc)" :disabled="doc._acting || !doc._rejectNote.trim()" class="btn btn-sm btn-secondary">Confirm</button>
                  <button @click="doc._rejecting = false" class="btn btn-sm">Cancel</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- In-app preview modal -->
    <teleport to="body">
      <div v-if="previewDoc" class="modal-overlay" @click.self="closePreview">
        <div class="modal" role="dialog" :aria-label="previewDoc.file_name">
          <div class="modal-header">
            <div class="modal-meta">
              <span class="modal-title">{{ previewDoc.file_name }}</span>
              <span class="muted-text">{{ previewDoc.employee_name }} · {{ previewDoc.document_type }}</span>
            </div>
            <div class="modal-actions">
              <button @click="download(previewDoc)" class="btn btn-sm btn-secondary">Download</button>
              <button @click="closePreview" class="modal-close" aria-label="Close">✕</button>
            </div>
          </div>
          <div class="modal-body">
            <div v-if="previewLoading" class="preview-loading">
              <div class="spinner"></div><span>Loading preview…</span>
            </div>
            <img v-else-if="previewType === 'image'" :src="previewUrl" class="preview-img" :alt="previewDoc.file_name" />
            <iframe v-else-if="previewType === 'pdf'" :src="previewUrl" class="preview-pdf" title="Document preview" />
            <div v-else class="preview-unsupported">
              <p>Preview not available for this file type.</p>
              <button @click="download(previewDoc)" class="btn btn-primary">Download to view</button>
            </div>
          </div>
        </div>
      </div>
    </teleport>

  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import SkeletonTable from '@/components/ui/SkeletonTable.vue'

const TABS = [
  { key: 'pending', label: 'Pending Review' },
  { key: 'approved', label: 'Approved' },
  { key: 'rejected', label: 'Rejected' },
  { key: 'all', label: 'All Documents' },
]

function getFileExt(filename) {
  return filename ? filename.split('.').pop().toLowerCase() : ''
}

export default {
  name: 'DocumentApprovalsView',
  components: { SkeletonTable },
  setup() {
    const loading = ref(false)
    const docs = ref([])
    const activeTab = ref('pending')
    const pendingCount = ref(0)

    const previewDoc = ref(null)
    const previewUrl = ref(null)
    const previewType = ref(null)
    const previewLoading = ref(false)

    const load = async () => {
      loading.value = true
      try {
        const status = activeTab.value === 'all' ? undefined : activeTab.value
        const params = status ? { status } : {}
        const { data } = await axios.get('/documents', { params })
        docs.value = (data || []).map(d => ({ ...d, _rejecting: false, _rejectNote: '', _acting: false }))

        if (activeTab.value !== 'pending') {
          try {
            const { data: pd } = await axios.get('/documents', { params: { status: 'pending' } })
            pendingCount.value = pd.length
          } catch { /* non-critical */ }
        } else {
          pendingCount.value = docs.value.length
        }
      } catch { /* handled by interceptor */ }
      loading.value = false
    }

    const switchTab = (key) => {
      activeTab.value = key
      load()
    }

    const isPreviewable = (doc) => {
      const ext = getFileExt(doc.file_name)
      return ['pdf', 'jpg', 'jpeg', 'png'].includes(ext)
    }

    const openPreview = async (doc) => {
      previewDoc.value = doc
      previewLoading.value = true
      previewUrl.value = null
      previewType.value = null
      try {
        const res = await axios.get(`/documents/${doc.id}/download`, {
          params: { inline: true },
          responseType: 'blob',
        })
        const ext = getFileExt(doc.file_name)
        const mimeMap = { pdf: 'application/pdf', jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png' }
        const mime = mimeMap[ext] || 'application/octet-stream'
        const blob = new Blob([res.data], { type: mime })
        previewUrl.value = URL.createObjectURL(blob)
        previewType.value = ext === 'pdf' ? 'pdf' : 'image'
      } catch {
        previewType.value = 'unsupported'
      }
      previewLoading.value = false
    }

    const closePreview = () => {
      if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
      previewDoc.value = null
      previewUrl.value = null
      previewType.value = null
    }

    const download = async (doc) => {
      try {
        const res = await axios.get(`/documents/${doc.id}/download`, { responseType: 'blob' })
        const url = URL.createObjectURL(new Blob([res.data]))
        const a = document.createElement('a')
        a.href = url
        a.download = doc.file_name
        document.body.appendChild(a)
        a.click()
        a.remove()
        URL.revokeObjectURL(url)
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
      if (!doc._rejectNote.trim()) return
      doc._acting = true
      try {
        await axios.patch(`/documents/${doc.id}/review`, { status: 'rejected', reason: doc._rejectNote })
        await load()
      } catch { doc._acting = false; doc._rejecting = false }
    }

    const statusBadgeClass = (status) => ({
      'badge-success': status === 'approved',
      'badge-danger': status === 'rejected',
      'badge-warning': status === 'pending',
    })

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

    return {
      TABS, loading, docs, activeTab, pendingCount,
      previewDoc, previewUrl, previewType, previewLoading,
      load, switchTab,
      isPreviewable, openPreview, closePreview,
      download, approve, startReject, confirmReject,
      statusBadgeClass, fmtDate, fmtSize,
    }
  }
}
</script>

<style scoped>
.page-content { padding: 24px; max-width: 1280px; display: flex; flex-direction: column; gap: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-title { font-size: 16px; font-weight: 600; color: var(--color-text-primary); margin: 0 0 4px; }
.breadcrumb { font-size: 11px; color: var(--color-text-muted); }
.sep { margin: 0 6px; }

/* Tab bar */
.tab-bar { display: flex; gap: 2px; border-bottom: 1px solid var(--color-border); }
.tab-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 16px; font-size: 13px; font-weight: 500;
  color: var(--color-text-muted); background: none; border: none;
  border-bottom: 2px solid transparent; margin-bottom: -1px;
  cursor: pointer; transition: color var(--transition-fast), border-color var(--transition-fast);
}
.tab-btn:hover { color: var(--color-text-base); }
.tab-btn.active { color: var(--color-accent); border-bottom-color: var(--color-accent); }
.tab-badge {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 18px; height: 18px; padding: 0 5px;
  background: var(--color-accent); color: #fff;
  font-size: 10px; font-weight: 600; border-radius: 9999px;
}

/* Card & table */
.card { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); }
.empty-state { font-size: 13px; color: var(--color-text-muted); text-align: center; padding: 48px 24px; }
.table-wrap { overflow-x: auto; }

.name-cell { font-weight: 500; white-space: nowrap; }
.muted-text { color: var(--color-text-muted); font-size: 12px; }
.file-name { font-size: 13px; color: var(--color-text-base); }

.action-cell { display: flex; gap: 6px; flex-wrap: wrap; }
.reject-inline { display: flex; gap: 6px; margin-top: 8px; align-items: center; flex-wrap: wrap; }
.reject-input { flex: 1; min-width: 140px; height: 30px; font-size: 12px; }
.rejection-reason { margin-top: 4px; font-size: 11px; color: var(--color-danger); font-style: italic; }

/* Modal overlay */
.modal-overlay {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(15,23,42,0.55);
  display: flex; align-items: center; justify-content: center;
  padding: 24px;
}
.modal {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-md);
  width: 100%; max-width: 900px;
  max-height: 90vh;
  display: flex; flex-direction: column;
  overflow: hidden;
}
.modal-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border);
  gap: 12px;
  flex-shrink: 0;
}
.modal-meta { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.modal-title { font-size: 14px; font-weight: 600; color: var(--color-text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.modal-actions { display: flex; gap: 8px; align-items: center; flex-shrink: 0; }
.modal-close {
  width: 30px; height: 30px; padding: 0; border: none; background: none;
  font-size: 16px; cursor: pointer; color: var(--color-text-muted);
  border-radius: var(--radius-md); display: flex; align-items: center; justify-content: center;
}
.modal-close:hover { background: var(--color-surface-secondary); color: var(--color-text-base); }
.modal-body { flex: 1; overflow: auto; display: flex; align-items: center; justify-content: center; min-height: 200px; }

.preview-loading { display: flex; align-items: center; gap: 10px; color: var(--color-text-muted); font-size: 13px; }
.spinner { width: 20px; height: 20px; border: 2px solid var(--color-border); border-top-color: var(--color-accent); border-radius: 50%; animation: spin 0.8s linear infinite; flex-shrink: 0; }
@keyframes spin { to { transform: rotate(360deg); } }

.preview-img { max-width: 100%; max-height: 75vh; object-fit: contain; display: block; }
.preview-pdf { width: 100%; height: 75vh; border: none; display: block; }
.preview-unsupported { text-align: center; padding: 40px; color: var(--color-text-muted); font-size: 13px; display: flex; flex-direction: column; align-items: center; gap: 16px; }
</style>
