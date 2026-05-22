<template>
  <div class="view-content">

    <!-- Page header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Payroll Processing</h1>
        <p class="page-subtitle">Calculate and generate payslips for employees</p>
      </div>
      <div class="header-actions">
        <button @click="calculatePayroll" :disabled="isCalculating" class="btn btn-primary">
          <span v-if="isCalculating" class="spinner spinner-sm" style="border-top-color:#fff;border-color:rgba(255,255,255,0.3);border-top-color:#fff;"></span>
          {{ isCalculating ? 'Calculating…' : 'Calculate Payroll' }}
        </button>
      </div>
    </div>

    <!-- Company + Employee selectors -->
    <div class="filters-bar">
      <div class="form-group" style="min-width:220px;">
        <label class="form-label">Company</label>
        <select v-model.number="selectedCompanyId" @change="onCompanyChange" class="form-input">
          <option :value="0">Select company…</option>
          <option v-for="c in companies" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </div>
      <div class="form-group" style="min-width:220px;">
        <label class="form-label">Employee</label>
        <select v-model.number="selectedEmployeeId" class="form-input" :disabled="!selectedCompanyId || employees.length === 0">
          <option :value="0">Select employee…</option>
          <option v-for="e in employees" :key="e.id" :value="e.id">{{ e.first_names }} {{ e.last_name }}</option>
        </select>
      </div>
      <div style="display:flex;gap:8px;align-items:flex-end;padding-bottom:1px;">
        <button @click="applyCompany" :disabled="!selectedCompanyId" class="btn btn-secondary btn-sm">Load Company</button>
        <button @click="applyEmployee" :disabled="!selectedEmployeeId" class="btn btn-secondary btn-sm">Load Employee</button>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs-underline">
      <button
        v-for="tab in tabs" :key="tab.id"
        @click="activeTab = tab.id"
        class="tab-underline"
        :class="{ active: activeTab === tab.id }"
      >{{ tab.name }}</button>
    </div>

    <!-- Loading skeleton -->
    <SkeletonTable v-if="loading" :rows="5" :cols="5" />

    <!-- ───── Details & Payslip tab ───── -->
    <div v-else-if="activeTab === 'details'" class="fade-in details-layout">

      <!-- Left: forms -->
      <div class="form-col">

        <!-- Employee Details -->
        <div class="card card-sm">
          <div class="card-header">
            <span class="card-title">Employee Details</span>
          </div>
          <div class="form-grid">
            <div class="form-group">
              <label class="form-label">First Names</label>
              <input v-model="formData.employee.first_names" type="text" class="form-input" placeholder="Jane" />
            </div>
            <div class="form-group">
              <label class="form-label">Last Name</label>
              <input v-model="formData.employee.last_name" type="text" class="form-input" placeholder="Doe" />
            </div>
            <div class="form-group">
              <label class="form-label">ID / Passport No.</label>
              <input v-model="formData.employee.id_no" type="text" class="form-input" placeholder="9001010001088" />
            </div>
            <div class="form-group">
              <label class="form-label">Employee No.</label>
              <input v-model="formData.employee.employee_no" type="text" class="form-input" placeholder="EMP001" />
            </div>
            <div class="form-group">
              <label class="form-label">Position</label>
              <input v-model="formData.employee.position" type="text" class="form-input" placeholder="Software Developer" />
            </div>
            <div class="form-group">
              <label class="form-label">Tax Reference</label>
              <input v-model="formData.employee.tax_ref" type="text" class="form-input" placeholder="1234567890" />
            </div>
            <div class="form-group span-2">
              <label class="form-label">Employment Date</label>
              <input v-model="formData.employee.emp_date" type="date" class="form-input" />
            </div>
          </div>
        </div>

        <!-- Pay Period -->
        <div class="card card-sm">
          <div class="card-header">
            <span class="card-title">Pay Period</span>
          </div>
          <div class="form-grid">
            <div class="form-group">
              <label class="form-label">Period Start</label>
              <input v-model="formData.period_start" type="date" class="form-input" />
            </div>
            <div class="form-group">
              <label class="form-label">Period End</label>
              <input v-model="formData.period_end" type="date" class="form-input" />
            </div>
            <div class="form-group span-2">
              <label class="form-label">Payment Date</label>
              <input v-model="formData.payment_date" type="date" class="form-input" />
            </div>
          </div>
        </div>

        <!-- Calculation Mode + Earnings -->
        <div class="card card-sm">
          <div class="card-header">
            <span class="card-title">{{ isReverseMode ? 'Net Pay Target' : 'Earnings (Monthly)' }}</span>
            <div class="calc-mode-toggle">
              <span class="form-label" :style="!isReverseMode ? 'color:var(--color-text-base);font-weight:600;' : ''">Normal</span>
              <button @click="toggleCalculationMode" class="toggle-btn-switch" :class="{ active: isReverseMode }" type="button">
                <span class="toggle-thumb-switch" :class="{ active: isReverseMode }"></span>
              </button>
              <span class="form-label" :style="isReverseMode ? 'color:var(--color-text-base);font-weight:600;' : ''">Reverse</span>
            </div>
          </div>
          <div v-if="isReverseMode" class="info-box info-blue" style="margin-bottom:14px;font-size:12px;">
            Enter the desired net pay. The system will work backwards to find the required gross salary.
          </div>
          <div class="form-grid">
            <div class="form-group" v-if="!isReverseMode">
              <label class="form-label">Basic Pay</label>
              <input v-model.number="formData.basic_pay" type="number" step="0.01" min="0" class="form-input" placeholder="0.00" />
            </div>
            <div class="form-group" v-if="isReverseMode">
              <label class="form-label">Target Net Pay</label>
              <input v-model.number="formData.target_net_pay" type="number" step="0.01" min="0" class="form-input" placeholder="0.00" />
            </div>
            <div class="form-group">
              <label class="form-label">Other Earnings</label>
              <input v-model.number="formData.other_earnings" type="number" step="0.01" min="0" class="form-input" placeholder="0.00" />
            </div>
          </div>
        </div>

        <!-- Deductions -->
        <div class="card card-sm">
          <div class="card-header">
            <span class="card-title">Deductions (Monthly)</span>
          </div>
          <div class="form-grid">
            <div class="form-group">
              <label class="form-label">Pension / Retirement</label>
              <input v-model.number="formData.pension" type="number" step="0.01" min="0" class="form-input" placeholder="0.00" />
            </div>
            <div class="form-group">
              <label class="form-label">Medical Aid</label>
              <input v-model.number="formData.medical" type="number" step="0.01" min="0" class="form-input" placeholder="0.00" />
            </div>
          </div>
        </div>

        <!-- SDL -->
        <div class="card card-sm">
          <div class="card-header">
            <span class="card-title">Skills Development Levy (SDL)</span>
          </div>
          <div class="form-grid">
            <div class="form-group">
              <label class="form-label">Annual Payroll</label>
              <input v-model.number="formData.annual_payroll" type="number" step="0.01" min="0" class="form-input" placeholder="0.00" />
              <span class="form-hint">SDL applies if annual payroll ≥ R500,000</span>
            </div>
            <div class="form-group">
              <label class="form-label">Excluded Amounts</label>
              <input v-model.number="formData.excluded_amounts" type="number" step="0.01" min="0" class="form-input" placeholder="0.00" />
              <span class="form-hint">Reimbursements, non-taxable allowances</span>
            </div>
          </div>
        </div>

        <!-- Leave Income -->
        <div class="card card-sm">
          <div class="card-header">
            <span class="card-title">Leave Income</span>
          </div>
          <div class="form-grid">
            <div class="form-group">
              <label class="form-label">Leave Days Taken</label>
              <input v-model.number="formData.leave_days_taken" type="number" min="0" max="31" class="form-input" placeholder="0" />
              <span class="form-hint">Days taken in this pay period</span>
            </div>
            <div class="form-group">
              <label class="form-label">Total Leave Days Available</label>
              <input v-model.number="formData.total_leave_days_available" type="number" min="0" max="365" class="form-input" placeholder="21" />
              <span class="form-hint">Annual entitlement (BCEA default: 21)</span>
            </div>
          </div>
        </div>

        <!-- Company Details -->
        <div class="card card-sm">
          <div class="card-header">
            <span class="card-title">Company Details</span>
          </div>
          <div class="form-grid">
            <div class="form-group">
              <label class="form-label">Company Name</label>
              <input v-model="formData.company.company_name" type="text" class="form-input" placeholder="Company name" />
            </div>
            <div class="form-group">
              <label class="form-label">Registration No.</label>
              <input v-model="formData.company.company_reg_no" type="text" class="form-input" placeholder="2023/123456/07" />
            </div>
            <div class="form-group span-2">
              <label class="form-label">Address</label>
              <textarea v-model="formData.company.company_address" rows="2" class="form-input" placeholder="Company address"></textarea>
            </div>
            <div class="form-group">
              <label class="form-label">UIF Reference</label>
              <input v-model="formData.company.uif_ref" type="text" class="form-input" placeholder="UIF reference" />
            </div>
            <div class="form-group">
              <label class="form-label">Phone</label>
              <input v-model="formData.company.phone" type="tel" class="form-input" placeholder="012 345 6789" />
            </div>
            <div class="form-group">
              <label class="form-label">Email</label>
              <input v-model="formData.company.email" type="email" class="form-input" placeholder="info@company.co.za" />
            </div>
            <div class="form-group">
              <label class="form-label">Run Identifier</label>
              <input v-model="formData.company.run" type="text" class="form-input" placeholder="e.g. June - 2025" />
            </div>
          </div>
        </div>

      </div>

      <!-- Right: sticky summary -->
      <div class="summary-col">
        <div class="summary-card">
          <p class="section-label" style="margin-bottom:14px;">Payroll Summary</p>

          <div v-if="calculatedData" class="summary-body">
            <div class="summary-row summary-row--success">
              <span>Total Earnings</span>
              <span>R{{ formatCurrency(calculatedData.total_earnings) }}</span>
            </div>
            <div class="summary-row summary-row--danger">
              <span>Total Deductions</span>
              <span>R{{ formatCurrency(calculatedData.total_deductions) }}</span>
            </div>
            <div class="summary-row summary-row--primary">
              <span>Net Pay</span>
              <span class="summary-net">R{{ formatCurrency(calculatedData.net_pay) }}</span>
            </div>

            <div v-if="calculatedData.paye || calculatedData.uif" class="summary-breakdown">
              <div class="breakdown-row"><span>PAYE</span><span>R{{ formatCurrency(calculatedData.paye) }}</span></div>
              <div class="breakdown-row"><span>UIF</span><span>R{{ formatCurrency(calculatedData.uif) }}</span></div>
              <div class="breakdown-row"><span>Pension</span><span>R{{ formatCurrency(formData.pension) }}</span></div>
              <div class="breakdown-row"><span>Medical Aid</span><span>R{{ formatCurrency(formData.medical) }}</span></div>
            </div>
          </div>

          <div v-else class="summary-empty">
            <svg width="36" height="36" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
            </svg>
            <p>Fill in payroll details, then click Calculate Payroll.</p>
          </div>

          <!-- Actions -->
          <div class="summary-actions">
            <div v-if="auth.roles.includes('manager') && selectedCompanyId && calculatedData" style="display:flex;gap:8px;">
              <button @click="approveRun" class="btn btn-secondary" style="flex:1;">Approve Run</button>
              <button @click="rejectRun" class="btn btn-secondary" style="flex:1;">Reject Run</button>
            </div>

            <button
              @click="generatePayslip"
              :disabled="!calculatedData || isGeneratingPDF"
              class="btn btn-secondary w-full"
            >
              <span v-if="isGeneratingPDF" class="spinner spinner-sm"></span>
              {{ isGeneratingPDF ? 'Generating…' : 'Download Payslip PDF' }}
            </button>

            <template v-if="calculatedData?.record_id">
              <div v-if="distributeStatus === 'distributed'" class="distribute-badge">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                Distributed to portal
              </div>
              <button v-else @click="distributeOne" :disabled="distributing" class="btn btn-secondary w-full">
                {{ distributing ? 'Distributing…' : 'Distribute to Employee Portal' }}
              </button>
              <p v-if="distributeError" style="font-size:12px;color:var(--color-error);margin:0;">{{ distributeError }}</p>
            </template>
          </div>
        </div>
      </div>

    </div>

    <!-- ───── Summary & Calculations tab ───── -->
    <div v-else-if="activeTab === 'summary'" class="fade-in">

      <div v-if="calculatedData" class="summary-tab">

        <!-- Reverse calc banner -->
        <div v-if="isReverseMode && calculatedData.calculated_gross_pay" class="card card-sm" style="border-color:var(--color-info-border);background:var(--color-info-bg);">
          <p class="section-label" style="color:#1e40af;margin-bottom:10px;">Reverse Calculation Result</p>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:12px;">
            <div class="result-cell">
              <div class="result-cell__label">Target Net Pay</div>
              <div class="result-cell__value">R{{ formatCurrency(formData.target_net_pay) }}</div>
            </div>
            <div class="result-cell result-cell--highlight">
              <div class="result-cell__label">Required Gross Pay</div>
              <div class="result-cell__value">R{{ formatCurrency(calculatedData.calculated_gross_pay) }}</div>
            </div>
          </div>
          <p style="font-size:12px;color:#1e40af;">
            To achieve a net pay of R{{ formatCurrency(formData.target_net_pay) }}, the gross salary must be R{{ formatCurrency(calculatedData.calculated_gross_pay) }}.
          </p>
        </div>

        <!-- Earnings / Deductions breakdown -->
        <div class="breakdown-grid">
          <div class="card card-sm">
            <div class="card-header"><span class="card-title">Earnings Breakdown</span></div>
            <div class="breakdown-list">
              <div v-for="[desc, amt] in calculatedData.earnings" :key="desc" class="breakdown-row">
                <span>{{ desc }}</span>
                <span style="font-weight:500;color:#15803d;">R{{ formatCurrency(amt) }}</span>
              </div>
            </div>
            <div class="breakdown-total">
              <span>Total Earnings</span>
              <span>R{{ formatCurrency(calculatedData.total_earnings) }}</span>
            </div>
          </div>

          <div class="card card-sm">
            <div class="card-header"><span class="card-title">Deductions Breakdown</span></div>
            <div class="breakdown-list">
              <div v-for="[desc, amt] in calculatedData.deductions" :key="desc" class="breakdown-row">
                <span>{{ desc }}</span>
                <span style="font-weight:500;color:#dc2626;">R{{ formatCurrency(amt) }}</span>
              </div>
            </div>
            <div class="breakdown-total">
              <span>Total Deductions</span>
              <span>R{{ formatCurrency(calculatedData.total_deductions) }}</span>
            </div>
          </div>
        </div>

        <!-- Net pay summary -->
        <div class="card card-sm net-pay-card">
          <div class="net-pay-amount">R{{ formatCurrency(calculatedData.net_pay) }}</div>
          <div class="net-pay-label">Net Pay</div>
          <div class="net-pay-meta">
            {{ formData.employee.first_names }} {{ formData.employee.last_name }}
            &nbsp;·&nbsp;
            {{ formatDate(formData.period_start) }} to {{ formatDate(formData.period_end) }}
          </div>
        </div>

        <!-- SDL details -->
        <div v-if="calculatedData.sdl_details && calculatedData.sdl > 0" class="card card-sm">
          <div class="card-header"><span class="card-title">SDL Details</span></div>
          <div class="detail-pairs">
            <div class="detail-pair"><span>Total Remuneration</span><span>R{{ formatCurrency(calculatedData.sdl_details.total_remuneration) }}</span></div>
            <div class="detail-pair"><span>SDL Rate</span><span>{{ calculatedData.sdl_details.sdl_rate }}</span></div>
            <div class="detail-pair"><span>SDL Amount</span><span>R{{ formatCurrency(calculatedData.sdl) }}</span></div>
          </div>
        </div>

        <!-- Leave income details -->
        <div v-if="calculatedData.leave_income_details && calculatedData.leave_income > 0" class="card card-sm">
          <div class="card-header"><span class="card-title">Leave Income Details</span></div>
          <div class="detail-pairs">
            <div class="detail-pair"><span>Annual Salary</span><span>R{{ formatCurrency(calculatedData.leave_income_details.annual_salary) }}</span></div>
            <div class="detail-pair"><span>Daily Rate</span><span>R{{ formatCurrency(calculatedData.leave_income_details.daily_rate) }}</span></div>
            <div class="detail-pair"><span>Leave Days</span><span>{{ calculatedData.leave_income_details.leave_days_taken }} / {{ calculatedData.leave_income_details.total_leave_days_available }}</span></div>
            <div class="detail-pair"><span>Leave Income</span><span>R{{ formatCurrency(calculatedData.leave_income) }}</span></div>
          </div>
        </div>

      </div>

      <div v-else class="card">
        <div class="empty-state">
          <svg class="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
          </svg>
          <p class="empty-title">No calculations yet</p>
          <p>Go to the Details tab, fill in the payroll data, then click Calculate Payroll.</p>
          <button @click="activeTab = 'details'" class="btn btn-primary btn-sm" style="margin-top:8px;">Go to Details</button>
        </div>
      </div>

    </div>

  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import MetricCard from '../components/MetricCard.vue'
