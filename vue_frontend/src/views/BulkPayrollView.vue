<template>
  <div class="bulk-content">

    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Bulk Payroll Run</h1>
        <div class="breadcrumb"><span>Payroll</span><span class="sep">/</span><span>Bulk Run</span></div>
      </div>
    </div>

    <!-- Config card -->
    <div class="card config-card">
      <h2 class="section-title">Run Settings</h2>
      <div class="config-row">
        <div class="form-group">
          <label class="form-label">Company</label>
          <select v-model.number="selectedCompany" class="form-input">
            <option :value="0">Select company</option>
            <option v-for="c in companies" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Month</label>
          <select v-model.number="selectedMonth" class="form-input">
            <option v-for="(name, idx) in months" :key="idx+1" :value="idx+1">{{ name }}</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Year</label>
          <input v-model.number="selectedYear" type="number" min="2020" max="2099" class="form-input" />
        </div>
        <div class="form-group actions-group">
          <label class="form-label">&nbsp;</label>
          <button @click="runPayroll" :disabled="loading || !selectedCompany" class="btn-primary">
            <span v-if="loading">Processing…</span>
            <span v-else>Run Payroll</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Results -->
    <div v-if="result" class="card results-card">
      <!-- Summary row -->
      <div class="summary-row">
        <div class="stat-box">
          <span class="stat-val">{{ result.total_employees }}</span>
          <span class="stat-label">Employees</span>
        </div>
        <div class="stat-box success">
          <span class="stat-val">{{ result.successful }}</span>
          <span class="stat-label">Processed</span>
        </div>
        <div class="stat-box" :class="result.failed > 0 ? 'error' : ''">
          <span class="stat-val">{{ result.failed }}</span>
          <span class="stat-label">Failed</span>
        </div>
        <div class="stat-box highlight">
          <span class="stat-val">R {{ fmt(result.total_net_pay) }}</span>
          <span class="stat-label">Total Net Pay</span>
        </div>
      </div>

      <!-- Approval workflow -->
      <div class="workflow-row" v-if="result.successful > 0">
        <div class="workflow-status">
          <span class="badge" :class="statusBadgeClass(periodStatus)">{{ periodStatusLabel }}</span>
          <span class="status-note">{{ statusNote }}</span>
        </div>
        <div class="workflow-actions">
          <button
            v-if="canSubmit"
            @click="submitForApproval" :disabled="approvalLoading"
            class="btn-secondary">{{ approvalLoading ? 'Submitting…' : 'Submit for Approval' }}
          </button>
          <button
            v-if="canApprove"
            @click="approvePayroll" :disabled="approvalLoading"
            class="btn-primary">{{ approvalLoading ? 'Approving…' : 'Approve Payroll' }}
          </button>
          <button
            v-if="canApprove"
            @click="showRejectInput = !showRejectInput"
            class="btn-danger-outline">Reject
          </button>
        </div>
      </div>
      <div v-if="showRejectInput" class="reject-row">
        <input v-model="rejectReason" class="form-input" placeholder="Reason for rejection (optional)" />
        <button @click="rejectPayroll" :disabled="approvalLoading" class="btn-danger">
          {{ approvalLoading ? 'Rejecting…' : 'Confirm Reject' }}
        </button>
      </div>
      <div v-if="approvalMsg" class="approval-msg" :class="approvalMsgType">{{ approvalMsg }}</div>

      <!-- Send emails -->
      <div class="email-row" v-if="result.successful > 0 && periodStatus === 'approved'">
        <button @click="sendPayslips" :disabled="sending" class="btn-secondary">
          {{ sending ? 'Sending…' : 'Send Payslips by Email' }}
        </button>
        <span v-if="emailResult" class="email-status" :class="emailResult.failed > 0 ? 'warn' : 'ok'">
          Sent {{ emailResult.sent }}, failed {{ emailResult.failed }}
          <span v-if="emailResult.failed > 0" :title="emailResult.errors?.join('\n')"> (hover for details)</span>
        </span>
        <span v-if="emailError" class="email-status warn">{{ emailError }}</span>
      </div>

      <!-- Publish to employee portals -->
      <div class="email-row" v-if="result.successful > 0 && periodStatus === 'approved'">
        <template v-if="!allPublished">
          <button @click="publishRun" :disabled="publishing" class="btn-secondary">
            {{ publishing ? 'Publishing…' : 'Publish All to Employee Portal' }}
          </button>
        </template>
        <template v-else>
          <button @click="unpublishRun" :disabled="publishing" class="btn-secondary btn-warning">
            {{ publishing ? 'Retracting…' : 'Unpublish from Portal' }}
          </button>
        </template>
        <span v-if="publishResult" class="email-status" :class="publishResult.skipped > 0 ? 'warn' : 'ok'">
          {{ publishResult.published }} published
          <span v-if="publishResult.skipped > 0">, {{ publishResult.skipped }} skipped (no portal account)</span>
        </span>
        <span v-if="unpublishResult" class="email-status ok">{{ unpublishResult }}</span>
      </div>

      <!-- Employee breakdown table -->
      <h3 class="table-heading">Employee Breakdown — {{ result.period }}</h3>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Employee</th>
              <th class="num">Basic Pay</th>
              <th class="num">Total Earnings</th>
              <th class="num">Deductions</th>
              <th class="num">Net Pay</th>
              <th class="status-col">Run</th>
              <th class="status-col">Portal</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="emp in result.employees" :key="emp.employee_id" :class="emp.status === 'error' ? 'row-error' : ''">
              <td>{{ emp.employee_name }}</td>
              <td class="num">R {{ fmt(emp.basic_pay) }}</td>
              <td class="num">R {{ fmt(emp.total_earnings) }}</td>
              <td class="num">R {{ fmt(emp.total_deductions) }}</td>
              <td class="num fw">R {{ fmt(emp.net_pay) }}</td>
              <td class="status-col">
                <span class="badge" :class="emp.status === 'success' ? 'badge-ok' : 'badge-err'">
                  {{ emp.status === 'success' ? 'OK' : 'Error' }}
                </span>
                <span v-if="emp.error" class="err-text" :title="emp.error"> ⚠</span>
              </td>
              <td class="status-col">
                <span v-if="emp.status !== 'success'" class="badge badge-gray">—</span>
                <span v-else-if="emp.distributed" class="badge badge-published">Published</span>
                <span v-else class="badge badge-gray">Draft</span>
              </td>
            </tr>
          </tbody>
          <tfoot>
            <tr>
              <td class="fw">Total</td>
              <td class="num fw">R {{ fmt(result.employees.filter(e=>e.status==='success').reduce((s,e)=>s+e.basic_pay,0)) }}</td>
              <td class="num fw">R {{ fmt(result.employees.filter(e=>e.status==='success').reduce((s,e)=>s+e.total_earnings,0)) }}</td>
              <td class="num fw">R {{ fmt(result.employees.filter(e=>e.status==='success').reduce((s,e)=>s+e.total_deductions,0)) }}</td>
              <td class="num fw">R {{ fmt(result.total_net_pay) }}</td>
              <td></td>
              <td class="status-col" style="font-size:11px;color:var(--color-text-muted)">
                {{ result.employees.filter(e=>e.distributed).length }}/{{ result.successful }}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>

    <!-- Error banner -->
    <div v-if="errorMsg" class="error-banner">{{ errorMsg }}</div>

  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December']

