<template>
  <div class="portal-content">

    <div class="page-header">
      <div>
        <h1 class="page-title">My Portal</h1>
        <div class="breadcrumb">
          <span>Employee</span>
          <span class="sep">/</span>
          <span>Dashboard</span>
        </div>
      </div>
      <div class="header-actions">
        <router-link to="/leave" class="btn-primary">Request Leave</router-link>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>Loading your portal…</span>
    </div>

    <div v-else-if="noProfile" class="card warn-card">
      <svg class="warn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
        <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
      <div>
        <p class="warn-title">No employee profile linked</p>
        <p class="warn-sub">Your account has not been linked to an employee record. Please contact your administrator.</p>
      </div>
    </div>

    <template v-else>

      <!-- Profile card -->
      <div class="card profile-card">
        <div class="profile-avatar">{{ avatarInitials }}</div>
        <div class="profile-details">
          <p class="profile-name">{{ profile.first_names }} {{ profile.last_name }}</p>
          <p class="profile-position">{{ profile.position || '—' }}</p>
          <div class="profile-meta">
            <span class="meta-item">
              <span class="meta-label">Employee #</span>
              <span class="meta-value">{{ profile.employee_no || '—' }}</span>
            </span>
            <span class="meta-sep">·</span>
            <span class="meta-item">
              <span class="meta-label">Start date</span>
              <span class="meta-value">{{ fmtDate(profile.emp_date) }}</span>
            </span>
            <span class="meta-sep" v-if="companyName">·</span>
            <span class="meta-item" v-if="companyName">
              <span class="meta-label">Company</span>
              <span class="meta-value">{{ companyName }}</span>
            </span>
          </div>
        </div>
      </div>

      <!-- Leave balances -->
      <section class="section">
        <h2 class="section-title">Leave Balances</h2>
        <div v-if="leaveBalances.length === 0" class="empty-state">No leave balances on record.</div>
        <div v-else class="balance-grid">
          <div v-for="b in leaveBalances" :key="b.leave_type" class="card balance-card">
            <p class="balance-type">{{ b.leave_type }}</p>
            <div class="balance-row">
              <div class="balance-stat">
                <span class="balance-val">{{ b.days_allocated }}</span>
                <span class="balance-label">Allocated</span>
              </div>
              <div class="balance-stat">
                <span class="balance-val taken">{{ b.days_taken }}</span>
                <span class="balance-label">Taken</span>
              </div>
              <div class="balance-stat">
                <span class="balance-val remaining">{{ b.days_remaining }}</span>
                <span class="balance-label">Remaining</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Payslips -->
      <section class="section">
        <h2 class="section-title">My Payslips</h2>
        <div class="card">
          <div v-if="payslips.length === 0" class="empty-state">No payslips found.</div>
          <template v-else>
            <div class="table-wrap">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Period</th>
                    <th>Net Pay</th>
                    <th>Status</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="slip in pagedPayslips" :key="slip.id">
                    <td>{{ slip.period || slip.period_start || '—' }}</td>
                    <td>{{ fmtMoney(slip.net_pay) }}</td>
                    <td>
                      <span class="badge" :class="statusBadge(slip.status)">{{ slip.status || 'N/A' }}</span>
                    </td>
                    <td>
                      <button @click="downloadPayslip(slip.id)" :disabled="downloading === slip.id" class="btn-light btn-sm">
                        {{ downloading === slip.id ? 'Downloading…' : 'Download' }}
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="pagination" v-if="payslips.length > pageSize">
              <button @click="prevPage" :disabled="page === 0" class="btn-light page-btn">← Prev</button>
              <span class="page-info">Page {{ page + 1 }} of {{ totalPages }}</span>
              <button @click="nextPage" :disabled="page >= totalPages - 1" class="btn-light page-btn">Next →</button>
            </div>
          </template>
        </div>
      </section>

      <!-- Leave requests -->
      <section class="section">
        <h2 class="section-title">My Leave Requests</h2>
        <div class="card">
          <div v-if="leaveRequests.length === 0" class="empty-state">No leave requests yet.</div>
          <div v-else class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>From</th>
                  <th>To</th>
                  <th>Days</th>
                  <th>Status</th>
                  <th>Submitted</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="req in leaveRequests" :key="req.id">
                  <td>{{ req.leave_type }}</td>
                  <td>{{ fmtDate(req.start_date) }}</td>
                  <td>{{ fmtDate(req.end_date) }}</td>
                  <td>{{ req.days_requested }}</td>
                  <td>
                    <span class="badge" :class="statusBadge(req.status)">{{ req.status }}</span>
                  </td>
                  <td>{{ fmtDate(req.created_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- Documents -->
      <section class="section">
        <h2 class="section-title">My Documents</h2>
        <div class="card">
          <div class="doc-upload-form">
            <div class="form-grid-3">
              <div class="form-group">
                <label class="form-label">Document Type</label>
                <select v-model="docForm.document_type" class="form-input">
                  <option value="">Select type</option>
                  <option>ID / Passport</option>
                  <option>Proof of Address</option>
                  <option>Bank Statement</option>
                  <option>Tax Certificate</option>
                  <option>Contract</option>
                  <option>Other</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">Description (optional)</label>
                <input v-model="docForm.description" type="text" class="form-input" placeholder="Brief description…" />
              </div>
              <div class="form-group">
                <label class="form-label">File (max 5 MB)</label>
                <input ref="fileInput" type="file" class="form-input file-input" @change="onFileChange" />
              </div>
            </div>
            <div class="form-actions-row">
              <span v-if="docUploadError" class="form-error">{{ docUploadError }}</span>
              <button @click="uploadDocument" :disabled="docUploading || !docForm.document_type || !docForm.file" class="btn-primary btn-sm">
                {{ docUploading ? 'Uploading…' : 'Upload Document' }}
              </button>
            </div>
            <div v-if="docUploadSuccess" class="success-banner">Document uploaded and pending review.</div>
          </div>

          <div v-if="documents.length > 0" class="doc-list">
            <div v-for="doc in documents" :key="doc.id" class="doc-row">
              <div class="doc-info">
                <span class="doc-name">{{ doc.file_name }}</span>
                <span class="doc-type">{{ doc.document_type }}</span>
              </div>
              <div class="doc-meta">
                <span class="badge" :class="statusBadge(doc.status)">{{ doc.status }}</span>
                <span v-if="doc.status === 'rejected' && doc.rejection_reason" class="rejection-reason">{{ doc.rejection_reason }}</span>
                <button @click="downloadDoc(doc.id, doc.file_name)" class="btn-light btn-sm">Download</button>
              </div>
            </div>
          </div>
          <div v-else-if="!docUploading" class="empty-state" style="padding: 16px 0 0;">No documents uploaded yet.</div>
        </div>
      </section>

      <!-- Banking Change Request -->
      <section class="section">
        <h2 class="section-title">Banking Details</h2>
        <div class="card">
          <!-- Current banking details -->
          <div class="banking-current">
            <p class="banking-label">Current Details</p>
            <div class="banking-fields">
              <span class="banking-field"><span class="meta-label">Bank</span> <span class="meta-value">{{ profile.bank_name || '—' }}</span></span>
              <span class="banking-field"><span class="meta-label">Account</span> <span class="meta-value">{{ profile.bank_account_last4 ? '•••• ' + profile.bank_account_last4 : (profile.account_number || '—') }}</span></span>
              <span class="banking-field"><span class="meta-label">Type</span> <span class="meta-value">{{ profile.account_type || '—' }}</span></span>
              <span class="banking-field"><span class="meta-label">Branch</span> <span class="meta-value">{{ profile.branch_code || '—' }}</span></span>
            </div>
          </div>

          <!-- Pending banking change -->
          <div v-if="pendingBankingChange" class="pending-change-banner">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="pending-icon">
              <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
            </svg>
            <div>
              <p class="pending-title">Change request pending review</p>
              <p class="pending-sub">
                {{ pendingBankingChange.new_bank_name }} · {{ pendingBankingChange.new_account_number }} · {{ pendingBankingChange.new_account_type }}
              </p>
            </div>
          </div>

          <!-- Request change form -->
          <template v-else>
            <div class="banking-divider"></div>
            <p class="banking-label">Request a Change</p>
            <div class="form-grid-2">
              <div class="form-group">
                <label class="form-label">New Bank Name</label>
                <input v-model="bankForm.new_bank_name" type="text" class="form-input" placeholder="e.g. FNB" />
              </div>
              <div class="form-group">
                <label class="form-label">New Account Number</label>
                <input v-model="bankForm.new_account_number" type="text" class="form-input" placeholder="Account number" />
              </div>
              <div class="form-group">
                <label class="form-label">Account Type</label>
                <select v-model="bankForm.new_account_type" class="form-input">
                  <option value="">Select type</option>
                  <option>Cheque</option>
                  <option>Savings</option>
                  <option>Transmission</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">Branch Code</label>
                <input v-model="bankForm.new_branch_code" type="text" class="form-input" placeholder="6-digit code" />
              </div>
            </div>
            <div class="form-actions-row" style="margin-top: 12px;">
              <span v-if="bankChangeError" class="form-error">{{ bankChangeError }}</span>
              <button @click="submitBankingChange" :disabled="bankSubmitting || !bankForm.new_bank_name || !bankForm.new_account_number" class="btn-primary btn-sm">
                {{ bankSubmitting ? 'Submitting…' : 'Submit Change Request' }}
              </button>
            </div>
            <div v-if="bankChangeSuccess" class="success-banner">Banking change request submitted for review.</div>
          </template>
        </div>
      </section>

    </template>

  </div>
</template>

<script>
import { ref, computed, onMounted, reactive } from 'vue'
import axios from 'axios'

export default {
  name: 'EmployeePortalView',
  setup() {
    const loading = ref(true)
    const noProfile = ref(false)
    const profile = ref({})
    const payslips = ref([])
    const leaveBalances = ref([])
    const leaveRequests = ref([])
    const downloading = ref(null)
    const page = ref(0)
    const pageSize = 10

    // Documents
    const documents = ref([])
    const fileInput = ref(null)
    const docForm = reactive({ document_type: '', description: '', file: null })
    const docUploading = ref(false)
    const docUploadError = ref('')
    const docUploadSuccess = ref(false)

    const onFileChange = (e) => { docForm.file = e.target.files[0] || null }

    const uploadDocument = async () => {
      docUploadError.value = ''
      docUploadSuccess.value = false
      if (!docForm.file) return
      if (docForm.file.size > 5 * 1024 * 1024) { docUploadError.value = 'File must be under 5 MB.'; return }
      docUploading.value = true
      try {
        const fd = new FormData()
        fd.append('file', docForm.file)
        fd.append('document_type', docForm.document_type)
        if (docForm.description) fd.append('description', docForm.description)
        await axios.post('/me/documents', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
        docUploadSuccess.value = true
        docForm.document_type = ''
        docForm.description = ''
        docForm.file = null
        if (fileInput.value) fileInput.value.value = ''
        await loadDocuments()
      } catch (e) {
        docUploadError.value = e?.response?.data?.detail || 'Upload failed.'
      } finally {
        docUploading.value = false
      }
    }

    const loadDocuments = async () => {
      try { const { data } = await axios.get('/me/documents'); documents.value = data || [] } catch {}
    }

    const downloadDoc = async (id, name) => {
      try {
        const { data } = await axios.get(`/me/documents/${id}/download`)
        const a = document.createElement('a')
        a.href = data.url
        a.setAttribute('download', name)
        document.body.appendChild(a)
        a.click()
        a.remove()
      } catch { alert('Failed to download document.') }
    }

    // Banking change request
    const bankingChanges = ref([])
    const pendingBankingChange = computed(() => bankingChanges.value.find(b => b.status === 'pending') || null)
    const bankForm = reactive({ new_bank_name: '', new_account_number: '', new_account_type: '', new_branch_code: '' })
    const bankSubmitting = ref(false)
    const bankChangeError = ref('')
    const bankChangeSuccess = ref(false)

    const loadBankingChanges = async () => {
      try { const { data } = await axios.get('/banking-changes/my'); bankingChanges.value = data || [] } catch {}
    }

    const submitBankingChange = async () => {
      bankChangeError.value = ''
      bankChangeSuccess.value = false
      bankSubmitting.value = true
      try {
        await axios.post('/banking-changes', {
          new_bank_name: bankForm.new_bank_name,
          new_account_number: bankForm.new_account_number,
          new_account_type: bankForm.new_account_type || undefined,
          new_branch_code: bankForm.new_branch_code || undefined
        })
        bankChangeSuccess.value = true
        bankForm.new_bank_name = ''
        bankForm.new_account_number = ''
        bankForm.new_account_type = ''
        bankForm.new_branch_code = ''
        await loadBankingChanges()
      } catch (e) {
        bankChangeError.value = e?.response?.data?.detail || 'Failed to submit request.'
      } finally {
        bankSubmitting.value = false
      }
    }

    const companyName = computed(() => {
      if (payslips.value.length > 0) return payslips.value[0].company_name || ''
      return ''
    })

    const avatarInitials = computed(() => {
      const f = profile.value.first_names || ''
      const l = profile.value.last_name || ''
      return ((f[0] || '') + (l[0] || '')).toUpperCase() || '?'
    })

    const totalPages = computed(() => Math.max(1, Math.ceil(payslips.value.length / pageSize)))

    const pagedPayslips = computed(() => {
      const start = page.value * pageSize
      return payslips.value.slice(start, start + pageSize)
    })

    const prevPage = () => { if (page.value > 0) page.value-- }
    const nextPage = () => { if (page.value < totalPages.value - 1) page.value++ }

    const fmtMoney = (n) => 'R ' + Number(n || 0).toLocaleString('en-ZA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

    const fmtDate = (s) => {
      if (!s) return '—'
      try { return new Date(s).toLocaleDateString('en-ZA', { year: 'numeric', month: 'short', day: '2-digit' }) }
      catch { return s }
    }

    const statusBadge = (s) => {
      const map = {
        approved: 'badge-green', paid: 'badge-green',
        rejected: 'badge-red', cancelled: 'badge-red',
        pending: 'badge-yellow',
        processed: 'badge-blue',
      }
      return map[(s || '').toLowerCase()] || 'badge-gray'
    }

    const downloadPayslip = async (id) => {
      downloading.value = id
      try {
        const res = await axios.get(`/payroll-records/${id}/payslip`, { responseType: 'blob' })
        const url = window.URL.createObjectURL(new Blob([res.data]))
        const a = document.createElement('a')
        a.href = url
        a.setAttribute('download', `payslip_${id}.pdf`)
        document.body.appendChild(a)
        a.click()
        a.remove()
        window.URL.revokeObjectURL(url)
      } catch (e) {
        alert('Failed to download payslip.')
      } finally {
        downloading.value = null
      }
    }

    const load = async () => {
      loading.value = true
      try {
        const [profileRes, payslipRes, leaveRes] = await Promise.allSettled([
          axios.get('/me/profile'),
          axios.get('/me/payslips'),
          axios.get('/me/leave')
        ])

        if (profileRes.status === 'fulfilled') {
          profile.value = profileRes.value.data
        } else {
          noProfile.value = true
        }

        if (payslipRes.status === 'fulfilled') {
          payslips.value = payslipRes.value.data || []
        }

        if (leaveRes.status === 'fulfilled') {
          const d = leaveRes.value.data
          leaveBalances.value = d.balances || []
          leaveRequests.value = d.requests || []
        }

        await Promise.allSettled([loadDocuments(), loadBankingChanges()])
      } catch {
        noProfile.value = true
      } finally {
        loading.value = false
      }
    }

    onMounted(load)

    return {
      loading, noProfile, profile, payslips, leaveBalances, leaveRequests,
      downloading, page, pageSize, totalPages, pagedPayslips,
      companyName, avatarInitials,
      prevPage, nextPage,
      fmtMoney, fmtDate, statusBadge, downloadPayslip,
      // Documents
      documents, fileInput, docForm, docUploading, docUploadError, docUploadSuccess,
      onFileChange, uploadDocument, downloadDoc,
      // Banking
      bankingChanges, pendingBankingChange, bankForm,
      bankSubmitting, bankChangeError, bankChangeSuccess, submitBankingChange
    }
  }
}
</script>

<style scoped>
.portal-content {
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

.breadcrumb {
  font-size: 11px;
  color: var(--color-text-muted);
}

.sep { margin: 0 6px; }

.header-actions { display: flex; gap: 10px; }

.loading-state {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--color-text-muted);
  font-size: 13px;
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

.card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 20px;
}

.warn-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  background: #fffbeb;
  border-color: #fde68a;
  padding: 16px 20px;
}

.warn-icon {
  width: 22px;
  height: 22px;
  color: #d97706;
  flex-shrink: 0;
  margin-top: 2px;
}

.warn-title {
  font-size: 13px;
  font-weight: 600;
  color: #92400e;
  margin: 0 0 4px;
}

.warn-sub {
  font-size: 12px;
  color: #92400e;
  margin: 0;
}

.profile-card {
  display: flex;
  align-items: center;
  gap: 20px;
}

.profile-avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--color-accent);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
  flex-shrink: 0;
}

.profile-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-base);
  margin: 0 0 2px;
}

