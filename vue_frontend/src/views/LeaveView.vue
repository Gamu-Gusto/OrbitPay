<template>
  <div class="leave-content">

    <div class="page-header">
      <div>
        <h1 class="page-title">Leave Management</h1>
        <div class="breadcrumb">
          <span>HR</span>
          <span class="sep">/</span>
          <span>Leave</span>
        </div>
      </div>
    </div>

    <!-- ══════════════ EMPLOYEE SECTION ══════════════ -->
    <template v-if="isEmployee">

      <!-- Submit request -->
      <section class="section">
        <h2 class="section-title">Submit a Leave Request</h2>
        <div class="card form-card">
          <div class="form-grid">
            <div class="form-group">
              <label class="form-label">Leave Type</label>
              <select v-model="reqForm.leave_type" class="form-input">
                <option value="">Select type</option>
                <option>Annual</option>
                <option>Sick</option>
                <option>Family Responsibility</option>
                <option>Unpaid</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Start Date</label>
              <input v-model="reqForm.start_date" type="date" class="form-input" />
            </div>
            <div class="form-group">
              <label class="form-label">End Date</label>
              <input v-model="reqForm.end_date" type="date" class="form-input" />
            </div>
            <div class="form-group days-badge-group">
              <label class="form-label">Duration</label>
              <span class="days-pill">{{ computedDays }} day{{ computedDays !== 1 ? 's' : '' }}</span>
            </div>
          </div>
          <div class="form-group mt-12">
            <label class="form-label">Reason</label>
            <textarea v-model="reqForm.reason" rows="3" class="form-input" placeholder="Optional reason…"></textarea>
          </div>
          <div class="form-actions">
            <span v-if="submitError" class="form-error">{{ submitError }}</span>
            <button @click="submitLeaveRequest" :disabled="submitting || !reqForm.leave_type || !reqForm.start_date || !reqForm.end_date" class="btn-primary">
              {{ submitting ? 'Submitting…' : 'Submit Request' }}
            </button>
          </div>
          <div v-if="submitSuccess" class="success-banner">Leave request submitted successfully.</div>
        </div>
      </section>

      <!-- Leave balances -->
      <section class="section">
        <h2 class="section-title">My Leave Balances</h2>
        <div class="card">
          <SkeletonTable v-if="loadingEmployee" :rows="5" :cols="4" />
          <div v-else-if="leaveBalances.length === 0" class="empty-state">No balances found.</div>
          <div v-else class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Leave Type</th>
                  <th class="num">Allocated</th>
                  <th class="num">Taken</th>
                  <th class="num">Remaining</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="b in leaveBalances" :key="b.leave_type">
                  <td>{{ b.leave_type }}</td>
                  <td class="num">{{ b.days_allocated }}</td>
                  <td class="num">{{ b.days_taken }}</td>
                  <td class="num">
                    <span :class="b.days_remaining <= 0 ? 'text-red' : 'text-green'">{{ b.days_remaining }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- My requests -->
      <section class="section">
        <h2 class="section-title">My Requests</h2>
        <div class="card">
          <SkeletonTable v-if="loadingEmployee" :rows="5" :cols="4" />
          <div v-else-if="myRequests.length === 0" class="empty-state">No leave requests yet.</div>
          <div v-else class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>From</th>
                  <th>To</th>
                  <th class="num">Days</th>
                  <th>Status</th>
                  <th>Note</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in myRequests" :key="r.id">
                  <td>{{ r.leave_type }}</td>
                  <td>{{ fmtDate(r.start_date) }}</td>
                  <td>{{ fmtDate(r.end_date) }}</td>
                  <td class="num">{{ r.days_requested }}</td>
                  <td><span class="badge" :class="statusBadge(r.status)">{{ statusLabel(r.status) }}</span></td>
                  <td>
                    <span v-if="r.status === 'request_documentation' && r.documentation_requested_reason" class="docs-requested-note">
                      📋 {{ r.documentation_requested_reason }}
                      <button @click="resubmit(r)" :disabled="r._resubmitting" class="btn-link-inline">Re-submit</button>
                    </span>
                    <span v-else-if="r.status === 'rejected' && r.review_note" class="rejection-reason">{{ r.review_note }}</span>
                    <span v-else class="muted-text">—</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

    </template>

    <!-- ══════════════ MANAGER SECTION ══════════════ -->
    <template v-if="isManager">
      <div class="divider" v-if="isEmployee"></div>

      <section class="section">
        <h2 class="section-title">Team Leave Requests</h2>

        <div class="filter-bar">
          <select v-model.number="mgr.companyId" @change="onCompanySelect" class="form-input filter-select">
            <option :value="0">Select company…</option>
            <option v-for="c in companies" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
          <select v-model="mgr.statusFilter" @change="fetchManagerRequests" class="form-input filter-select">
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="under_review">Under Review</option>
            <option value="request_documentation">Docs Requested</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
          <button @click="fetchManagerRequests" :disabled="!mgr.companyId || loadingManager" class="btn-secondary">
            {{ loadingManager ? 'Loading…' : 'Refresh' }}
          </button>
        </div>

        <div class="card">
          <div v-if="!mgr.companyId" class="empty-state">Select a company to view requests.</div>
          <SkeletonTable v-else-if="loadingManager" :rows="5" :cols="4" />
          <div v-else-if="managerRequests.length === 0" class="empty-state">No requests found.</div>
          <div v-else class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Employee</th>
                  <th>Type</th>
                  <th>From</th>
                  <th>To</th>
                  <th class="num">Days</th>
                  <th>Reason</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in managerRequests" :key="r.id">
                  <td class="name-cell">{{ r.employee_name }}</td>
                  <td>{{ r.leave_type }}</td>
                  <td>{{ fmtDate(r.start_date) }}</td>
                  <td>{{ fmtDate(r.end_date) }}</td>
                  <td class="num">{{ r.days_requested }}</td>
                  <td class="muted-text reason-cell">{{ r.reason || '—' }}</td>
                  <td><span class="badge" :class="statusBadge(r.status)">{{ statusLabel(r.status) }}</span></td>
                  <td>
                    <template v-if="['pending','under_review'].includes(r.status)">
                      <div class="action-cell">
                        <button v-if="r.status === 'pending'" @click="markUnderReview(r)" :disabled="r._acting" class="btn-light btn-sm">Review</button>
                        <button @click="approve(r)" :disabled="r._acting" class="btn-primary btn-sm">Approve</button>
                        <button @click="startReject(r)" :disabled="r._acting" class="btn-light btn-sm">Reject</button>
                      </div>
                      <div v-if="r._rejecting" class="reject-inline">
                        <input v-model="r._rejectNote" type="text" class="form-input reject-input" placeholder="Rejection note…" />
                        <button @click="confirmReject(r)" :disabled="r._acting" class="btn-secondary btn-sm">Confirm</button>
                        <button @click="r._rejecting = false" class="btn-light btn-sm">Cancel</button>
                      </div>
                    </template>
                    <span v-else-if="r.status === 'request_documentation'" class="muted-text" style="font-size:11px">Awaiting docs</span>
                    <span v-else class="muted-text">—</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </template>

  </div>
</template>

<script>
import { ref, computed, reactive, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { useLeaveFormatting } from '../composables/useLeaveFormatting'
import SkeletonTable from '../components/ui/SkeletonTable.vue'

export default {
  name: 'LeaveView',
  components: { SkeletonTable },
  setup() {
    const auth = useAuthStore()
    const { fmtDate, statusLabel, statusBadge } = useLeaveFormatting()

    const isEmployee = computed(() => auth.roles.includes('employee'))
    const isManager = computed(() =>
      auth.roles.some(r => ['super_admin', 'accountant'].includes(r))
    )

    // ── Employee state ──────────────────────────────────
    const loadingEmployee = ref(false)
    const leaveBalances = ref([])
    const myRequests = ref([])

    const reqForm = reactive({
      leave_type: '',
      start_date: '',
      end_date: '',
      reason: ''
    })
    const submitting = ref(false)
    const submitError = ref('')
    const submitSuccess = ref(false)

    const computedDays = computed(() => {
      if (!reqForm.start_date || !reqForm.end_date) return 0
      const diff = (new Date(reqForm.end_date) - new Date(reqForm.start_date)) / 86400000
      return diff >= 0 ? Math.floor(diff) + 1 : 0
    })

    const fetchEmployeeLeave = async () => {
      loadingEmployee.value = true
      try {
        const { data } = await axios.get('/me/leave')
        leaveBalances.value = data.balances || []
        myRequests.value = (data.requests || []).map(r => ({ ...r, _resubmitting: false }))
      } catch {}
      loadingEmployee.value = false
    }

    const submitLeaveRequest = async () => {
      submitError.value = ''
      submitSuccess.value = false
      submitting.value = true
      try {
        await axios.post('/me/leave/request', {
          leave_type: reqForm.leave_type,
          start_date: reqForm.start_date,
          end_date: reqForm.end_date,
          reason: reqForm.reason
        })
        submitSuccess.value = true
        reqForm.leave_type = ''
        reqForm.start_date = ''
        reqForm.end_date = ''
        reqForm.reason = ''
        await fetchEmployeeLeave()
      } catch (e) {
        submitError.value = e?.response?.data?.detail || 'Failed to submit request.'
      } finally {
        submitting.value = false
      }
    }

    // ── Manager state ───────────────────────────────────
    const companies = ref([])
    const loadingManager = ref(false)
    const managerRequests = ref([])

    const mgr = reactive({
      companyId: 0,
      statusFilter: 'pending'
    })

    const fetchCompanies = async () => {
      try {
        const { data } = await axios.get('/companies')
        companies.value = data
      } catch {}
    }

    const onCompanySelect = () => {
      if (mgr.companyId) fetchManagerRequests()
    }

    const fetchManagerRequests = async () => {
      if (!mgr.companyId) return
      loadingManager.value = true
      try {
        const params = {}
        if (mgr.statusFilter) params.status = mgr.statusFilter
        const { data } = await axios.get(`/companies/${mgr.companyId}/leave/requests`, { params })
        managerRequests.value = (data || []).map(r => ({
          ...r,
          _rejecting: false,
          _rejectNote: '',
          _acting: false
        }))
      } catch {}
      loadingManager.value = false
    }

    const markUnderReview = async (r) => {
      r._acting = true
      try {
        await axios.put(`/leave/requests/${r.id}/review`, { status: 'under_review' })
        await fetchManagerRequests()
      } catch { r._acting = false }
    }

    const approve = async (r) => {
      r._acting = true
      try {
        await axios.put(`/leave/requests/${r.id}/review`, { status: 'approved' })
        await fetchManagerRequests()
      } catch { r._acting = false }
    }

    const startReject = (r) => {
      managerRequests.value.forEach(x => { x._rejecting = false })
      r._rejecting = true
      r._rejectNote = ''
    }

    const confirmReject = async (r) => {
      r._acting = true
      try {
        await axios.put(`/leave/requests/${r.id}/review`, { status: 'rejected', note: r._rejectNote })
        await fetchManagerRequests()
      } catch { r._acting = false; r._rejecting = false }
    }

    const resubmit = async (r) => {
      r._resubmitting = true
      try {
        await axios.post(`/leave/requests/${r.id}/submit-documents`)
        await fetchEmployeeLeave()
      } catch { r._resubmitting = false }
    }



    onMounted(async () => {
      if (isEmployee.value) fetchEmployeeLeave()
      if (isManager.value) fetchCompanies()
    })

    return {
      isEmployee, isManager,
      loadingEmployee, leaveBalances, myRequests,
      reqForm, submitting, submitError, submitSuccess, computedDays,
      submitLeaveRequest, resubmit,
      companies, loadingManager, managerRequests, mgr,
      onCompanySelect, fetchManagerRequests,
      markUnderReview, approve, startReject, confirmReject,
      fmtDate, statusLabel, statusBadge
    }
  }
}
</script>

<style scoped>
.leave-content {
  padding: 24px;
  max-width: 1100px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.page-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-base);
  margin: 0 0 4px;
}

.breadcrumb { font-size: 11px; color: var(--color-text-muted); }
.sep { margin: 0 6px; }

.section { display: flex; flex-direction: column; gap: 10px; }

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0;
}