export default {
  name: 'BulkPayrollView',
  setup() {
    const auth = useAuthStore()
    const hasRole = (roles) => auth.roles?.some(r => roles.includes(r))

    const companies = ref([])
    const selectedCompany = ref(0)
    const selectedMonth = ref(new Date().getMonth() + 1)
    const selectedYear = ref(new Date().getFullYear())
    const loading = ref(false)
    const sending = ref(false)
    const result = ref(null)
    const errorMsg = ref('')
    const emailResult = ref(null)
    const emailError = ref('')

    // Approval workflow
    const periodStatus = ref('draft')
    const approvalLoading = ref(false)
    const approvalMsg = ref('')
    const approvalMsgType = ref('ok')
    const showRejectInput = ref(false)
    const rejectReason = ref('')

    // Portal publish
    const publishing = ref(false)
    const publishResult = ref(null)
    const unpublishResult = ref('')

    const canSubmit = computed(() => periodStatus.value === 'draft' && hasRole(['super_admin', 'accountant', 'manager']))
    const canApprove = computed(() => periodStatus.value === 'submitted' && hasRole(['super_admin', 'manager']))

    const allPublished = computed(() => {
      if (!result.value?.employees) return false
      const successful = result.value.employees.filter(e => e.status === 'success')
      return successful.length > 0 && successful.every(e => e.distributed)
    })

    const periodStatusLabel = computed(() => ({
      draft: 'Draft', submitted: 'Submitted for Approval', approved: 'Approved', rejected: 'Rejected', none: ''
    }[periodStatus.value] || periodStatus.value))

    const statusNote = computed(() => ({
      draft: 'Submit to send this run for client approval.',
      submitted: 'Awaiting approval from a client admin or super admin.',
      approved: 'This pay run is approved. You can now send payslips.',
      rejected: 'This pay run was rejected. Correct and resubmit.',
    }[periodStatus.value] || ''))

    const statusBadgeClass = (s) => ({
      draft: 'badge-gray', submitted: 'badge-yellow', approved: 'badge-ok', rejected: 'badge-err'
    }[s] || 'badge-gray')

    const fmt = (n) => Number(n || 0).toLocaleString('en-ZA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

    const loadCompanies = async () => {
      try {
        const { data } = await axios.get('/companies')
        companies.value = data
      } catch {}
    }

    const fetchPeriodStatus = async () => {
      if (!selectedCompany.value) return
      try {
        const { data } = await axios.get(`/companies/${selectedCompany.value}/payroll/status`, {
          params: { year: selectedYear.value, month: selectedMonth.value }
        })
        periodStatus.value = data.status
      } catch { periodStatus.value = 'none' }
    }

    const runPayroll = async () => {
      errorMsg.value = ''
      result.value = null
      emailResult.value = null
      emailError.value = ''
      approvalMsg.value = ''
      publishResult.value = null
      unpublishResult.value = ''
      periodStatus.value = 'draft'
      loading.value = true
      try {
        const { data } = await axios.post(`/companies/${selectedCompany.value}/payroll/bulk`, {
          year: selectedYear.value,
          month: selectedMonth.value
        })
        result.value = data
        await fetchPeriodStatus()
      } catch (e) {
        errorMsg.value = e?.response?.data?.detail || e?.message || 'Bulk payroll run failed'
      } finally {
        loading.value = false
      }
    }

    const submitForApproval = async () => {
      approvalLoading.value = true
      approvalMsg.value = ''
      try {
        await axios.post(`/companies/${selectedCompany.value}/payroll/submit`, { year: selectedYear.value, month: selectedMonth.value })
        await fetchPeriodStatus()
        approvalMsg.value = 'Pay run submitted for approval.'
        approvalMsgType.value = 'ok'
      } catch (e) {
        approvalMsg.value = e?.response?.data?.detail || 'Submit failed'
        approvalMsgType.value = 'err'
      } finally { approvalLoading.value = false }
    }

    const approvePayroll = async () => {
      approvalLoading.value = true
      approvalMsg.value = ''
      try {
        await axios.post(`/companies/${selectedCompany.value}/payroll/approve`, { year: selectedYear.value, month: selectedMonth.value })
        await fetchPeriodStatus()
        approvalMsg.value = 'Pay run approved. You can now send payslips.'
        approvalMsgType.value = 'ok'
      } catch (e) {
        approvalMsg.value = e?.response?.data?.detail || 'Approval failed'
        approvalMsgType.value = 'err'
      } finally { approvalLoading.value = false }
    }

    const rejectPayroll = async () => {
      approvalLoading.value = true
      approvalMsg.value = ''
      try {
        await axios.post(`/companies/${selectedCompany.value}/payroll/reject`, {
          year: selectedYear.value, month: selectedMonth.value, reason: rejectReason.value
        })
        await fetchPeriodStatus()
        showRejectInput.value = false
        rejectReason.value = ''
        approvalMsg.value = 'Pay run rejected.'
        approvalMsgType.value = 'err'
      } catch (e) {
        approvalMsg.value = e?.response?.data?.detail || 'Rejection failed'
        approvalMsgType.value = 'err'
      } finally { approvalLoading.value = false }
    }

    const sendPayslips = async () => {
      emailResult.value = null
      emailError.value = ''
      sending.value = true
      try {
        const { data } = await axios.post(`/companies/${selectedCompany.value}/payroll/send-payslips`, {
          year: selectedYear.value,
          month: selectedMonth.value
        })
        emailResult.value = data
      } catch (e) {
        const detail = e?.response?.data?.detail || e?.message || 'Failed to send emails'
        emailError.value = detail
      } finally {
        sending.value = false
      }
    }

    const publishRun = async () => {
      if (!result.value?.payroll_run_id) return
      publishing.value = true
      publishResult.value = null
      unpublishResult.value = ''
      try {
        const { data } = await axios.post(`/payroll/runs/${result.value.payroll_run_id}/publish`)
        publishResult.value = data
        result.value.employees.forEach(e => {
          if (e.status === 'success') e.distributed = true
        })
      } catch (e) {
        publishResult.value = null
        errorMsg.value = e?.response?.data?.detail || 'Failed to publish payslips'
      } finally {
        publishing.value = false
      }
    }

    const unpublishRun = async () => {
      if (!result.value?.payroll_run_id) return
      publishing.value = true
      publishResult.value = null
      unpublishResult.value = ''
      try {
        const { data } = await axios.post(`/payroll/runs/${result.value.payroll_run_id}/unpublish`)
        unpublishResult.value = `${data.retracted} payslip${data.retracted !== 1 ? 's' : ''} retracted from portal.`
        result.value.employees.forEach(e => {
          if (e.status === 'success') e.distributed = false
        })
      } catch (e) {
        errorMsg.value = e?.response?.data?.detail || 'Failed to unpublish payslips'
      } finally {
        publishing.value = false
      }
    }

    onMounted(loadCompanies)

    return {
      companies, selectedCompany, selectedMonth, selectedYear, months: MONTHS,
      loading, sending, result, errorMsg, emailResult, emailError,
      periodStatus, approvalLoading, approvalMsg, approvalMsgType, showRejectInput, rejectReason,
      publishing, publishResult, unpublishResult, allPublished,
      canSubmit, canApprove, periodStatusLabel, statusNote, statusBadgeClass,
      fmt, runPayroll, sendPayslips, publishRun, unpublishRun,
      submitForApproval, approvePayroll, rejectPayroll, hasRole
    }
  }
}
</script>

<style scoped>
.bulk-content {
  padding: 24px;
  max-width: 1100px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-title { font-size: 16px; font-weight: 500; color: var(--color-text-base); margin: 0 0 4px; }
.breadcrumb { font-size: 11px; color: var(--color-text-muted); }
.sep { margin: 0 6px; }

.card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 20px 24px;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-base);
  margin: 0 0 16px;
}