.profile-position {
  font-size: 12px;
  color: var(--color-text-muted);
  margin: 0 0 8px;
}

.profile-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.meta-item { display: flex; gap: 4px; font-size: 12px; }
.meta-label { color: var(--color-text-muted); }
.meta-value { color: var(--color-text-base); font-weight: 500; }
.meta-sep { color: var(--color-border); }

.section { display: flex; flex-direction: column; gap: 10px; }

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0;
}

.balance-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 14px;
}

.balance-card { padding: 16px; }

.balance-type {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-base);
  margin: 0 0 12px;
}

.balance-row {
  display: flex;
  gap: 16px;
}

.balance-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.balance-val {
  font-size: 22px;
  font-weight: 700;
  color: var(--color-text-base);
  line-height: 1;
}

.balance-val.taken { color: #dc2626; }
.balance-val.remaining { color: #15803d; }

.balance-label {
  font-size: 10px;
  color: var(--color-text-muted);
  margin-top: 2px;
}

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
}

.data-table tbody tr:last-child td { border-bottom: none; }
.data-table tbody tr:hover td { background: var(--color-bg-page); }

.badge {
  display: inline-block;
  padding: 2px 9px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.badge-green { background: #dcfce7; color: #15803d; }
.badge-red { background: #fee2e2; color: #b91c1c; }
.badge-yellow { background: #fef9c3; color: #854d0e; }
.badge-blue { background: #dbeafe; color: #1d4ed8; }
.badge-gray { background: var(--color-bg-page); color: var(--color-text-muted); }

.btn-sm { padding: 4px 12px; font-size: 12px; }

.pagination {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 14px 0;
  border-top: 1px solid var(--color-border);
  margin-top: 4px;
}

.page-info { font-size: 12px; color: var(--color-text-muted); }
.page-btn { padding: 4px 12px; font-size: 12px; }

.empty-state {
  font-size: 13px;
  color: var(--color-text-muted);
  padding: 24px 0;
  text-align: center;
}

/* Document upload */
.doc-upload-form { margin-bottom: 16px; }
.form-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.form-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.form-group { display: flex; flex-direction: column; gap: 5px; }
.form-label { font-size: 11.5px; font-weight: 500; color: var(--color-text-muted); }
.file-input { padding: 5px 8px; }
.form-actions-row { display: flex; align-items: center; justify-content: flex-end; gap: 12px; margin-top: 12px; }
.form-error { font-size: 12px; color: #dc2626; }
.success-banner { margin-top: 10px; padding: 9px 14px; background: #dcfce7; border: 1px solid #86efac; border-radius: 7px; font-size: 12.5px; color: #15803d; }

.doc-list { display: flex; flex-direction: column; gap: 8px; border-top: 1px solid var(--color-border); padding-top: 14px; }
.doc-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 8px 0; border-bottom: 1px solid var(--color-border); }
.doc-row:last-child { border-bottom: none; }
.doc-info { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.doc-name { font-size: 13px; font-weight: 500; color: var(--color-text-base); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.doc-type { font-size: 11px; color: var(--color-text-muted); }
.doc-meta { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.rejection-reason { font-size: 11.5px; color: #b91c1c; font-style: italic; max-width: 160px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* Banking change */
.banking-current { margin-bottom: 4px; }
.banking-label { font-size: 11.5px; font-weight: 600; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.04em; margin: 0 0 10px; }
.banking-fields { display: flex; gap: 20px; flex-wrap: wrap; }
.banking-field { display: flex; gap: 6px; font-size: 13px; }
.banking-divider { height: 1px; background: var(--color-border); margin: 16px 0; }

.pending-change-banner { display: flex; align-items: flex-start; gap: 12px; background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 12px 16px; margin-top: 12px; }
.pending-icon { width: 20px; height: 20px; color: #d97706; flex-shrink: 0; margin-top: 2px; }
.pending-title { font-size: 13px; font-weight: 600; color: #92400e; margin: 0 0 2px; }
.pending-sub { font-size: 12px; color: #92400e; margin: 0; }

@media (max-width: 700px) {
  .profile-card { flex-direction: column; align-items: flex-start; }
  .balance-grid { grid-template-columns: 1fr 1fr; }
  .form-grid-3 { grid-template-columns: 1fr; }
  .form-grid-2 { grid-template-columns: 1fr; }
  .banking-fields { flex-direction: column; gap: 6px; }
}
</style>
