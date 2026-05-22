<template>
  <div class="view-content">

    <!-- ── Page header ─────────────────────────────────────────────────────── -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Leave Management</h1>
        <div class="breadcrumb">
          <span>HR</span><span class="sep">/</span><span>Leave</span>
        </div>
      </div>
      <button v-if="isEmployee" @click="showApplyModal = true" class="btn btn-primary btn-sm">
        + Apply for Leave
      </button>
    </div>

    <!-- ── Tabs ────────────────────────────────────────────────────────────── -->
    <div class="tabs-underline">
      <button
        v-if="isEmployee"
        :class="['tab-underline', { active: activeTab === 'balances' }]"
        @click="activeTab = 'balances'"
      >Balances</button>
      <button
        v-if="isEmployee"
        :class="['tab-underline', { active: activeTab === 'requests' }]"
        @click="activeTab = 'requests'"
      >My Requests</button>
      <button
        v-if="isManager"
        :class="['tab-underline', { active: activeTab === 'team' }]"
        @click="activeTab = 'team'"
      >Team Requests</button>
    </div>

    <!-- ══════════════ BALANCES TAB ══════════════ -->
    <div v-if="activeTab === 'balances' && isEmployee" class="card">
      <div class="card-header">
        <span class="card-title">Leave Balances</span>
      </div>
      <SkeletonTable v-if="loadingEmployee" :rows="4" :cols="4" />
      <div v-else-if="leaveBalances.length === 0" class="empty-state">
        <p>No leave balances found.</p>
      </div>
      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Leave Type</th>
              <th class="col-right">Allocated</th>
              <th class="col-right">Taken</th>
              <th class="col-right">Remaining</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="b in leaveBalances" :key="b.leave_type">
              <td class="cell-primary">{{ b.leave_type }}</td>
              <td class="col-right cell-muted">{{ b.days_allocated }}</td>
              <td class="col-right cell-muted">{{ b.days_taken }}</td>
              <td class="col-right">
                <span :class="b.days_remaining <= 0 ? 'bal-zero' : 'bal-ok'">
                  {{ b.days_remaining }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ══════════════ MY REQUESTS TAB ══════════════ -->
    <div v-if="activeTab === 'requests' && isEmployee" class="card">
      <div class="card-header">
        <span class="card-title">My Leave Requests</span>
      </div>
      <SkeletonTable v-if="loadingEmployee" :rows="5" :cols="6" />
      <div v-else-if="myRequests.length === 0" class="empty-state">
        <p>No leave requests yet. Use <strong>Apply for Leave</strong> to submit one.</p>
      </div>
      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>From</th>
              <th>To</th>
              <th class="col-right">Days</th>
              <th>Status</th>
              <th>Note</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in myRequests" :key="r.id">
              <td class="cell-primary">{{ r.leave_type }}</td>
              <td class="cell-muted">{{ fmtDate(r.start_date) }}</td>
              <td class="cell-muted">{{ fmtDate(r.end_date) }}</td>
              <td class="col-right cell-muted">{{ r.days_requested }}</td>
              <td>
                <span class="badge" :class="statusBadge(r.status)">{{ statusLabel(r.status) }}</span>
              </td>
              <td>
                <span
                  v-if="r.status === 'request_documentation' && r.documentation_requested_reason"
                  class="docs-note"
                >
                  {{ r.documentation_requested_reason }}
                  <button @click="resubmit(r)" :disabled="r._resubmitting" class="btn-text">
                    Re-submit
                  </button>
                </span>
                <span v-else-if="r.status === 'rejected' && r.review_note" class="rejection-note">
                  {{ r.review_note }}
                </span>
                <span v-else class="cell-muted">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ══════════════ TEAM REQUESTS TAB ══════════════ -->
    <template v-if="activeTab === 'team' && isManager">
      <div class="filter-row">
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
        <button
          @click="fetchManagerRequests"
          :disabled="!mgr.companyId || loadingManager"
          class="btn btn-secondary btn-sm"
        >
          {{ loadingManager ? 'Loading…' : 'Refresh' }}
        </button>
      </div>

      <div class="card">
        <div v-if="!mgr.companyId" class="empty-state">
          <p>Select a company above to view team leave requests.</p>
        </div>
        <SkeletonTable v-else-if="loadingManager" :rows="5" :cols="8" />
        <div v-else-if="managerRequests.length === 0" class="empty-state">
          <p>No requests found for the selected filters.</p>
        </div>
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Employee</th>
                <th>Type</th>
                <th>From</th>
                <th>To</th>
                <th class="col-right">Days</th>
                <th>Reason</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in managerRequests" :key="r.id">
                <td class="cell-primary">{{ r.employee_name }}</td>
                <td>{{ r.leave_type }}</td>
                <td class="cell-muted">{{ fmtDate(r.start_date) }}</td>
                <td class="cell-muted">{{ fmtDate(r.end_date) }}</td>
                <td class="col-right cell-muted">{{ r.days_requested }}</td>
                <td class="reason-cell cell-muted">{{ r.reason || '—' }}</td>
                <td>
                  <span class="badge" :class="statusBadge(r.status)">{{ statusLabel(r.status) }}</span>
                </td>
                <td>
                  <template v-if="['pending', 'under_review'].includes(r.status)">
                    <div class="col-actions">
                      <button
                        v-if="r.status === 'pending'"
                        @click="markUnderReview(r)"
                        :disabled="r._acting"
                        class="btn btn-light btn-sm"
                      >Review</button>
                      <button @click="approve(r)" :disabled="r._acting" class="btn btn-primary btn-sm">Approve</button>
                      <button @click="startReject(r)" :disabled="r._acting" class="btn btn-light btn-sm">Reject</button>
                    </div>
                    <div v-if="r._rejecting" class="inline-form">
                      <input
                        v-model="r._rejectNote"
                        type="text"
                        class="form-input inline-input"
                        placeholder="Rejection note…"
                        @keyup.enter="confirmReject(r)"
                      />
                      <button @click="confirmReject(r)" :disabled="r._acting" class="btn btn-secondary btn-sm">Confirm</button>
                      <button @click="r._rejecting = false" class="btn btn-light btn-sm">Cancel</button>
                    </div>
                  </template>
                  <span v-else-if="r.status === 'request_documentation'" class="cell-muted text-xs">Awaiting docs</span>
                  <span v-else class="cell-muted">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <!-- ══════════════ APPLY FOR LEAVE MODAL ══════════════ -->
    <teleport to="body">
      <div v-if="showApplyModal" class="modal-overlay" @click.self="closeApplyModal">
        <div class="modal" role="dialog" aria-labelledby="apply-modal-title">
          <div class="modal-header">
            <h2 id="apply-modal-title">Apply for Leave</h2>
            <button @click="closeApplyModal" class="modal-close" aria-label="Close">✕</button>
          </div>

          <div class="modal-body">
            <div class="form-grid">
              <div class="form-group">
                <label class="form-label">Leave Type</label>
                <select v-model="reqForm.leave_type" class="form-input">
                  <option value="">Select type…</option>
                  <option>Annual</option>
                  <option>Sick</option>
                  <option>Family Responsibility</option>
                  <option>Unpaid</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">Duration</label>
                <div class="days-pill">
                  {{ computedDays }} day{{ computedDays !== 1 ? 's' : '' }}
                </div>
              </div>
              <div class="form-group">
                <label class="form-label">Start Date</label>
                <input v-model="reqForm.start_date" type="date" class="form-input" />
              </div>
              <div class="form-group">
                <label class="form-label">End Date</label>
                <input v-model="reqForm.end_date" type="date" class="form-input" />
              </div>
              <div class="form-group span-2">
                <label class="form-label">Reason <span class="form-hint">(optional)</span></label>
                <textarea v-model="reqForm.reason" rows="3" class="form-input" placeholder="Briefly describe your reason…"></textarea>
              </div>
            </div>

            <div v-if="submitError" class="info-box info-red mt-3">{{ submitError }}</div>
            <div v-if="submitSuccess" class="info-box info-green mt-3">Leave request submitted successfully.</div>
          </div>

          <div class="modal-footer">
            <button @click="closeApplyModal" class="btn btn-secondary btn-sm">Cancel</button>
            <button
              @click="submitLeaveRequest"
              :disabled="submitting || !reqForm.leave_type || !reqForm.start_date || !reqForm.end_date"
              class="btn btn-primary btn-sm"
            >
              {{ submitting ? 'Submitting…' : 'Submit Request' }}
            </button>
          </div>
        </div>
      </div>
    </teleport>

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

    // ── Tab state ───────────────────────────────────────
    const activeTab = ref(isEmployee ? 'balances' : 'team')

    // ── Modal state ─────────────────────────────────────
    const showApplyModal = ref(false)
    const closeApplyModal = () => {
      showApplyModal.value = false
      submitError.value = ''
      submitSuccess.value = false
    }

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
      activeTab,
      showApplyModal, closeApplyModal,
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
/* ── Root wrapper ─────────────────────────────────────────────────────────── */
.view-content {
  padding: 24px;
  max-width: 1280px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ── Page header ──────────────────────────────────────────────────────────── */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

/* ── Filter row (manager tab) ─────────────────────────────────────────────── */
.filter-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.filter-select { width: auto; min-width: 160px; }

/* ── Balance colors ───────────────────────────────────────────────────────── */
.bal-ok   { color: var(--color-success);  font-weight: 600; }
.bal-zero { color: var(--color-danger);   font-weight: 600; }

/* ── Reason cell (truncate long text) ─────────────────────────────────────── */
.reason-cell { max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* ── Inline approve/reject form ───────────────────────────────────────────── */
.inline-form {
  display: flex;
  gap: 6px;
  margin-top: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.inline-input { flex: 1; min-width: 120px; height: 28px; font-size: 12px; }

/* ── Docs-requested note in My Requests ───────────────────────────────────── */
.docs-note {
  font-size: var(--text-xs);
  color: #92400e;
  font-style: italic;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.rejection-note { font-size: var(--text-xs); color: var(--color-danger); font-style: italic; }

/* ── Duration pill inside modal ───────────────────────────────────────────── */
.days-pill {
  display: inline-flex;
  align-items: center;
  height: 36px;
  padding: 0 14px;
  background: var(--color-info-bg);
  color: var(--color-info);
  border-radius: var(--radius-full);
  font-size: var(--text-base);
  font-weight: 600;
}

/* ── Span-2 helper inside modal form-grid ─────────────────────────────────── */
.span-2 { grid-column: span 2; }

/* ── Spacing utility ──────────────────────────────────────────────────────── */
.mt-3 { margin-top: var(--space-3); }

/* ── Responsive ───────────────────────────────────────────────────────────── */
@media (max-width: 600px) {
  .filter-row { flex-direction: column; align-items: flex-start; }
  .filter-select { width: 100%; }
  .span-2 { grid-column: span 1; }
}
</style>