.config-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr auto;
  gap: 16px;
  align-items: end;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.actions-group { min-width: 140px; }

/* Summary stats */
.summary-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-box {
  background: var(--color-bg-page);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stat-box.success { border-color: #bbf7d0; background: #f0fdf4; }
.stat-box.error { border-color: #fecaca; background: #fef2f2; }
.stat-box.highlight { border-color: #bfdbfe; background: #eff6ff; }

.stat-val { font-size: 22px; font-weight: 700; color: var(--color-text-base); line-height: 1; }
.stat-label { font-size: 11px; color: var(--color-text-muted); }

/* Email / publish rows */
.email-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.email-status { font-size: 12.5px; }
.email-status.ok { color: #16a34a; }
.email-status.warn { color: #b45309; }

/* Table */
.table-heading {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin: 0 0 10px;
}
.table-wrap { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th {
  padding: 8px 12px;
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-page);
}
.data-table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-base);
}
.data-table tfoot td {
  border-top: 2px solid var(--color-border);
  border-bottom: none;
  background: var(--color-bg-page);
}
.data-table tr:last-child td { border-bottom: none; }
.num { text-align: right; font-variant-numeric: tabular-nums; }
.fw { font-weight: 600; }
.status-col { text-align: center; }
.row-error td { background: #fef2f2; }

.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
}
.badge-ok { background: #dcfce7; color: #15803d; }
.badge-err { background: #fee2e2; color: #b91c1c; }
.badge-gray { background: var(--color-bg-page); color: var(--color-text-muted); border: 1px solid var(--color-border); }
.badge-yellow { background: #fef9c3; color: #a16207; }
.badge-published { background: #dbeafe; color: #1d4ed8; }
.err-text { cursor: help; color: #f59e0b; margin-left: 4px; }

/* Approval workflow */
.workflow-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.workflow-status { display: flex; align-items: center; gap: 10px; }
.status-note { font-size: 12px; color: var(--color-text-muted); }
.workflow-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.btn-danger-outline {
  display: inline-flex; align-items: center; justify-content: center;
  padding: 0 14px; height: 34px; border-radius: 6px; font-size: 13px; font-weight: 500;
  border: 1px solid #fca5a5; background: transparent; color: #b91c1c; cursor: pointer;
  transition: background 0.12s;
}
.btn-danger-outline:hover { background: #fee2e2; }
.btn-warning {
  border-color: #fbbf24 !important;
  color: #92400e;
}
.reject-row { display: flex; gap: 10px; margin-bottom: 10px; }
.reject-row .form-input { flex: 1; }
.approval-msg { font-size: 13px; padding: 8px 12px; border-radius: 6px; margin-bottom: 8px; }
.approval-msg.ok { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
.approval-msg.err { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }

.error-banner {
  padding: 12px 16px;
  background: var(--color-error-bg, #fef2f2);
  border: 1px solid var(--color-error-border, #fecaca);
  border-radius: 8px;
  font-size: 13px;
  color: #b91c1c;
}

@media (max-width: 768px) {
  .config-row { grid-template-columns: 1fr 1fr; }
  .summary-row { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 480px) {
  .config-row { grid-template-columns: 1fr; }
  .summary-row { grid-template-columns: 1fr 1fr; }
}
</style>