import FormSection from '../components/FormSection.vue'
import SkeletonTable from '../components/ui/SkeletonTable.vue'

export default {
  name: 'PayrollView',
  components: { MetricCard, FormSection, SkeletonTable },
  setup() {
    const auth            = useAuthStore()
    const loading         = ref(false)
    const activeTab       = ref('details')
    const isCalculating   = ref(false)
    const isGeneratingPDF = ref(false)
    const calculatedData  = ref(null)
    const isReverseMode   = ref(false)

    const tabs = [
      { id: 'details', name: 'Details & Payslip' },
      { id: 'summary', name: 'Summary & Calculations' }
    ]

    const formData = reactive({
      employee: {
        first_names: '',
        last_name:   '',
        id_no:       '',
        employee_no: '',
        position:    '',
        tax_ref:     '',
        emp_date:    new Date().toISOString().split('T')[0]
      },
      company: {
        company_name:    'OrbitPay',
        company_reg_no:  '',
        company_address: '',
        uif_ref:         '',
        phone:           '',
        email:           '',
        run:             ''
      },
      period_start:              new Date().toISOString().split('T')[0],
      period_end:                new Date().toISOString().split('T')[0],
      payment_date:              new Date().toISOString().split('T')[0],
      basic_pay:                 0,
      other_earnings:            0,
      pension:                   0,
      medical:                   0,
      target_net_pay:            0,
      annual_payroll:            0,
      excluded_amounts:          0,
      leave_days_taken:          0,
      total_leave_days_available: 21
    })

    const toggleCalculationMode = () => {
      isReverseMode.value = !isReverseMode.value
      calculatedData.value = null
    }

    const API              = ''
    const companies        = ref([])
    const employees        = ref([])
    const selectedCompanyId  = ref(0)
    const selectedEmployeeId = ref(0)

    const loadCompanies = async () => {
      loading.value = true
      try {
        const { data } = await axios.get(`${API}/companies`)
        companies.value = data
      } catch (e) {
        console.error('Failed to load companies', e)
      } finally {
        loading.value = false
      }
    }

    const onCompanyChange = async () => {
      selectedEmployeeId.value = 0
      employees.value = []
      if (!selectedCompanyId.value) return
      try {
        const [companyRes, empsRes] = await Promise.all([
          axios.get(`${API}/companies/${selectedCompanyId.value}`),
          axios.get(`${API}/companies/${selectedCompanyId.value}/employees`, { params: { include_inactive: false } })
        ])
        employees.value = empsRes.data
        mapCompanyToForm(companyRes.data)
      } catch (e) {
        console.error('Failed to load company/employees', e)
      }
    }

    const applyCompany = async () => {
      if (!selectedCompanyId.value) return
      try {
        const { data } = await axios.get(`${API}/companies/${selectedCompanyId.value}`)
        mapCompanyToForm(data)
      } catch (e) {
        console.error('Failed to apply company', e)
      }
    }

    const applyEmployee = async () => {
      if (!selectedEmployeeId.value) return
      try {
        const { data } = await axios.get(`${API}/employees/${selectedEmployeeId.value}`)
        mapEmployeeToForm(data)
      } catch (e) {
        console.error('Failed to apply employee', e)
      }
    }

    const mapCompanyToForm = (c) => {
      formData.company.company_name    = c?.name || ''
      formData.company.company_reg_no  = c?.registration_number || ''
      formData.company.company_address = c?.address || ''
      formData.company.uif_ref         = c?.uif_reference || ''
      formData.company.phone           = c?.phone || ''
      formData.company.email           = c?.email || ''
    }

    const mapEmployeeToForm = (e) => {
      formData.employee.first_names = e?.first_names || ''
      formData.employee.last_name   = e?.last_name || ''
      formData.employee.id_no       = e?.id_no || ''
      formData.employee.employee_no = e?.employee_no || ''
      formData.employee.position    = e?.position || ''
      formData.employee.tax_ref     = e?.tax_ref || ''
      formData.employee.emp_date    = e?.emp_date || new Date().toISOString().split('T')[0]
      formData.basic_pay     = Number(e?.basic_salary ?? 0)
      const allowancesTotal  = Number(e?.housing_allowance ?? 0) + Number(e?.transport_allowance ?? 0) + Number(e?.meal_allowance ?? 0) + Number(e?.other_allowances ?? 0)
      formData.other_earnings = allowancesTotal || 0
      formData.pension = Number(e?.pension_contribution ?? 0)
      formData.medical = Number(e?.medical_aid ?? 0)
    }

    const formatCurrency = (amount) => new Intl.NumberFormat('en-ZA', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount || 0)

    const formatDate = (dateString) => new Date(dateString).toLocaleDateString('en-ZA', {
      year: 'numeric', month: 'long', day: 'numeric'
    })

    const calculatePayroll = async () => {
      isCalculating.value = true
      distributeStatus.value = ''
      distributeError.value  = ''
      try {
        let response
        if (isReverseMode.value) {
          const reverseData = {
            employee:     formData.employee,
            company:      formData.company,
            period_start: formData.period_start,
            period_end:   formData.period_end,
            payment_date: formData.payment_date,
            target_net_pay:             formData.target_net_pay,
            pension:                    formData.pension,
            medical:                    formData.medical,
            annual_payroll:             formData.annual_payroll,
            excluded_amounts:           formData.excluded_amounts,
            leave_days_taken:           formData.leave_days_taken,
            total_leave_days_available: formData.total_leave_days_available
          }
          response = await axios.post('/calculate-reverse-payroll', reverseData)
          const r  = response.data
          calculatedData.value = {
            employee: r.employee, company: r.company,
            period_start: r.period_start, period_end: r.period_end, payment_date: r.payment_date,
            earnings: r.earnings, total_earnings: r.total_earnings,
            deductions: r.deductions, total_deductions: r.total_deductions,
            net_pay: r.net_pay, paye: r.paye, uif: r.uif,
            calculated_gross_pay: r.calculated_gross_pay,
            sdl: r.sdl, leave_income: r.leave_income,
            sdl_details: r.sdl_details, leave_income_details: r.leave_income_details
          }
        } else {
          response = await axios.post('/calculate-payroll', formData)
          calculatedData.value = response.data
        }
      } catch (error) {
        console.error('Error calculating payroll:', error)
        let detail = error?.response?.data?.detail || error.message || 'Unknown error'
        if (Array.isArray(detail)) detail = detail.map(e => e.msg || e).join('\n')
        alert(`Error calculating payroll:\n${detail}`)
      } finally {
        isCalculating.value = false
      }
    }

    const approveRun = async () => {
      try {
        const { data: run } = await axios.post('/payroll-runs', {
          company_id:   selectedCompanyId.value,
          period_start: formData.period_start,
          period_end:   formData.period_end
        })
        await axios.post(`/payroll-runs/${run.id}/approve`)
        alert('Run approved')
      } catch { alert('Approval failed') }
    }

    const rejectRun = async () => {
      try {
        const { data: run } = await axios.post('/payroll-runs', {
          company_id:   selectedCompanyId.value,
          period_start: formData.period_start,
          period_end:   formData.period_end
        })
        await axios.post(`/payroll-runs/${run.id}/reject`)
        alert('Run rejected')
      } catch { alert('Reject failed') }
    }

    const generatePayslip = async () => {
      if (!calculatedData.value) return
      isGeneratingPDF.value = true
      try {
        const response = await axios.post('/generate-payslip', calculatedData.value, { responseType: 'blob' })
        const url  = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `payslip_${formData.employee.last_name}_${formData.employee.first_names}.pdf`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
      } catch (error) {
        console.error('Error generating payslip:', error)
        alert('Error generating payslip. Please try again.')
      } finally {
        isGeneratingPDF.value = false
      }
    }

    const distributing     = ref(false)
    const distributeStatus = ref('')
    const distributeError  = ref('')

    const distributeOne = async () => {
      if (!calculatedData.value?.record_id) return
      distributing.value    = true
      distributeError.value = ''
      try {
        await axios.post(`/payroll-records/${calculatedData.value.record_id}/distribute`)
        distributeStatus.value = 'distributed'
      } catch (e) {
        distributeError.value = e?.response?.data?.detail || 'Distribution failed.'
      } finally {
        distributing.value = false
      }
    }

    onMounted(loadCompanies)

    return {
      auth, loading, activeTab, isCalculating, isGeneratingPDF,
      calculatedData, isReverseMode, tabs, formData,
      companies, employees, selectedCompanyId, selectedEmployeeId,
      onCompanyChange, applyCompany, applyEmployee,
      toggleCalculationMode,
      formatCurrency, formatDate,
      calculatePayroll, generatePayslip,
      approveRun, rejectRun,
      distributing, distributeStatus, distributeError, distributeOne
    }
  }
}
</script>

