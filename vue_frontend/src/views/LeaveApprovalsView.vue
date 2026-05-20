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

    <div v-if="loading" class="loading-state"><div class="spinner"></div><span>Loading pending requests…</span></div>

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
              <th>Reason</th>
              <th>Submitted</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in requests" :key="r.id">
              <td class="name-cell">{{ r.employee_name }}</td>
              <td class="muted-text">{{ r.company_name || '—' }}</td>
              <td>{{ r.leave_type }}</td>
              <td>{{ fmtDate(r.start_date) }}</td>
              <td>{{ fmtDate(r.end_date) }}</td>
              <td class="num">{{ r.days_requested }}</td>
              <td class="reason-cell muted-text">{{ r.reason || '—' }}</td>
              <td class="muted-text">{{ fmtDate(r.created_at) }}</td>
              <td>
                <div class="action-cell">
                  <button @click="approve(r)" :disabled="r._acting" class="btn-primary btn-sm">Approve</button>
                  <button @click="startReject(r)" :disabled="r._acting" class="btn-light btn-sm">Reject</button>
                </div>
                <div v-if="r._rejecting" class="reject-inline">
                  <input v-model="r._rejectNote" type="text" class="form-input reject-input" placeholder="Rejection note…" />
                  <button @click="confirmReject(r)" :disabled="r._acting" class="btn-secondary btn-sm">Confirm</button>
                  <button @click="r._rejecting = false" class="btn-light btn-sm">Cancel</button>
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
        requests.value = (data || []).map(r => ({ ...r, _rejecting: false, _rejectNote: '', _acting: false }))
      } catch {}
      loading.value = false
    }

    const approve = async (r) => {
      r._acting = true
      try {
        await axios.put(`/leave/requests/${r.id}/review`, { approved: true })
        await load()
      } catch { r._acting = false }
    }

    const startReject = (r) => {
      requests.value.forEach(x => { x._rejecting = false })
      r._rejecting = true
      r._rejectNote = ''
    }

    const confirmReject = async (r) => {
      r._acting = true
      try {
        await axios.put(`/leave/requests/${r.id}/review`, { approved: false, note: r._rejectNote })
        await load()
      } catch { r._acting = false; r._rejecting = false }
    }

    const fmtDate = (s) => {
      if (!s) return '—'
      try { return new Date(s).toLocaleDateString('en-ZA', { year: 'numeric', month: 'short', day: '2-digit' }) }
      catch { return s }
    }

    onMounted(load)
    return { loading, requests, load, approve, startReject, confirmReject, fmtDate }
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

.num { text-align: right; }
.name-cell { font-weight: 500; white-space: nowrap; }
.muted-text { color: var(--color-text-muted); font-size: 12px; }
.reason-cell { max-width: 160px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.action-cell { display: flex; gap: 6px; }
.reject-inline { display: flex; gap: 6px; margin-top: 6px; align-items: center; flex-wrap: wrap; }
.reject-input { flex: 1; min-width: 120px; font-size: 12px; padding: 4px 8px; }
.btn-sm { padding: 4px 12px; font-size: 12px; white-space: nowrap; }
.form-input { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 6px; padding: 7px 10px; font-size: 13px; color: var(--color-text-base); width: 100%; box-sizing: border-box; }
</style>
