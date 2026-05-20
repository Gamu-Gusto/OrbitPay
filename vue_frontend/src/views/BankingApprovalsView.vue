<template>
  <div class="page-content">

    <div class="page-header">
      <div>
        <h1 class="page-title">Banking Change Approvals</h1>
        <div class="breadcrumb"><span>Approvals</span><span class="sep">/</span><span>Banking</span></div>
      </div>
      <button @click="load" :disabled="loading" class="btn-secondary">
        {{ loading ? 'Loading…' : 'Refresh' }}
      </button>
    </div>

    <div v-if="loading" class="loading-state"><div class="spinner"></div><span>Loading pending requests…</span></div>

    <div v-else-if="changes.length === 0" class="card empty-state">No banking change requests pending review.</div>

    <div v-else class="card">
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Employee</th>
              <th>Company</th>
              <th>Current Bank</th>
              <th>Current Account</th>
              <th>New Bank</th>
              <th>New Account</th>
              <th>New Type</th>
              <th>New Branch</th>
              <th>Requested</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in changes" :key="c.id">
              <td class="name-cell">{{ c.employee_name || '—' }}</td>
              <td class="muted-text">{{ c.company_name || '—' }}</td>
              <td class="muted-text">{{ c.current_bank_name || '—' }}</td>
              <td class="muted-text">{{ c.current_account_number || '—' }}</td>
              <td class="highlight">{{ c.new_bank_name || '—' }}</td>
              <td class="highlight">{{ c.new_account_number || '—' }}</td>
              <td class="highlight">{{ c.new_account_type || '—' }}</td>
              <td class="highlight">{{ c.new_branch_code || '—' }}</td>
              <td class="muted-text">{{ fmtDate(c.requested_at) }}</td>
              <td>
                <div class="action-cell">
                  <button @click="approve(c)" :disabled="c._acting" class="btn-primary btn-sm">Approve</button>
                  <button @click="startReject(c)" :disabled="c._acting" class="btn-light btn-sm">Reject</button>
                </div>
                <div v-if="c._rejecting" class="reject-inline">
                  <input v-model="c._rejectNote" type="text" class="form-input reject-input" placeholder="Rejection reason…" />
                  <button @click="confirmReject(c)" :disabled="c._acting" class="btn-secondary btn-sm">Confirm</button>
                  <button @click="c._rejecting = false" class="btn-light btn-sm">Cancel</button>
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
  name: 'BankingApprovalsView',
  setup() {
    const loading = ref(false)
    const changes = ref([])

    const load = async () => {
      loading.value = true
      try {
        const { data } = await axios.get('/banking-changes/pending')
        changes.value = (data || []).map(c => ({ ...c, _rejecting: false, _rejectNote: '', _acting: false }))
      } catch {}
      loading.value = false
    }

    const approve = async (c) => {
      c._acting = true
      try {
        await axios.patch(`/banking-changes/${c.id}/review`, { status: 'approved' })
        await load()
      } catch { c._acting = false }
    }

    const startReject = (c) => {
      changes.value.forEach(x => { x._rejecting = false })
      c._rejecting = true
      c._rejectNote = ''
    }

    const confirmReject = async (c) => {
      c._acting = true
      try {
        await axios.patch(`/banking-changes/${c.id}/review`, { status: 'rejected', reason: c._rejectNote })
        await load()
      } catch { c._acting = false; c._rejecting = false }
    }

    const fmtDate = (s) => {
      if (!s) return '—'
      try { return new Date(s).toLocaleDateString('en-ZA', { year: 'numeric', month: 'short', day: '2-digit' }) }
      catch { return s }
    }

    onMounted(load)
    return { loading, changes, load, approve, startReject, confirmReject, fmtDate }
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
.data-table td { padding: 10px 14px; color: var(--color-text-base); border-bottom: 1px solid var(--color-border); vertical-align: top; white-space: nowrap; }
.data-table tbody tr:last-child td { border-bottom: none; }
.data-table tbody tr:hover td { background: var(--color-bg-page); }

.name-cell { font-weight: 500; }
.muted-text { color: var(--color-text-muted); font-size: 12px; }
.highlight { color: var(--color-text-base); font-weight: 500; }

.action-cell { display: flex; gap: 6px; flex-wrap: wrap; }
.reject-inline { display: flex; gap: 6px; margin-top: 6px; align-items: center; flex-wrap: wrap; }
.reject-input { flex: 1; min-width: 140px; font-size: 12px; padding: 4px 8px; }
.btn-sm { padding: 4px 12px; font-size: 12px; white-space: nowrap; }
.form-input { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 6px; padding: 7px 10px; font-size: 13px; color: var(--color-text-base); width: 100%; box-sizing: border-box; }
</style>