<style scoped>
/* ── View layout ─────────────────────────────────────────────────────────── */
.view-content {
  padding: 24px;
  max-width: 1280px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.filters-bar {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  flex-wrap: wrap;
}

/* ── Two-column details layout ───────────────────────────────────────────── */
.details-layout {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 20px;
  align-items: start;
}

.form-col {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ── Calculation mode toggle (inside card header) ────────────────────────── */
.calc-mode-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toggle-btn-switch {
  position: relative;
  width: 38px;
  height: 21px;
  background: var(--color-border-input);
  border-radius: 999px;
  border: none;
  cursor: pointer;
  padding: 0;
  transition: background 0.2s;
  flex-shrink: 0;
}
.toggle-btn-switch.active { background: var(--color-accent); }

.toggle-thumb-switch {
  position: absolute;
  top: 3px; left: 3px;
  width: 15px; height: 15px;
  background: #fff;
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  transition: transform 0.2s;
  display: block;
}
.toggle-thumb-switch.active { transform: translateX(17px); }

/* ── Summary card (sticky sidebar) ──────────────────────────────────────── */
.summary-col { position: relative; }

.summary-card {
  position: sticky;
  top: 24px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 16px;
}

.summary-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 500;
}
.summary-row--success { background: var(--color-success-bg); color: #065f46; }
.summary-row--danger  { background: var(--color-error-bg);   color: #991b1b; }
.summary-row--primary { background: var(--color-info-bg);    color: #1e40af; }

.summary-net { font-size: 17px; font-weight: 700; }

.summary-breakdown {
  padding-top: 8px;
  margin-top: 4px;
  border-top: 1px solid var(--color-border);
}

.breakdown-row {
  display: flex;
  justify-content: space-between;
  font-size: 11.5px;
  color: var(--color-text-muted);
  padding: 3px 0;
}

.summary-empty {
  text-align: center;
  padding: 24px 0;
  color: var(--color-text-muted);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}
.summary-empty svg { opacity: 0.3; }
.summary-empty p { font-size: 12.5px; line-height: 1.5; max-width: 200px; }

.summary-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-top: 1px solid var(--color-border);
  padding-top: 14px;
}

.distribute-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: var(--color-success-bg);
  border: 1px solid var(--color-success-border);
  border-radius: var(--radius-md);
  font-size: 12.5px;
  font-weight: 600;
  color: #15803d;
}

/* ── Summary tab layout ──────────────────────────────────────────────────── */
.summary-tab {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 900px;
}

.breakdown-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.breakdown-list {
  display: flex;
  flex-direction: column;
}

.breakdown-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-border);
  font-size: 13px;
}

