<template>
  <div class="page-wrapper">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">Accountant Registrations</h1>
        <p class="page-subtitle">Review and action self-registration requests from accountants.</p>
      </div>
    </div>

    <div class="card" style="padding:0;overflow:hidden">
      <div v-if="loading" class="empty-state">
        <p>Loading…</p>
      </div>

      <template v-else-if="registrations.length">
        <table class="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Firm</th>
              <th>Phone</th>
              <th>Requested</th>
              <th>Status</th>
              <th style="text-align:right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="reg in registrations" :key="reg.id">
              <td class="font-medium">{{ reg.full_name }}</td>
              <td>{{ reg.email }}</td>
              <td>{{ reg.firm_name || '—' }}</td>
              <td>{{ reg.phone || '—' }}</td>
              <td>{{ formatDate(reg.requested_at) }}</td>
              <td>
                <span class="status-badge" :class="statusClass(reg.status)">{{ reg.status }}</span>
              </td>
              <td>
                <div class="actions" style="justify-content:flex-end;gap:6px">
                  <template v-if="reg.status === 'pending'">
                    <button @click="approve(reg)" class="btn-primary" style="font-size:12px;height:28px;padding:0 12px">
                      Approve
                    </button>
                    <button @click="openReject(reg)" class="btn-light danger" style="font-size:12px;height:28px;padding:0 12px">
                      Reject
                    </button>
                  </template>
                  <span v-else style="font-size:12px;color:var(--color-text-muted)">
                    {{ reg.rejection_reason ? `Rejected: ${reg.rejection_reason}` : '—' }}
                  </span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </template>

      <div v-else class="empty-state">
        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
          <circle cx="9" cy="7" r="4"/>
          <polyline points="16 11 18 13 22 9"/>
        </svg>
        <p>No registration requests yet.</p>
      </div>
    </div>

    <!-- Reject reason modal -->
    <div v-if="rejectTarget" class="modal-overlay">
      <div class="modal" style="max-width:440px">
        <div class="modal-header">
          <h2>Reject Registration</h2>
          <button @click="rejectTarget = null" class="modal-close">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <p style="font-size:13px;color:var(--color-text-muted);margin-bottom:12px">
            Provide a reason for rejecting <strong>{{ rejectTarget.full_name }}</strong>'s registration.
            This reason will be emailed to the applicant.
          </p>
          <div class="form-group">
            <label class="form-label">Reason <span style="color:var(--color-error)">*</span></label>
            <textarea v-model="rejectReason" class="form-input" rows="3" placeholder="e.g. Unable to verify credentials" style="resize:vertical"></textarea>
          </div>
          <div v-if="actionError" class="auth-error" style="margin-top:8px">{{ actionError }}</div>
        </div>
        <div class="modal-footer">
          <button @click="rejectTarget = null" class="btn-secondary">Cancel</button>
          <button @click="confirmReject" :disabled="actionLoading" class="btn-primary">
            {{ actionLoading ? 'Rejecting…' : 'Confirm Rejection' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'

export default {
  name: 'AccountantRegistrationsView',
  setup() {
    const auth   = useAuthStore()
    const toast  = useToastStore()

    const registrations = ref([])
    const loading       = ref(false)
    const rejectTarget  = ref(null)
    const rejectReason  = ref('')
    const actionLoading = ref(false)
    const actionError   = ref('')

    const authHeader = () => ({ headers: { Authorization: `Bearer ${auth.accessToken}` } })

    const load = async () => {
      loading.value = true
      try {
        const { data } = await axios.get('/accountant-registrations', authHeader())
        registrations.value = data
      } catch (e) {
        toast.error('Failed to load registrations')
      } finally {
        loading.value = false
      }
    }

    const approve = async (reg) => {
      if (!confirm(`Approve registration for ${reg.full_name}? An account will be created and they will be notified by email.`)) return
      try {
        await axios.patch(`/accountant-registrations/${reg.id}/review`, { status: 'approved' }, authHeader())
        toast.success(`${reg.full_name} approved — account created.`)
        await load()
      } catch (e) {
        toast.error(e.response?.data?.detail || 'Failed to approve')
      }
    }

    const openReject = (reg) => {
      rejectTarget.value = reg
      rejectReason.value = ''
      actionError.value  = ''
    }

    const confirmReject = async () => {
      if (!rejectReason.value.trim()) {
        actionError.value = 'Please provide a rejection reason.'
        return
      }
      actionLoading.value = true
      actionError.value   = ''
      try {
        await axios.patch(
          `/accountant-registrations/${rejectTarget.value.id}/review`,
          { status: 'rejected', reason: rejectReason.value.trim() },
          authHeader()
        )
        toast.success('Registration rejected.')
        rejectTarget.value = null
        await load()
      } catch (e) {
        actionError.value = e.response?.data?.detail || 'Failed to reject'
      } finally {
        actionLoading.value = false
      }
    }

    const formatDate = (iso) => {
      if (!iso) return '—'
      return new Date(iso).toLocaleDateString('en-ZA', { day: '2-digit', month: 'short', year: 'numeric' })
    }

    const statusClass = (status) => ({
      pending:  'badge-warning',
      approved: 'badge-success',
      rejected: 'badge-error',
    }[status] || '')

    onMounted(load)

    return { registrations, loading, rejectTarget, rejectReason, actionLoading, actionError, approve, openReject, confirmReject, formatDate, statusClass }
  }
}
</script>

<style scoped>
.page-subtitle {
  font-size: 13px;
  color: var(--color-text-muted);
  margin-top: 2px;
}

.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11.5px;
  font-weight: 600;
  text-transform: capitalize;
}
.badge-warning { background: #fef3c7; color: #92400e; }
.badge-success { background: #dcfce7; color: #166534; }
.badge-error   { background: #fee2e2; color: #991b1b; }

.auth-error {
  padding: 10px 12px;
  background: var(--color-error-bg);
  border: 1px solid var(--color-error-border);
  border-radius: 6px;
  font-size: 13px;
  color: #b91c1c;
}

.btn-light.danger { color: #b91c1c; border-color: #fca5a5; }
.btn-light.danger:hover { background: #fee2e2; }
</style>
