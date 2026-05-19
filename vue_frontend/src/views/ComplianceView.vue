<template>
  <div class="compliance-content">

    <div class="page-header">
      <div>
        <h1 class="page-title">Statutory Compliance</h1>
        <div class="breadcrumb">
          <span>Admin</span>
          <span class="sep">/</span>
          <span>Compliance</span>
        </div>
      </div>
    </div>

    <!-- Filter bar -->
    <div class="filter-bar">
      <select v-model.number="filters.companyId" class="form-input filter-select">
        <option :value="0">Select company…</option>
        <option v-for="c in companies" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
      <input v-model.number="filters.year" type="number" min="2000" max="2099" class="form-input year-input" placeholder="Year" />
      <select v-model.number="filters.month" class="form-input filter-select">
        <option v-for="(m, i) in months" :key="i" :value="i + 1">{{ m }}</option>
      </select>
      <button @click="loadAll" :disabled="loading || !filters.companyId" class="btn-primary">
        {{ loading ? 'Loading…' : 'Load' }}
      </button>
    </div>

    <div v-if="!filters.companyId" class="empty-state">
      <p>Select a company to view statutory compliance exports.</p>
    </div>

    <template v-if="filters.companyId && !loading">

      <!-- ── EMP201 ─────────────────────────────────────── -->
      <section class="section">
        <div class="section-header">
          <div>
            <h2 class="section-title">EMP201 — Monthly Employer Declaration</h2>
            <p class="section-desc">SARS monthly PAYE, UIF and SDL declaration for {{ selectedMonthName }} {{ filters.year }}</p>
          </div>
          <button @click="downloadEmp201" :disabled="downloading.emp201" class="btn-download">
            {{ downloading.emp201 ? 'Downloading…' : 'Download CSV' }}
          </button>
        </div>

        <div v-if="emp201" class="card compliance-card">
          <div class="detail-row">
            <span class="detail-label">Employer</span>
            <span class="detail-value">{{ emp201.company.name }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Registration No.</span>
            <span class="detail-value">{{ emp201.company.registration_number || '—' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">UIF Reference</span>
            <span class="detail-value">{{ emp201.company.uif_reference || '—' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Period</span>
            <span class="detail-value">{{ emp201.period }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Employees processed</span>
            <span class="detail-value">{{ emp201.employee_count }}</span>
          </div>
          <div class="divider"></div>
          <div class="detail-row">
            <span class="detail-label">Total Remuneration</span>
            <span class="detail-value amount">{{ fmt(emp201.total_remuneration) }}</span>
          </div>
          <div class="detail-row highlight">
            <span class="detail-label">PAYE (Code 4102)</span>
            <span class="detail-value amount">{{ fmt(emp201.paye) }}</span>
          </div>
          <div class="detail-row highlight">
            <span class="detail-label">UIF — Employee (Code 4142)</span>
            <span class="detail-value amount">{{ fmt(emp201.uif_employee) }}</span>
          </div>
          <div class="detail-row highlight">
            <span class="detail-label">UIF — Employer</span>
            <span class="detail-value amount">{{ fmt(emp201.uif_employer) }}</span>
          </div>
          <div class="detail-row highlight">
            <span class="detail-label">SDL (Code 4149)</span>
            <span class="detail-value amount">{{ fmt(emp201.sdl) }}</span>
          </div>
          <div class="divider"></div>
          <div class="detail-row total-row">
            <span class="detail-label">Total Monthly Liability</span>
            <span class="detail-value amount">{{ fmt(emp201.total_liability) }}</span>
          </div>
        </div>
        <div v-else class="no-data">No payroll records for {{ selectedMonthName }} {{ filters.year }}.</div>
      </section>

      <!-- ── IRP5 / IT3(a) ──────────────────────────────── -->
      <section class="section">
        <div class="section-header">
          <div>
            <h2 class="section-title">IRP5 / IT3(a) — Annual Tax Certificates</h2>
            <p class="section-desc">Year-end employee tax certificate data for {{ filters.year }} tax year</p>
          </div>
          <button @click="downloadIrp5" :disabled="downloading.irp5" class="btn-download">
            {{ downloading.irp5 ? 'Downloading…' : 'Download CSV' }}
          </button>
        </div>

        <div v-if="irp5 && irp5.employees.length" class="card">
          <div class="table-totals">
            <div class="total-chip">
              <span class="chip-label">Employees</span>
              <span class="chip-value">{{ irp5.employee_count }}</span>
            </div>
            <div class="total-chip">
              <span class="chip-label">Total Remuneration</span>
              <span class="chip-value">{{ fmt(irp5.totals.total_remuneration) }}</span>
            </div>
            <div class="total-chip">
              <span class="chip-label">Total PAYE</span>
              <span class="chip-value">{{ fmt(irp5.totals.paye) }}</span>
            </div>
            <div class="total-chip">
              <span class="chip-label">Total UIF</span>
              <span class="chip-value">{{ fmt(irp5.totals.uif_employee + irp5.totals.uif_employer) }}</span>
            </div>
          </div>
          <div class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Employee</th>
                  <th>ID Number</th>
                  <th>Tax Ref</th>
                  <th class="num">Basic (3601)</th>
                  <th class="num">Other (3605)</th>
                  <th class="num">Total Rem.</th>
                  <th class="num">PAYE (4102)</th>
                  <th class="num">UIF Emp. (4142)</th>
                  <th class="num">Pension (4115)</th>
                  <th class="num">Months</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="e in irp5.employees" :key="e.name">
                  <td>{{ e.name }}</td>
                  <td>{{ e.id_no || '—' }}</td>
                  <td>{{ e.tax_ref || '—' }}</td>
                  <td class="num">{{ fmt(e.basic_salary) }}</td>
                  <td class="num">{{ fmt(e.other_income) }}</td>
                  <td class="num fw">{{ fmt(e.total_remuneration) }}</td>
                  <td class="num">{{ fmt(e.paye) }}</td>
                  <td class="num">{{ fmt(e.uif_employee) }}</td>
                  <td class="num">{{ fmt(e.pension) }}</td>
                  <td class="num">{{ e.months }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div v-else class="no-data">No payroll records for {{ filters.year }}.</div>
      </section>

      <!-- ── UI-19 ──────────────────────────────────────── -->
      <section class="section">
        <div class="section-header">
          <div>
            <h2 class="section-title">UI-19 — UIF Monthly Declaration</h2>
            <p class="section-desc">Department of Labour monthly UIF declaration for {{ selectedMonthName }} {{ filters.year }}</p>
          </div>
          <button @click="downloadUi19" :disabled="downloading.ui19" class="btn-download">
            {{ downloading.ui19 ? 'Downloading…' : 'Download CSV' }}
          </button>
        </div>

        <div v-if="emp201 && emp201.record_count > 0" class="card compliance-card">
          <div class="detail-row">
            <span class="detail-label">Employer</span>
            <span class="detail-value">{{ emp201.company.name }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">UIF Reference</span>
            <span class="detail-value">{{ emp201.company.uif_reference || '—' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Period</span>
            <span class="detail-value">{{ emp201.period }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Employees declared</span>
            <span class="detail-value">{{ emp201.employee_count }}</span>
          </div>
          <div class="divider"></div>
          <div class="detail-row highlight">
            <span class="detail-label">Total Gross Remuneration</span>
            <span class="detail-value amount">{{ fmt(emp201.total_remuneration) }}</span>
          </div>
          <div class="detail-row highlight">
            <span class="detail-label">UIF — Employee Contributions</span>
            <span class="detail-value amount">{{ fmt(emp201.uif_employee) }}</span>
          </div>
          <div class="detail-row highlight">
            <span class="detail-label">UIF — Employer Contributions</span>
            <span class="detail-value amount">{{ fmt(emp201.uif_employer) }}</span>
          </div>
          <div class="divider"></div>
          <div class="detail-row total-row">
            <span class="detail-label">Total UIF Contribution</span>
            <span class="detail-value amount">{{ fmt(emp201.uif_total) }}</span>
          </div>
        </div>
        <div v-else class="no-data">No payroll records for {{ selectedMonthName }} {{ filters.year }}.</div>
      </section>

      <!-- ── EFT Batch ──────────────────────────────────── -->
      <section class="section">
        <div class="section-header">
          <div>
            <h2 class="section-title">EFT Batch Payment File</h2>
            <p class="section-desc">Bank payment batch for net salaries — {{ selectedMonthName }} {{ filters.year }}</p>
          </div>
          <button @click="downloadEft" :disabled="downloading.eft" class="btn-download">
            {{ downloading.eft ? 'Downloading…' : 'Download CSV' }}
          </button>
        </div>

        <div v-if="emp201 && emp201.record_count > 0" class="card compliance-card">
          <div class="detail-row">
            <span class="detail-label">Period</span>
            <span class="detail-value">{{ emp201.period }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Payments</span>
            <span class="detail-value">{{ emp201.employee_count }} employees</span>
          </div>
          <div class="divider"></div>
          <div class="detail-row total-row">
            <span class="detail-label">Total Net Pay</span>
            <span class="detail-value amount">{{ fmt(emp201.total_net_pay) }}</span>
          </div>
          <p class="eft-note">
            The downloaded file contains one row per employee with their bank name, account number, branch code, account type, and net pay amount.
            Import directly into your bank's batch payment portal.
          </p>
        </div>
        <div v-else class="no-data">No approved payroll records for {{ selectedMonthName }} {{ filters.year }}.</div>
      </section>

    </template>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'

const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December']

export default {
  name: 'ComplianceView',
  setup() {
    const companies = ref([])
    const loading   = ref(false)
    const emp201    = ref(null)
    const irp5      = ref(null)
    const downloading = reactive({ emp201: false, irp5: false, ui19: false, eft: false })

    const today = new Date()
    const filters = reactive({
      companyId: 0,
      year: today.getFullYear(),
      month: today.getMonth() + 1,
    })

    const selectedMonthName = computed(() => MONTHS[filters.month - 1])

    const fmt = (v) => `R ${Number(v || 0).toLocaleString('en-ZA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`

    onMounted(async () => {
      try {
        const { data } = await axios.get('/companies')
        companies.value = data
        if (data.length === 1) filters.companyId = data[0].id
      } catch {}
    })

    const loadAll = async () => {
      if (!filters.companyId) return
      loading.value = true
      emp201.value = null
      irp5.value = null
      try {
        const [e201, i5] = await Promise.all([
          axios.get('/compliance/emp201', { params: { company_id: filters.companyId, year: filters.year, month: filters.month } }),
          axios.get('/compliance/irp5/preview', { params: { company_id: filters.companyId, year: filters.year } }),
        ])
        emp201.value = e201.data
        irp5.value = i5.data
      } catch (err) {
        alert(err?.response?.data?.detail || 'Failed to load compliance data')
      } finally {
        loading.value = false
      }
    }

    const blobDownload = async (url, params, key, filename) => {
      downloading[key] = true
      try {
        const { data, headers } = await axios.get(url, { params, responseType: 'blob' })
        const cd = headers['content-disposition'] || ''
        const match = cd.match(/filename="?([^"]+)"?/)
        const name = match ? match[1] : filename
        const link = document.createElement('a')
        link.href = URL.createObjectURL(new Blob([data], { type: 'text/csv' }))
        link.download = name
        link.click()
        URL.revokeObjectURL(link.href)
      } catch (err) {
        alert(err?.response?.data?.detail || `Download failed`)
      } finally {
        downloading[key] = false
      }
    }

    const downloadEmp201 = () => blobDownload('/compliance/emp201/download', { company_id: filters.companyId, year: filters.year, month: filters.month }, 'emp201', `EMP201_${filters.year}-${String(filters.month).padStart(2,'0')}.csv`)
    const downloadIrp5   = () => blobDownload('/compliance/irp5/download',   { company_id: filters.companyId, year: filters.year },                          'irp5',  `IRP5_${filters.year}.csv`)
    const downloadUi19   = () => blobDownload('/compliance/ui19/download',   { company_id: filters.companyId, year: filters.year, month: filters.month }, 'ui19',  `UI19_${filters.year}-${String(filters.month).padStart(2,'0')}.csv`)
    const downloadEft    = () => blobDownload('/compliance/eft/download',    { company_id: filters.companyId, year: filters.year, month: filters.month }, 'eft',   `EFT_${filters.year}-${String(filters.month).padStart(2,'0')}.csv`)

    return {
      companies, loading, emp201, irp5, downloading, filters,
      months: MONTHS, selectedMonthName, fmt,
      loadAll, downloadEmp201, downloadIrp5, downloadUi19, downloadEft,
    }
  }
}
</script>

<style scoped>
.compliance-content { display: flex; flex-direction: column; gap: 24px; }

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}
.page-title { font-size: 22px; font-weight: 700; color: var(--color-text-base); margin: 0; }
.breadcrumb { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--color-text-muted); margin-top: 2px; }
.sep { opacity: 0.4; }

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 14px 16px;
}
.filter-select { min-width: 160px; }
.year-input { width: 90px; }

.section { display: flex; flex-direction: column; gap: 12px; }
.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
.section-title { font-size: 15px; font-weight: 600; color: var(--color-text-base); margin: 0; }
.section-desc { font-size: 12px; color: var(--color-text-muted); margin: 2px 0 0; }

.card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  overflow: hidden;
}
.compliance-card { padding: 0; }

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid var(--color-border);
}
.detail-row:last-child { border-bottom: none; }
.detail-label { font-size: 13px; color: var(--color-text-muted); }
.detail-value { font-size: 13px; color: var(--color-text-base); font-weight: 500; }
.detail-value.amount { font-family: monospace; }

.highlight { background: rgba(14, 165, 233, 0.04); }
.total-row { background: rgba(14, 165, 233, 0.08); }
.total-row .detail-label { font-weight: 600; color: var(--color-text-base); }
.total-row .detail-value { font-size: 14px; font-weight: 700; color: var(--color-accent); }

.divider { height: 1px; background: var(--color-border); margin: 4px 0; }

.table-totals {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--color-border);
}
.total-chip {
  display: flex;
  flex-direction: column;
  gap: 2px;
  background: var(--color-bg-subtle, #f8fafc);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 8px 14px;
}
.chip-label { font-size: 11px; color: var(--color-text-muted); }
.chip-value { font-size: 13px; font-weight: 600; color: var(--color-text-base); }

.table-wrap { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.data-table th {
  padding: 9px 12px;
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
  background: var(--color-bg-subtle, #f8fafc);
}
.data-table td {
  padding: 9px 12px;
  color: var(--color-text-base);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: rgba(14,165,233,0.03); }
.num { text-align: right; font-family: monospace; }
.fw { font-weight: 600; }

.btn-download {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  background: var(--color-accent, #0ea5e9);
  color: #fff;
  border: none;
  border-radius: 7px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
}
.btn-download:hover:not(:disabled) { opacity: 0.88; }
.btn-download:disabled { opacity: 0.5; cursor: not-allowed; }

.eft-note {
  margin: 12px 16px 16px;
  font-size: 12px;
  color: var(--color-text-muted);
  line-height: 1.5;
}

.empty-state {
  text-align: center;
  padding: 48px 24px;
  color: var(--color-text-muted);
  font-size: 14px;
}

.no-data {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 24px;
  text-align: center;
  font-size: 13px;
  color: var(--color-text-muted);
}

@media (max-width: 640px) {
  .section-header { flex-direction: column; }
  .btn-download { align-self: flex-start; }
}
</style>
