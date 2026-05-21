<template>
  <div class="page-content">

    <div class="page-header">
      <div>
        <h1 class="page-title">Leave Approvals</h1>
        <div class="breadcrumb"><span>Approvals</span><span class="sep">/</span><span>Leave</span></div>
      </div>
      <button @click="load" :disabled="loading" class="btn-secondary">
        {{ loading ? 'Loading…' : 'Refresh' }}
      </button>
    </div>

    <div v-if="loading" class="loading-state"><div class="spinner"></div><span>Loading requests…</span></div>

    <div v-else-if="requests.length === 0" class="card empty-state">All leave requests have been reviewed.</div>

    <div v-else class="card">
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Employee</th>
              <th>Company</th>
              <th>Type</th>
              <th>From</th>
              <th>To</th>
              <th class="num">Days</th>
              <th>Reason / Notes</th>
              <th>Status</th>
              <th>Submitted</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in requests" :key="r.id">
              <td class="name-cell">{{ r.employee_name }}</td>
              <td class="muted-text">{{ r.company_name || '—' }}</td>
              <td>{{ r.leave_type }}</td>
              <td class="muted-text">{{ fmtDate(r.start_date) }}</td>
              <td class="muted-text">{{ fmtDate(r.end_date) }}</td>
              <td class="num">{{ r.days_requested }}</td>
              <td class="reason-cell muted-text">
                <span v-if="r.status === 'request_documentation' && r.documentation_requested_reason" class="docs-note">
                  Docs requested: {{ r.documentation_requested_reason }}
                </span>
                <span v-else>{{ r.reason || '—' }}</span>
              </td>
              <td><span class="badge" :class="statusBadge(r.status)">{{ statusLabel(r.status) }}</span></td>
              <td class="muted-text">{{ fmtDate(r.created_at) }}</td>
              <td>
                <div v-if="r.status === 'request_documentation'" class="muted-text" style="font-size:11px;white-space:nowrap">
                  Awaiting employee docs
                </div>
                <div v-else class="action-cell">
                  <button v-if="r.status === 'pending'" @click="markUnderReview(r)" :disabled="r._acting" class="btn-light btn-sm">Review</button>
                  <button @click="approve(r)" :disabled="r._acting" class="btn-primary btn-sm">Approve</button>
                  <button @click="startReject(r)" :disabled="r._acting" class="btn-light btn-sm">Reject</button>
                  <button @click="startRequestDocs(r)" :disabled="r._acting" class="btn-secondary btn-sm">Req. Docs</button>
                </div>
                <div v-if="r._rejecting" class="reject-inline">
                  <input v-model="r._rejectNote" type="text" class="form-input reject-input" placeholder="Rejection note…" />
                  <button @click="confirmReject(r)" :disabled="r._acting" class="btn-secondary btn-sm">Confirm</button>
                  <button @click="r._rejecting = false" class="btn-light btn-sm">Cancel</button>
                </div>
                <div v-if="r._requestingDocs" class="reject-inline">
                  <input v-model="r._docsReason" type="text" class="form-input reject-input" placeholder="What documentation is needed?" />
                  <button @click="confirmRequestDocs(r)" :disabled="r._acting" class="btn-secondary btn-sm">Send</button>
                  <button @click="r._requestingDocs = false" class="btn-light btn-sm">Cancel</button>
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
  name: 'LeaveApprovalsView',
  setup() {
    const loading = ref(false)
    const requests = ref([])

    const load = async () => {
      loading.value = true
      try {
        const { data } = await axios.get('/leave/pending')
        requests.value = (data || []).map(r => ({
          ...r,
          _rejecting: false, _rejectNote: '',
          _requestingDocs: false, _docsReason: '',
          _acting: false
        }))
      } catch {}
      loading.value = false
    }

    const markUnderReview = async (r) => {
      r._acting = true
      try {
        await axios.put(`/leave/requests/${r.id}/review`, { status: 'under_review' })
        await load()
      } catch { r._acting = false }
    }

    const approve = async (r) => {
      r._acting = true
      try {
        await axios.put(`/leave/requests/${r.id}/review`, { status: 'approved' })
        await load()
      } catch { r._acting = false }
    }

    const startReject = (r) => {
      requests.value.forEach(x => { x._rejecting = false; x._requestingDocs = false })
      r._rejecting = true
      r._rejectNote = ''
    }

    const confirmReject = async (r) => {
      r._acting = true
      try {
        await axios.put(`/leave/requests/${r.id}/review`, { status: 'rejected', note: r._rejectNote })
        await load()
      } catch { r._acting = false; r._rejecting = false }
    }

    const startRequestDocs = (r) => {
      requests.value.forEach(x => { x._rejecting = false; x._requestingDocs = false })
      r._requestingDocs = true
      r._docsReason = ''
    }

    const confirmRequestDocs = async (r) => {
      if (!r._docsReason.trim()) return
      r._acting = true
      try {
        await axios.post(`/leave/requests/${r.id}/request-documents`, { reason: r._docsReason })
        await load()
      } catch { r._acting = false; r._requestingDocs = false }
    }

    const fmtDate = (s) => {
      if (!s) return '—'
      try { return new Date(s).toLocaleDateString('en-ZA', { year: 'numeric', month: 'short', day: '2-digit' }) }
      catch { return s }
    }

    const statusLabel = (s) => {
      const map = {
        pending: 'Pending',
        under_review: 'Under Review',
        request_documentation: 'Docs Requested',
        approved: 'Approved',
        rejected: 'Rejected',
      }
      return map[s] || s
    }

    const statusBadge = (s) => {
      const map = {
        pending: 'badge-yellow',
        under_review: 'badge-blue',
        request_documentation: 'badge-orange',
        approved: 'badge-green',
        rejected: 'badge-red',
      }
      return map[s] || 'badge-gray'
    }

    onMounted(load)
    return {
      loading, requests, load,
      markUnderReview, approve, startReject, confirmReject,
      startRequestDocs, confirmRequestDocs,
      fmtDate, statusLabel, statusBadge
    }
  }
}
</script>

<style scoped>
.page-content { padding: 24px; max-width: 1300px; display: flex; flex-direction: column; gap: 24px; }
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

.num { text-align: right; }
.name-cell { font-weight: 500; white-space: nowrap; }
.muted-text { color: var(--color-text-muted); font-size: 12px; }
.reason-cell { max-width: 200px; }
.docs-note { font-style: italic; color: #92400e; font-size: 11px; }

.badge { display: inline-block; padding: 2px 9px; border-radius: 10px; font-size: 11px; font-weight: 600; white-space: nowrap; }
.badge-yellow  { background: #fef9c3; color: #854d0e; }
.badge-blue    { background: #dbeafe; color: #1d4ed8; }
.badge-orange  { background: #ffedd5; color: #92400e; }
.badge-green   { background: #dcfce7; color: #15803d; }
.badge-red     { background: #fee2e2; color: #b91c1c; }
.badge-gray    { background: var(--color-bg-page); color: var(--color-text-muted); }

.action-cell { display: flex; gap: 6px; flex-wrap: wrap; }
.reject-inline { display: flex; gap: 6px; margin-top: 6px; align-items: center; flex-wrap: wrap; }
.reject-input { flex: 1; min-width: 140px; font-size: 12px; padding: 4px 8px; }
.btn-sm { padding: 4px 12px; font-size: 12px; white-space: nowrap; }
.form-input { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 6px; padding: 7px 10px; font-size: 13px; color: var(--color-text-base); width: 100%; box-sizing: border-box; }
</style>
