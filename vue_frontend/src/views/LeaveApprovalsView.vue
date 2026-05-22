<template>
  <div class="view-content">

    <!-- ── Page header ─────────────────────────────────────────────────────── -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Leave Approvals</h1>
        <div class="breadcrumb">
          <span>Approvals</span><span class="sep">/</span><span>Leave</span>
        </div>
      </div>
      <button @click="load" :disabled="loading" class="btn btn-secondary btn-sm">
        {{ loading ? 'Loading…' : 'Refresh' }}
      </button>
    </div>

    <!-- ── Loading ─────────────────────────────────────────────────────────── -->
    <SkeletonTable v-if="loading" :rows="6" :cols="9" />

    <!-- ── Empty ───────────────────────────────────────────────────────────── -->
    <div v-else-if="requests.length === 0" class="card">
      <div class="empty-state">
        <p class="empty-title">All caught up</p>
        <p>There are no pending leave requests to review.</p>
      </div>
    </div>

    <!-- ── Table ───────────────────────────────────────────────────────────── -->
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
              <th class="col-right">Days</th>
              <th>Reason</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in requests" :key="r.id">
              <td class="cell-primary">{{ r.employee_name }}</td>
              <td class="cell-muted">{{ r.company_name || '—' }}</td>
              <td>{{ r.leave_type }}</td>
              <td class="cell-muted">{{ fmtDate(r.start_date) }}</td>
              <td class="cell-muted">{{ fmtDate(r.end_date) }}</td>
              <td class="col-right cell-muted">{{ r.days_requested }}</td>
              <td class="reason-cell">
                <span
                  v-if="r.status === 'request_documentation' && r.documentation_requested_reason"
                  class="docs-note"
                >
                  Docs requested: {{ r.documentation_requested_reason }}
                </span>
                <span v-else class="cell-muted">{{ r.reason || '—' }}</span>
              </td>
              <td>
                <span class="badge" :class="statusBadge(r.status)">{{ statusLabel(r.status) }}</span>
              </td>
              <td>
                <!-- Awaiting docs — no further action -->
                <span v-if="r.status === 'request_documentation'" class="cell-muted text-xs awaiting">
                  Awaiting employee docs
                </span>

                <!-- Standard action buttons -->
                <div v-else class="col-actions">
                  <button
                    v-if="r.status === 'pending'"
                    @click="markUnderReview(r)"
                    :disabled="r._acting"
                    class="btn btn-light btn-sm"
                  >Review</button>
                  <button @click="approve(r)" :disabled="r._acting" class="btn btn-primary btn-sm">Approve</button>
                  <button @click="startReject(r)" :disabled="r._acting" class="btn btn-light btn-sm">Reject</button>
                  <button @click="startRequestDocs(r)" :disabled="r._acting" class="btn btn-secondary btn-sm">Req. Docs</button>
                </div>

                <!-- Inline reject form -->
                <div v-if="r._rejecting" class="inline-form">
                  <input
                    v-model="r._rejectNote"
                    type="text"
                    class="form-input inline-input"
                    placeholder="Rejection note…"
                    @keyup.enter="confirmReject(r)"
                  />
                  <button
                    @click="confirmReject(r)"
                    :disabled="r._acting"
                    class="btn btn-secondary btn-sm"
                  >Confirm</button>
                  <button @click="r._rejecting = false" class="btn btn-light btn-sm">Cancel</button>
                </div>

                <!-- Inline request-docs form -->
                <div v-if="r._requestingDocs" class="inline-form">
                  <input
                    v-model="r._docsReason"
                    type="text"
                    class="form-input inline-input"
                    placeholder="What documentation is needed?"
                    @keyup.enter="confirmRequestDocs(r)"
                  />
                  <button
                    @click="confirmRequestDocs(r)"
                    :disabled="r._acting"
                    class="btn btn-secondary btn-sm"
                  >Send</button>
                  <button @click="r._requestingDocs = false" class="btn btn-light btn-sm">Cancel</button>
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
import { useLeaveFormatting } from '../composables/useLeaveFormatting'
import SkeletonTable from '../components/ui/SkeletonTable.vue'

export default {
  name: 'LeaveApprovalsView',
  components: { SkeletonTable },
  setup() {
    const { fmtDate, statusLabel, statusBadge } = useLeaveFormatting()
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

/* ── Reason cell ──────────────────────────────────────────────────────────── */
.reason-cell { max-width: 200px; }

/* ── Docs-requested note ──────────────────────────────────────────────────── */
.docs-note {
  font-size: var(--text-xs);
  color: #92400e;
  font-style: italic;
}

/* ── Inline action / confirm forms ───────────────────────────────────────── */
.inline-form {
  display: flex;
  gap: 6px;
  margin-top: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.inline-input { flex: 1; min-width: 140px; height: 28px; font-size: 12px; }

/* ── Awaiting label ───────────────────────────────────────────────────────── */
.awaiting { white-space: nowrap; }
</style>
