<template>
  <div class="reports-content">

    <div class="page-header">
      <div>
        <h1 class="page-title">Reports &amp; Analytics</h1>
        <div class="breadcrumb">
          <span>Admin</span>
          <span class="sep">/</span>
          <span>Reports</span>
        </div>
      </div>
    </div>

    <!-- Filter bar -->
    <div class="filter-bar">
      <select v-model.number="filters.companyId" class="form-input filter-select">
        <option :value="0">All companies</option>
        <option v-for="c in companies" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
      <input v-model.number="filters.year" type="number" min="2000" max="2099" class="form-input year-input" placeholder="Year" />
      <select v-model.number="filters.month" class="form-input filter-select">
        <option :value="0">All months</option>
        <option v-for="(m, i) in months" :key="i" :value="i + 1">{{ m }}</option>
      </select>
      <button @click="generateReport" :disabled="loading" class="btn-primary">
        {{ loading && !analyticsMode ? 'Loading…' : 'Generate Report' }}
      </button>
      <button @click="exportCsv" :disabled="exporting" class="btn-secondary">
        {{ exporting ? 'Exporting…' : 'Export CSV' }}
      </button>
      <button @click="toggleAnalytics" :disabled="loading" class="btn-light" :class="{ 'active-mode': analyticsMode }">
        Analytics
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>{{ analyticsMode ? 'Loading analytics…' : 'Generating report…' }}</span>
    </div>

    <!-- ── ANALYTICS MODE ───────────────────────────────────── -->
    <template v-if="analyticsMode && analyticsData && !loading">

      <!-- Monthly trend chart -->
      <section class="section">
        <h2 class="section-title">Monthly Trend</h2>
        <div class="card chart-card">
          <div class="chart-legend">
            <span class="legend-dot gross"></span><span class="legend-label">Gross</span>
            <span class="legend-dot net"></span><span class="legend-label">Net</span>
          </div>
          <div class="chart-wrap">
            <svg :viewBox="`0 0 ${svgW} ${svgH}`" width="100%" :height="svgH" class="trend-svg">
              <g v-for="(m, i) in trendMonths" :key="i">
                <!-- Gross bar -->
                <rect
                  :x="barGroupX(i)"
                  :y="barY(m.total_gross)"
                  :width="barW"
                  :height="barHeight(m.total_gross)"
                  fill="#3b82f6"
                  rx="2"
                >
                  <title>{{ months[i] }} Gross: {{ fmtMoney(m.total_gross) }}</title>
                </rect>
                <!-- Net bar -->
                <rect
                  :x="barGroupX(i) + barW + 2"
                  :y="barY(m.total_net)"
                  :width="barW"
                  :height="barHeight(m.total_net)"
                  fill="#14b8a6"
                  rx="2"
                >
                  <title>{{ months[i] }} Net: {{ fmtMoney(m.total_net) }}</title>
                </rect>
                <!-- Month label -->
                <text
                  :x="barGroupX(i) + barW + 1"
                  :y="svgH - 4"
                  text-anchor="middle"
                  font-size="9"
                  fill="var(--color-text-muted)"
                >{{ months[i].slice(0, 3) }}</text>
              </g>
            </svg>
          </div>
        </div>
      </section>

      <!-- Top earners -->
      <section class="section">
        <h2 class="section-title">Top Earners</h2>
        <div class="card">
          <div v-if="topEarners.length === 0" class="empty-state">No data.</div>
          <div v-else class="earner-list">
            <div v-for="(e, i) in topEarners" :key="i" class="earner-row">
              <span class="earner-rank">{{ i + 1 }}</span>
              <span class="earner-name">{{ e.name }}</span>
              <div class="earner-bar-wrap">
                <div class="earner-bar" :style="{ width: earnerBarPct(e.net_pay) + '%' }"></div>
              </div>
              <span class="earner-amount">{{ fmtMoney(e.net_pay) }}</span>
            </div>
          </div>
        </div>
      </section>

    </template>

    <!-- ── REPORT MODE ─────────────────────────────────────── -->
    <template v-if="!analyticsMode && reportData && !loading">

      <!-- Summary cards -->
      <div class="summary-cards">
        <div class="card summary-card">
          <p class="sum-label">Total Gross Pay</p>
          <p class="sum-val">{{ fmtMoney(reportData.totals.total_gross) }}</p>
        </div>
        <div class="card summary-card">
          <p class="sum-label">Total Net Pay</p>
          <p class="sum-val accent">{{ fmtMoney(reportData.totals.total_net) }}</p>
        </div>
        <div class="card summary-card">
          <p class="sum-label">Total PAYE</p>
          <p class="sum-val">{{ fmtMoney(reportData.totals.total_paye) }}</p>
        </div>
        <div class="card summary-card">
          <p class="sum-label">Total SDL</p>
          <p class="sum-val">{{ fmtMoney(reportData.totals.total_sdl) }}</p>
        </div>
      </div>

      <!-- Tax breakdown -->
      <section class="section">
        <h2 class="section-title">Tax Breakdown</h2>
        <div class="card">
          <div class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Component</th>
                  <th class="num">Total</th>
                </tr>
              </thead>
              <tbody>
                <tr><td>PAYE</td><td class="num">{{ fmtMoney(reportData.totals.total_paye) }}</td></tr>
                <tr><td>UIF (Employee)</td><td class="num">{{ fmtMoney(reportData.totals.total_uif_employee) }}</td></tr>
                <tr><td>UIF (Employer)</td><td class="num">{{ fmtMoney(reportData.totals.total_uif_employer) }}</td></tr>
                <tr><td>SDL</td><td class="num">{{ fmtMoney(reportData.totals.total_sdl) }}</td></tr>
                <tr><td>Pension</td><td class="num">{{ fmtMoney(reportData.totals.total_pension) }}</td></tr>
                <tr><td>Medical Aid</td><td class="num">{{ fmtMoney(reportData.totals.total_medical) }}</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- Employee detail table -->
      <section class="section">
        <h2 class="section-title">Employee Detail</h2>
        <div class="card">
          <div v-if="(reportData.records || []).length === 0" class="empty-state">No records found.</div>
          <div v-else class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Employee</th>
                  <th>Period</th>
                  <th class="num">Basic Pay</th>
                  <th class="num">Total Earnings</th>
                  <th class="num">Total Deductions</th>
                  <th class="num">Net Pay</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in reportData.records" :key="r.id">
                  <td class="name-cell">{{ r.employee_name }}</td>
                  <td class="muted-text">{{ r.period }}</td>
                  <td class="num">{{ fmtMoney(r.basic_pay) }}</td>
                  <td class="num">{{ fmtMoney(r.total_earnings) }}</td>
                  <td class="num text-red">{{ fmtMoney(r.total_deductions) }}</td>
                  <td class="num text-green">{{ fmtMoney(r.net_pay) }}</td>
                  <td><span class="badge" :class="statusBadge(r.status)">{{ r.status || 'N/A' }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

    </template>

    <!-- Empty prompt -->
    <div v-if="!loading && !reportData && !analyticsData" class="card empty-prompt">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="empty-icon">
        <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
      </svg>
      <p>Select filters and click <strong>Generate Report</strong> or <strong>Analytics</strong> to get started.</p>
    </div>

  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'

const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December']

export default {
  name: 'ReportsView',
  setup() {
    const companies = ref([])
    const loading = ref(false)
    const exporting = ref(false)
    const analyticsMode = ref(false)
    const reportData = ref(null)
    const analyticsData = ref(null)

    const filters = reactive({
      companyId: 0,
      year: new Date().getFullYear(),
      month: 0
    })

    const months = MONTHS

    const buildParams = () => {
      const p = { year: filters.year }
      if (filters.companyId) p.company_id = filters.companyId
      if (filters.month) p.month = filters.month
      return p
    }

    const generateReport = async () => {
      analyticsMode.value = false
      loading.value = true
      reportData.value = null
      analyticsData.value = null
      try {
        const { data } = await axios.get('/reports/payroll-summary', { params: buildParams() })
        reportData.value = data
      } catch (e) {
        alert(e?.response?.data?.detail || 'Failed to generate report.')
      } finally {
        loading.value = false
      }
    }

    const exportCsv = async () => {
      exporting.value = true
      try {
        const res = await axios.get('/reports/export', { params: buildParams(), responseType: 'blob' })
        const url = window.URL.createObjectURL(new Blob([res.data]))
        const a = document.createElement('a')
        a.href = url
        a.setAttribute('download', `payroll_report_${filters.year}${filters.month ? '_' + filters.month : ''}.csv`)
        document.body.appendChild(a)
        a.click()
        a.remove()
        window.URL.revokeObjectURL(url)
      } catch {
        alert('Failed to export CSV.')
      } finally {
        exporting.value = false
      }
    }

    const toggleAnalytics = async () => {
      analyticsMode.value = !analyticsMode.value
      if (!analyticsMode.value) return
      reportData.value = null
      loading.value = true
      analyticsData.value = null
      try {
        const { data } = await axios.get('/reports/analytics', { params: buildParams() })
        analyticsData.value = data
      } catch {
        alert('Failed to load analytics.')
        analyticsMode.value = false
      } finally {
        loading.value = false
      }
    }

    // ── Chart helpers ────────────────────────────────────────
    const svgW = 700
    const svgH = 200
    const chartPadB = 20
    const chartPadT = 10
    const barGroupW = computed(() => (svgW - 20) / 12)
    const barW = computed(() => (barGroupW.value - 8) / 2)

    const trendMonths = computed(() => {
      if (!analyticsData.value?.monthly_trend) return Array(12).fill({ total_gross: 0, total_net: 0 })
      const src = analyticsData.value.monthly_trend
      return MONTHS.map((_, i) => src[i] || { total_gross: 0, total_net: 0 })
    })

    const chartMax = computed(() => {
      const vals = trendMonths.value.flatMap(m => [m.total_gross || 0, m.total_net || 0])
      return Math.max(...vals, 1)
    })

    const barGroupX = (i) => 10 + i * barGroupW.value

    const chartHeight = svgH - chartPadB - chartPadT

    const barHeight = (v) => {
      const h = (v / chartMax.value) * chartHeight
      return Math.max(h, 2)
    }

    const barY = (v) => svgH - chartPadB - barHeight(v)

    // ── Top earners ──────────────────────────────────────────
    const topEarners = computed(() => analyticsData.value?.top_earners || [])

    const maxEarner = computed(() => {
      const vals = topEarners.value.map(e => e.net_pay || 0)
      return Math.max(...vals, 1)
    })

    const earnerBarPct = (v) => Math.round(((v || 0) / maxEarner.value) * 100)

    // ── Utilities ────────────────────────────────────────────
    const fmtMoney = (n) => 'R ' + Number(n || 0).toLocaleString('en-ZA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

    const statusBadge = (s) => {
      const map = { approved: 'badge-green', paid: 'badge-green', rejected: 'badge-red', pending: 'badge-yellow', processed: 'badge-blue' }
      return map[(s || '').toLowerCase()] || 'badge-gray'
    }

    const fetchCompanies = async () => {
      try {
        const { data } = await axios.get('/companies')
        companies.value = data
      } catch {}
    }

    onMounted(fetchCompanies)

    return {
      companies, loading, exporting, analyticsMode,
      reportData, analyticsData,
      filters, months,
      generateReport, exportCsv, toggleAnalytics,
      svgW, svgH,
      trendMonths, barGroupX, barW, barHeight, barY,
      topEarners, earnerBarPct,
      fmtMoney, statusBadge
    }
  }
}
</script>

<style scoped>
.reports-content {
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

.filter-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.filter-select { width: auto; min-width: 160px; }
.year-input { width: 90px; }

.active-mode {
  background: #eff6ff;
  border-color: var(--color-accent);
  color: var(--color-accent);
}

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

.summary-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.summary-card { padding: 16px; }

.sum-label {
  font-size: 11px;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 6px;
  font-weight: 600;
}

.sum-val {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text-base);
  margin: 0;
}

.sum-val.accent { color: var(--color-accent); }

.section { display: flex; flex-direction: column; gap: 10px; }

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0;
}

/* Chart */
.chart-card { padding: 16px; }

.chart-legend {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  flex-shrink: 0;
}

.legend-dot.gross { background: #3b82f6; }
.legend-dot.net { background: #14b8a6; }

.legend-label { font-size: 12px; color: var(--color-text-muted); margin-right: 6px; }

.chart-wrap { width: 100%; overflow-x: auto; }
.trend-svg { display: block; }

/* Top earners */
.earner-list { display: flex; flex-direction: column; gap: 10px; }

.earner-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.earner-rank {
  width: 20px;
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text-muted);
  text-align: right;
}

.earner-name {
  width: 160px;
  flex-shrink: 0;
  font-size: 13px;
  color: var(--color-text-base);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.earner-bar-wrap {
  flex: 1;
  height: 10px;
  background: var(--color-bg-page);
  border-radius: 5px;
  overflow: hidden;
}

.earner-bar {
  height: 100%;
  background: var(--color-accent);
  border-radius: 5px;
  transition: width 0.3s;
}

.earner-amount {
  width: 120px;
  flex-shrink: 0;
  text-align: right;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-base);
}

/* Table */
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

.num { text-align: right; }

.text-green { color: #15803d; font-weight: 600; }
.text-red { color: #dc2626; }
.name-cell { font-weight: 500; }
.muted-text { color: var(--color-text-muted); font-size: 12px; }

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

.empty-state {
  font-size: 13px;
  color: var(--color-text-muted);
  padding: 24px 0;
  text-align: center;
}

.empty-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 48px 24px;
  text-align: center;
  color: var(--color-text-muted);
  font-size: 13px;
}

.empty-icon {
  width: 40px;
  height: 40px;
  color: var(--color-border);
}

@media (max-width: 900px) {
  .summary-cards { grid-template-columns: 1fr 1fr; }
}

@media (max-width: 600px) {
  .summary-cards { grid-template-columns: 1fr; }
  .filter-bar { flex-direction: column; align-items: flex-start; }
  .filter-select, .year-input { width: 100%; }
  .earner-name { width: 100px; }
  .earner-amount { width: 90px; font-size: 12px; }
}
</style>