.divider {
  height: 1px;
  background: var(--color-border);
}

.card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 20px;
}

.form-card { display: flex; flex-direction: column; gap: 0; }

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 14px;
}

.form-group { display: flex; flex-direction: column; gap: 5px; }

.form-label { font-size: 11.5px; font-weight: 500; color: var(--color-text-muted); }

.mt-12 { margin-top: 14px; }

.days-badge-group { justify-content: flex-end; }

.days-pill {
  display: inline-block;
  padding: 5px 14px;
  background: #eff6ff;
  color: #1d4ed8;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  align-self: flex-start;
  margin-top: 2px;
}

.form-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
}

.form-error { font-size: 12px; color: #dc2626; }

.success-banner {
  margin-top: 12px;
  padding: 10px 14px;
  background: #dcfce7;
  border: 1px solid #86efac;
  border-radius: 7px;
  font-size: 13px;
  color: #15803d;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.filter-select { width: auto; min-width: 160px; }

.table-wrap { overflow-x: auto; }

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.data-table th {
  text-align: left;
  padding: 10px 14px;
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}

.data-table td {
  padding: 10px 14px;
  color: var(--color-text-base);
  border-bottom: 1px solid var(--color-border);
  vertical-align: top;
}

.data-table tbody tr:last-child td { border-bottom: none; }
.data-table tbody tr:hover td { background: var(--color-bg-page); }

.num { text-align: right; }

.badge {
  display: inline-block;
  padding: 2px 9px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.badge-green  { background: #dcfce7; color: #15803d; }
.badge-red    { background: #fee2e2; color: #b91c1c; }
.badge-yellow { background: #fef9c3; color: #854d0e; }
.badge-blue   { background: #dbeafe; color: #1d4ed8; }
.badge-orange { background: #ffedd5; color: #92400e; }
.badge-gray   { background: var(--color-bg-page); color: var(--color-text-muted); }

.docs-requested-note { font-size: 11px; color: #92400e; font-style: italic; display: flex; flex-direction: column; gap: 4px; }
.btn-link-inline { background: none; border: none; color: #1d4ed8; font-size: 11px; cursor: pointer; padding: 0; text-decoration: underline; }
.btn-link-inline:hover { color: #1e40af; }

.text-green { color: #15803d; font-weight: 600; }
.text-red { color: #dc2626; font-weight: 600; }

.muted-text { color: var(--color-text-muted); font-size: 12px; }
.rejection-reason { font-size: 12px; color: #b91c1c; font-style: italic; }
.name-cell { font-weight: 500; }
.reason-cell { max-width: 180px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.action-cell { display: flex; gap: 6px; }

.reject-inline {
  display: flex;
  gap: 6px;
  margin-top: 6px;
  align-items: center;
  flex-wrap: wrap;
}

.reject-input { flex: 1; min-width: 120px; font-size: 12px; padding: 4px 8px; }

.btn-sm { padding: 4px 12px; font-size: 12px; white-space: nowrap; }

.loading-state {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--color-text-muted);
  font-size: 13px;
  padding: 8px 0;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.empty-state {
  font-size: 13px;
  color: var(--color-text-muted);
  padding: 24px 0;
  text-align: center;
}

@media (max-width: 700px) {
  .form-grid { grid-template-columns: 1fr 1fr; }
  .filter-bar { flex-direction: column; align-items: flex-start; }
  .filter-select { width: 100%; }
}
</style>