.breakdown-total {
  display: flex;
  justify-content: space-between;
  padding: 10px 0 0;
  margin-top: 4px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
  border-top: 2px solid var(--color-border);
}

/* ── Net pay hero ────────────────────────────────────────────────────────── */
.net-pay-card {
  text-align: center;
  padding: 32px 24px;
}
.net-pay-amount {
  font-size: 36px;
  font-weight: 700;
  color: var(--color-primary);
  letter-spacing: -0.02em;
  margin-bottom: 4px;
}
.net-pay-label {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
  margin-bottom: 10px;
}
.net-pay-meta {
  font-size: 12px;
  color: var(--color-text-muted);
}

/* ── Detail pairs (SDL / Leave details) ──────────────────────────────────── */
.detail-pairs {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.detail-pair {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  padding: 7px 0;
  border-bottom: 1px solid var(--color-border);
}
.detail-pair:last-child { border-bottom: none; }
.detail-pair span:first-child { color: var(--color-text-muted); }
.detail-pair span:last-child  { font-weight: 500; }

/* ── Reverse calc result cells ───────────────────────────────────────────── */
.result-cell {
  background: #fff;
  border-radius: var(--radius-md);
  padding: 16px;
  text-align: center;
}
.result-cell--highlight { border: 2px solid var(--color-success); }
.result-cell__label { font-size: 11px; color: var(--color-text-muted); margin-bottom: 4px; }
.result-cell__value { font-size: 20px; font-weight: 700; color: var(--color-text-primary); }

/* ── span-2 helper for form-grid ─────────────────────────────────────────── */
.span-2 { grid-column: span 2; }

/* ── Responsive ──────────────────────────────────────────────────────────── */
@media (max-width: 1024px) {
  .details-layout {
    grid-template-columns: 1fr;
  }
  .summary-card {
    position: static;
  }
  .summary-col {
    order: -1;
  }
  .breakdown-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .view-content { padding: 16px; }
  .filters-bar { flex-direction: column; align-items: stretch; }
  .span-2 { grid-column: span 1; }
}
</style>
