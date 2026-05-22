<template>
  <div class="payroll-layout">
    <div class="payroll-content">
      <!-- Page Header -->
      <div class="page-header">
        <div class="header-left">
          <h1 class="page-title">Payroll Processing</h1>
          <div class="breadcrumb">
            <span>Payroll</span>
            <span class="separator">/</span>
            <span>Process Pay Run</span>
          </div>
        </div>
        <div class="header-right">
          <button @click="calculatePayroll" :disabled="isCalculating" class="btn-primary">
            <svg v-if="isCalculating" class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ isCalculating ? 'Calculating...' : 'Calculate Payroll' }}
          </button>
        </div>
      </div>

      <!-- Metric Cards -->
      <div class="metric-cards" v-if="calculatedData">
        <MetricCard label="Gross Pay" :value="calculatedData.total_earnings" />
        <MetricCard label="Deductions" :value="calculatedData.total_deductions" />
        <MetricCard label="Net Pay" :value="calculatedData.net_pay" type="success" />
      </div>

      <!-- Tabs -->
      <div class="tabs-underline">
        <button v-for="tab in tabs" :key="tab.id" @click="activeTab = tab.id" class="tab-underline" :class="{ active: activeTab === tab.id }">
          {{ tab.name }}
        </button>
      </div>

      <!-- Details Tab -->
      <div v-if="activeTab === 'details'" class="fade-in tab-content">
        <div class="form-layout">
          <!-- Left Column - Forms -->
          <div class="form-column">
            <!-- Import Saved Company & Employee -->
            <FormSection ref="sectionPayrun" title="Import Saved Company & Employee" icon="import">
              <div class="form-row-3">
                <div class="form-group span-2">
                  <label class="form-label">Company</label>
                  <select v-model.number="selectedCompanyId" @change="onCompanyChange" class="form-input">
                    <option :value="0">Select company</option>
                    <option v-for="c in companies" :key="c.id" :value="c.id">{{ c.name }}</option>
                  </select>
                </div>
                <div class="form-group">
                  <button @click="applyCompany" :disabled="!selectedCompanyId" class="btn-secondary w-full">Load Company</button>
                </div>
              </div>
              <div class="form-row-3">
                <div class="form-group span-2">
                  <label class="form-label">Employee</label>
                  <select v-model.number="selectedEmployeeId" class="form-input" :disabled="!selectedCompanyId || employees.length === 0">
                    <option :value="0">Select employee</option>
                    <option v-for="e in employees" :key="e.id" :value="e.id">{{ e.first_names }} {{ e.last_name }}</option>
                  </select>
                </div>
                <div class="form-group">
                  <button @click="applyEmployee" :disabled="!selectedEmployeeId" class="btn-secondary w-full">Load Employee</button>
                </div>
              </div>
            </FormSection>

            <!-- Employee Details Card -->
            <FormSection ref="sectionEmployees" title="Employee Details" icon="user">
              <div class="form-group">
                <label class="form-label">First Names</label>
                <input v-model="formData.employee.first_names" type="text" class="form-input" placeholder="Enter first names" />
              </div>
              <div class="form-group">
                <label class="form-label">Last Name</label>
                <input v-model="formData.employee.last_name" type="text" class="form-input" placeholder="Enter last name" />
              </div>
              <div class="form-group">
                <label class="form-label">ID/Passport No.</label>
                <input v-model="formData.employee.id_no" type="text" class="form-input" placeholder="Enter ID or passport number" />
              </div>
              <div class="form-group">
                <label class="form-label">Employee No.</label>
                <input v-model="formData.employee.employee_no" type="text" class="form-input" placeholder="Enter employee number" />
              </div>
              <div class="form-group">
                <label class="form-label">Position</label>
                <input v-model="formData.employee.position" type="text" class="form-input" placeholder="Enter position" />
              </div>
              <div class="form-group">
                <label class="form-label">Tax Reference</label>
                <input v-model="formData.employee.tax_ref" type="text" class="form-input" placeholder="Enter tax reference" />
              </div>
              <div class="form-group span-2">
                <label class="form-label">Employment Date</label>
                <input v-model="formData.employee.emp_date" type="date" class="form-input" />
              </div>
            </FormSection>

            <!-- Pay Period Card -->
            <FormSection ref="sectionEarnings" title="Earnings" icon="money">
              <div class="form-group">
                <label class="form-label">Period Start</label>
                <input v-model="formData.period_start" type="date" class="form-input" />
              </div>
              <div class="form-group">
                <label class="form-label">Period End</label>
                <input v-model="formData.period_end" type="date" class="form-input" />
              </div>
              <div class="form-group">
                <label class="form-label">Payment Date</label>
                <input v-model="formData.payment_date" type="date" class="form-input" />
              </div>
            </FormSection>

            <!-- Calculation Mode Toggle -->
            <FormSection ref="sectionDeductions" title="Deductions" icon="calculator">
              <div class="form-group span-2">
                <p class="text-sm text-muted mb-3">{{ isReverseMode ? 'Calculate gross salary from desired net pay' : 'Calculate net pay from gross salary' }}</p>
                <div class="flex items-center gap-3">
                  <span class="text-sm" :class="!isReverseMode ? 'text-base font-medium' : 'text-muted'">Normal</span>
                  <button @click="toggleCalculationMode" class="toggle-switch" :class="{ active: isReverseMode }">
                    <span class="toggle-thumb" :class="{ active: isReverseMode }"></span>
                  </button>
                  <span class="text-sm" :class="isReverseMode ? 'text-base font-medium' : 'text-muted'">Reverse</span>
                </div>
                <div v-if="isReverseMode" class="info-box info-blue mt-3">
                  <p class="text-sm"><strong>Reverse Calculation Mode:</strong> Enter the desired net pay amount. The system will calculate the required gross salary to achieve this net amount after all deductions.</p>
                </div>
              </div>
            </FormSection>

            <!-- Earnings Card -->
            <FormSection :title="isReverseMode ? 'Net Pay Target' : 'Earnings (Monthly)'" icon="money">
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
            </FormSection>

            <!-- Deductions Card -->
            <FormSection title="Deductions (Monthly)" icon="document">
              <div class="form-group">
                <label class="form-label">Pension/Retirement</label>
                <input v-model.number="formData.pension" type="number" step="0.01" min="0" class="form-input" placeholder="0.00" />
              </div>
              <div class="form-group">
                <label class="form-label">Medical Aid</label>
                <input v-model.number="formData.medical" type="number" step="0.01" min="0" class="form-input" placeholder="0.00" />
              </div>
            </FormSection>

            <!-- SDL Calculation Card -->
            <FormSection ref="sectionSdl" title="Skills Development Levy (SDL)" icon="calculator">
              <div class="form-group">
                <label class="form-label">Annual Payroll</label>
                <input v-model.number="formData.annual_payroll" type="number" step="0.01" min="0" class="form-input" placeholder="0.00" />
                <p class="hint-text">Total annual payroll for SDL threshold check (R500,000+)</p>
              </div>
              <div class="form-group">
                <label class="form-label">Excluded Amounts</label>
                <input v-model.number="formData.excluded_amounts" type="number" step="0.01" min="0" class="form-input" placeholder="0.00" />
                <p class="hint-text">Reimbursements, non-taxable allowances, retirement contributions</p>
              </div>
              <div class="form-group span-2">
                <div class="info-box info-blue">
                  <p class="text-sm"><strong>SDL Information:</strong> SDL is calculated at 1% of total remuneration, but only applies if your annual payroll exceeds R500,000.</p>
                </div>
              </div>
            </FormSection>

            <!-- Leave Income Card -->
            <FormSection title="Leave Income" icon="calendar">
              <div class="form-group">
                <label class="form-label">Leave Days Taken</label>
                <input v-model.number="formData.leave_days_taken" type="number" min="0" max="31" class="form-input" placeholder="0" />
                <p class="hint-text">Number of leave days taken in this period</p>
              </div>
              <div class="form-group">
                <label class="form-label">Total Leave Days Available</label>
                <input v-model.number="formData.total_leave_days_available" type="number" min="0" max="31" class="form-input" placeholder="21" />
                <p class="hint-text">Annual leave days available (default: 21 as per BCEA)</p>
              </div>
              <div class="form-group span-2">
                <div class="info-box info-green">
                  <p class="text-sm"><strong>Leave Income Calculation:</strong> Leave income is calculated based on daily rates from annual salary. Only paid leave days within available limits are included.</p>
                </div>
              </div>
            </FormSection>

            <!-- Company Details Card -->
            <FormSection ref="sectionPeriods" title="Company Details" icon="building">
              <div class="form-group">
                <label class="form-label">Company Name</label>
                <input v-model="formData.company.company_name" type="text" class="form-input" placeholder="Enter company name" />
              </div>
              <div class="form-group">
                <label class="form-label">Registration No.</label>
                <input v-model="formData.company.company_reg_no" type="text" class="form-input" placeholder="Enter registration number" />
              </div>
              <div class="form-group span-2">
                <label class="form-label">Address</label>
                <textarea v-model="formData.company.company_address" rows="2" class="form-input" placeholder="Enter company address"></textarea>
              </div>
              <div class="form-group">
                <label class="form-label">UIF Reference</label>
                <input v-model="formData.company.uif_ref" type="text" class="form-input" placeholder="UIF reference" />
              </div>
              <div class="form-group">
                <label class="form-label">Phone</label>
                <input v-model="formData.company.phone" type="tel" class="form-input" placeholder="Phone number" />
              </div>
              <div class="form-group">
                <label class="form-label">Email</label>
                <input v-model="formData.company.email" type="email" class="form-input" placeholder="Email address" />
              </div>
              <div class="form-group span-2">
                <label class="form-label">Run (e.g., June - 2025)</label>
                <input v-model="formData.company.run" type="text" class="form-input" placeholder="Enter payroll run identifier" />
              </div>
            </FormSection>
          </div>

          <!-- Right Column - Summary & Actions -->
          <div class="summary-column">
            <div class="summary-card sticky">
              <h3 class="summary-title">Payroll Summary</h3>
              
              <div v-if="calculatedData" class="summary-content">
                <div class="summary-item success">
                  <span class="label">Total Earnings</span>
                  <span class="value">R{{ formatCurrency(calculatedData.total_earnings) }}</span>
                </div>
                <div class="summary-item error">
                  <span class="label">Total Deductions</span>
                  <span class="value">R{{ formatCurrency(calculatedData.total_deductions) }}</span>
                </div>
                <div class="summary-item primary">
                  <span class="label">Net Pay</span>
                  <span class="value large">R{{ formatCurrency(calculatedData.net_pay) }}</span>
                </div>
                <div class="detail-breakdown" v-if="calculatedData.paye || calculatedData.uif">
                  <div class="detail-row"><span>PAYE:</span><span>R{{ formatCurrency(calculatedData.paye) }}</span></div>
                  <div class="detail-row"><span>UIF:</span><span>R{{ formatCurrency(calculatedData.uif) }}</span></div>
                  <div class="detail-row"><span>Pension:</span><span>R{{ formatCurrency(formData.pension) }}</span></div>
                  <div class="detail-row"><span>Medical:</span><span>R{{ formatCurrency(formData.medical) }}</span></div>
                </div>
              </div>

              <div v-else class="summary-empty">
                <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path>
                </svg>
                <p>Enter payroll details to see calculations</p>
              </div>

              <!-- Action Buttons -->
              <div class="action-buttons">
                <div v-if="auth.roles.includes('manager') && selectedCompanyId && calculatedData" class="approval-row">
                  <button @click="approveRun" class="btn-secondary flex-1">Approve Run</button>
                  <button @click="rejectRun" class="btn-secondary flex-1">Reject Run</button>
                </div>
                <button @click="generatePayslip" :disabled="!calculatedData || isGeneratingPDF" class="btn-secondary w-full">
                  <svg v-if="isGeneratingPDF" class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {{ isGeneratingPDF ? 'Generating...' : 'Generate Payslip PDF' }}
                </button>
                <template v-if="calculatedData?.record_id">
                  <div v-if="distributeStatus === 'distributed'" class="distribute-badge">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                    Distributed to portal
                  </div>
                  <button v-else @click="distributeOne" :disabled="distributing" class="btn-secondary w-full">
                    {{ distributing ? 'Distributing…' : 'Distribute to Employee Portal' }}
                  </button>
                  <p v-if="distributeError" class="distribute-warn">{{ distributeError }}</p>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Summary Tab -->
      <div v-if="activeTab === 'summary'" class="fade-in tab-content">
        <div class="summary-tab-content">
          <div v-if="calculatedData" class="summary-results">
            <!-- Reverse Calculation Result -->
            <div v-if="isReverseMode && calculatedData.calculated_gross_pay" class="reverse-result">
              <h3>Reverse Calculation Result</h3>
              <div class="result-grid">
                <div class="result-item">
                  <p class="label">Target Net Pay</p>
                  <p class="value">R{{ formatCurrency(formData.target_net_pay) }}</p>
                </div>
                <div class="result-item highlight">
                  <p class="label">Calculated Gross Pay</p>
                  <p class="value">R{{ formatCurrency(calculatedData.calculated_gross_pay) }}</p>
                </div>
              </div>
              <p class="result-note">To achieve a net pay of R{{ formatCurrency(formData.target_net_pay) }}, the employee needs a gross salary of R{{ formatCurrency(calculatedData.calculated_gross_pay) }}.</p>
            </div>

            <!-- Detailed Breakdown -->
            <div class="breakdown-grid">
              <!-- Earnings Breakdown -->
              <div class="breakdown-card">
                <h3>Earnings Breakdown</h3>
                <div class="breakdown-list">
                  <div v-for="[description, amount] in calculatedData.earnings" :key="description" class="breakdown-row">
                    <span>{{ description }}</span>
                    <span class="value">R{{ formatCurrency(amount) }}</span>
                  </div>
                  <div class="breakdown-total">
                    <span>Total Earnings</span>
                    <span class="value">R{{ formatCurrency(calculatedData.total_earnings) }}</span>
                  </div>
                </div>
              </div>

              <!-- Deductions Breakdown -->
              <div class="breakdown-card">
                <h3>Deductions Breakdown</h3>
                <div class="breakdown-list">
                  <div v-for="[description, amount] in calculatedData.deductions" :key="description" class="breakdown-row">
                    <span>{{ description }}</span>
                    <span class="value">R{{ formatCurrency(amount) }}</span>
                  </div>
                  <div class="breakdown-total">
                    <span>Total Deductions</span>
                    <span class="value">R{{ formatCurrency(calculatedData.total_deductions) }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Net Pay Summary -->
            <div class="net-pay-summary">
              <h3>Net Pay</h3>
              <p class="net-pay-value">R{{ formatCurrency(calculatedData.net_pay) }}</p>
              <p class="net-pay-employee">For {{ formData.employee.first_names }} {{ formData.employee.last_name }}</p>
              <p class="net-pay-period">Pay period: {{ formatDate(formData.period_start) }} to {{ formatDate(formData.period_end) }}</p>
            </div>

            <!-- SDL Details -->
            <div v-if="calculatedData.sdl_details && calculatedData.sdl > 0" class="sdl-details">
              <h3>SDL Details</h3>
              <div class="sdl-grid">
                <div class="sdl-item"><span>Total Remuneration:</span><span>R{{ formatCurrency(calculatedData.sdl_details.total_remuneration) }}</span></div>
                <div class="sdl-item"><span>SDL Rate:</span><span>{{ calculatedData.sdl_details.sdl_rate }}</span></div>
                <div class="sdl-item"><span>SDL Amount:</span><span>R{{ formatCurrency(calculatedData.sdl) }}</span></div>
              </div>
            </div>

            <!-- Leave Income Details -->
            <div v-if="calculatedData.leave_income_details && calculatedData.leave_income > 0" class="leave-details">
              <h3>Leave Income Details</h3>
              <div class="leave-grid">
                <div class="leave-item"><span>Annual Salary:</span><span>R{{ formatCurrency(calculatedData.leave_income_details.annual_salary) }}</span></div>
                <div class="leave-item"><span>Daily Rate:</span><span>R{{ formatCurrency(calculatedData.leave_income_details.daily_rate) }}</span></div>
                <div class="leave-item"><span>Leave Days:</span><span>{{ calculatedData.leave_income_details.leave_days_taken }} / {{ calculatedData.leave_income_details.total_leave_days_available }}</span></div>
                <div class="leave-item"><span>Leave Income:</span><span>R{{ formatCurrency(calculatedData.leave_income) }}</span></div>
              </div>
            </div>
          </div>

          <div v-else class="summary-empty-state">
            <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
            </svg>
            <h3>No calculations available</h3>
            <p>Please go to the Details tab and calculate payroll first.</p>
            <button @click="activeTab = 'details'" class="btn-primary">Go to Details</button>
          </div>
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

export default {
  name: 'PayrollView',
  components: {
    MetricCard,
    FormSection
  },
  setup() {
    const auth = useAuthStore()
    const activeTab = ref('details')
    const activeSection = ref('payrun')
    const isCalculating = ref(false)
    const isGeneratingPDF = ref(false)
    const calculatedData = ref(null)
    const isReverseMode = ref(false)

    const tabs = [
      { id: 'details', name: 'Details & Payslip' },
      { id: 'summary', name: 'Summary & Calculations' }
    ]

    const formData = reactive({
      employee: {
        first_names: '',
        last_name: '',
        id_no: '',
        employee_no: '',
        position: '',
        tax_ref: '',
        emp_date: new Date().toISOString().split('T')[0]
      },
      company: {
        company_name: 'OrbitPay',
        company_reg_no: '',
        company_address: '',
        uif_ref: '',
        phone: '',
        email: '',
        run: ''
      },
      period_start: new Date().toISOString().split('T')[0],
      period_end: new Date().toISOString().split('T')[0],
      payment_date: new Date().toISOString().split('T')[0],
      basic_pay: 0,
      other_earnings: 0,
      pension: 0,
      medical: 0,
      target_net_pay: 0,
      annual_payroll: 0,
      excluded_amounts: 0,
      leave_days_taken: 0,
      total_leave_days_available: 21
    })

    const toggleCalculationMode = () => {
      isReverseMode.value = !isReverseMode.value
      calculatedData.value = null
    }

    const sectionPayrun = ref(null)
    const sectionEmployees = ref(null)
    const sectionPeriods = ref(null)
    const sectionEarnings = ref(null)
    const sectionDeductions = ref(null)
    const sectionSdl = ref(null)

    const handleSidebarNav = (section) => {
      activeSection.value = section
      
      // Map sidebar sections to component refs
      const sectionMap = {
        'payrun': sectionPayrun,
        'employees': sectionEmployees,
        'periods': sectionPeriods,
        'earnings': sectionEarnings,
        'deductions': sectionDeductions,
        'sdl': sectionSdl
      }
      
      const targetRef = sectionMap[section]
      if (targetRef?.value?.$el) {
        // Switch to details tab if not already there
        activeTab.value = 'details'
        
        // Scroll to the section with offset for fixed header
        setTimeout(() => {
          const element = targetRef.value.$el
          const offset = 120 // Account for header + nav + some padding
          const top = element.getBoundingClientRect().top + window.pageYOffset - offset
          window.scrollTo({ top, behavior: 'smooth' })
        }, 50)
      }
    }

    // Import data from backend
    const API = ''
    const companies = ref([])
    const employees = ref([])
    const selectedCompanyId = ref(0)
    const selectedEmployeeId = ref(0)

    const loadCompanies = async () => {
      try {
        const { data } = await axios.get(`${API}/companies`)
        companies.value = data
      } catch (e) {
        console.error('Failed to load companies', e)
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
      formData.company.company_name = c?.name || ''
      formData.company.company_reg_no = c?.registration_number || ''
      formData.company.company_address = c?.address || ''
      formData.company.uif_ref = c?.uif_reference || ''
      formData.company.phone = c?.phone || ''
      formData.company.email = c?.email || ''
    }

    const mapEmployeeToForm = (e) => {
      formData.employee.first_names = e?.first_names || ''
      formData.employee.last_name = e?.last_name || ''
      formData.employee.id_no = e?.id_no || ''
      formData.employee.employee_no = e?.employee_no || ''
      formData.employee.position = e?.position || ''
      formData.employee.tax_ref = e?.tax_ref || ''
      formData.employee.emp_date = e?.emp_date || new Date().toISOString().split('T')[0]
      formData.basic_pay = Number(e?.basic_salary ?? 0)
      const allowancesTotal = Number(e?.housing_allowance ?? 0) + Number(e?.transport_allowance ?? 0) + Number(e?.meal_allowance ?? 0) + Number(e?.other_allowances ?? 0)
      formData.other_earnings = allowancesTotal || 0
      formData.pension = Number(e?.pension_contribution ?? 0)
      formData.medical = Number(e?.medical_aid ?? 0)
    }

    const formatCurrency = (amount) => {
      return new Intl.NumberFormat('en-ZA', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(amount || 0)
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString('en-ZA', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    }

    const calculatePayroll = async () => {
      isCalculating.value = true
      distributeStatus.value = ''
      distributeError.value = ''
      try {
        let response
        if (isReverseMode.value) {
          const reverseData = {
            employee: formData.employee,
            company: formData.company,
            period_start: formData.period_start,
            period_end: formData.period_end,
            payment_date: formData.payment_date,
            target_net_pay: formData.target_net_pay,
            pension: formData.pension,
            medical: formData.medical,
            annual_payroll: formData.annual_payroll,
            excluded_amounts: formData.excluded_amounts,
            leave_days_taken: formData.leave_days_taken,
            total_leave_days_available: formData.total_leave_days_available
          }
          response = await axios.post('/calculate-reverse-payroll', reverseData)
          const reverseResult = response.data
          calculatedData.value = {
            employee: reverseResult.employee,
            company: reverseResult.company,
            period_start: reverseResult.period_start,
            period_end: reverseResult.period_end,
            payment_date: reverseResult.payment_date,
            earnings: reverseResult.earnings,
            total_earnings: reverseResult.total_earnings,
            deductions: reverseResult.deductions,
            total_deductions: reverseResult.total_deductions,
            net_pay: reverseResult.net_pay,
            paye: reverseResult.paye,
            uif: reverseResult.uif,
            calculated_gross_pay: reverseResult.calculated_gross_pay,
            sdl: reverseResult.sdl,
            leave_income: reverseResult.leave_income,
            sdl_details: reverseResult.sdl_details,
            leave_income_details: reverseResult.leave_income_details
          }
        } else {
          response = await axios.post('/calculate-payroll', formData)
          calculatedData.value = response.data
        }
      } catch (error) {
        console.error('Error calculating payroll:', error)
        let detail = error?.response?.data?.detail || error.message || 'Unknown error'
        if (Array.isArray(detail)) {
          detail = detail.map(e => e.msg || e).join('\n')
        }
        alert(`Error calculating payroll:\n${detail}`)
      } finally {
        isCalculating.value = false
      }
    }

    const approveRun = async () => {
      try {
        const { data: run } = await axios.post('/payroll-runs', {
          company_id: selectedCompanyId.value,
          period_start: formData.period_start,
          period_end: formData.period_end
        })
        await axios.post(`/payroll-runs/${run.id}/approve`)
        alert('Run approved')
      } catch (e) { alert('Approval failed') }
    }

    const rejectRun = async () => {
      try {
        const { data: run } = await axios.post('/payroll-runs', {
          company_id: selectedCompanyId.value,
          period_start: formData.period_start,
          period_end: formData.period_end
        })
        await axios.post(`/payroll-runs/${run.id}/reject`)
        alert('Run rejected')
      } catch (e) { alert('Reject failed') }
    }

    const generatePayslip = async () => {
      if (!calculatedData.value) return
      isGeneratingPDF.value = true
      try {
        const response = await axios.post('/generate-payslip', calculatedData.value, {
          responseType: 'blob'
        })
        const url = window.URL.createObjectURL(new Blob([response.data]))
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

    const distributing = ref(false)
    const distributeStatus = ref('')
    const distributeError = ref('')

    const distributeOne = async () => {
      if (!calculatedData.value?.record_id) return
      distributing.value = true
      distributeError.value = ''
      try {
        await axios.post(`/payroll-records/${calculatedData.value.record_id}/distribute`)
        distributeStatus.value = 'distributed'
      } catch (e) {
        const detail = e?.response?.data?.detail || 'Distribution failed.'
        distributeError.value = detail
      } finally {
        distributing.value = false
      }
    }

    onMounted(() => {
      loadCompanies()
    })

    return {
      auth,
      activeTab,
      activeSection,
      isCalculating,
      isGeneratingPDF,
      calculatedData,
      isReverseMode,
      tabs,
      formData,
      companies,
      employees,
      selectedCompanyId,
      selectedEmployeeId,
      onCompanyChange,
      applyCompany,
      applyEmployee,
      approveRun,
      rejectRun,
      toggleCalculationMode,
      handleSidebarNav,
      formatCurrency,
      formatDate,
      calculatePayroll,
      generatePayslip,
      distributing, distributeStatus, distributeError, distributeOne,
    }
  }
}
</script>

<style scoped>
.payroll-layout {
  min-height: 100vh;
  background-color: var(--color-bg-page);
}

.payroll-content {
  padding: 24px;
  max-width: 1280px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  flex-direction: column;
}

.page-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-base);
  margin-bottom: 4px;
}

.breadcrumb {
  font-size: 11px;
  color: var(--color-text-muted);
}

.breadcrumb .separator {
  margin: 0 6px;
}

.metric-cards {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.tab-content {
  margin-top: 24px;
}

.form-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 24px;
}

.form-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-row-3 {
  display: grid;
  grid-template-columns: 1fr 1fr 120px;
  gap: 12px;
  align-items: flex-end;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group.span-2 {
  grid-column: span 2;
}

.hint-text {
  font-size: 11px;
  color: var(--color-text-muted);
  margin-top: 4px;
}

.text-muted {
  color: var(--color-text-muted);
}

.text-base {
  color: var(--color-text-base);
}

.font-medium {
  font-weight: 500;
}

.flex {
  display: flex;
}

.items-center {
  align-items: center;
}

.gap-3 {
  gap: 12px;
}

.mt-3 {
  margin-top: 12px;
}

.mb-3 {
  margin-bottom: 12px;
}

.info-box {
  padding: 12px;
  border-radius: 6px;
}

.info-blue {
  background-color: #eff6ff;
  border: 1px solid #bfdbfe;
}

.info-green {
  background-color: #f0fdf4;
  border: 1px solid #bbf7d0;
}

.toggle-switch {
  position: relative;
  width: 44px;
  height: 24px;
  background-color: var(--color-border);
  border-radius: 12px;
  border: none;
  cursor: pointer;
  padding: 0;
}

.toggle-switch.active {
  background-color: var(--color-primary);
}

.toggle-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background-color: white;
  border-radius: 50%;
  transition: transform 0.2s;
}

.toggle-thumb.active {
  transform: translateX(20px);
}

.summary-column {
  position: relative;
}

.summary-card {
  background-color: var(--color-bg-card);
  border: 0.5px solid var(--color-border);
  border-radius: 12px;
  padding: 16px;
}

.summary-card.sticky {
  position: sticky;
  top: 24px;
}

.summary-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-base);
  margin-bottom: 16px;
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-radius: 6px;
}

.summary-item.success {
  background-color: #f0fdf4;
}

.summary-item.error {
  background-color: #fef2f2;
}

.summary-item.primary {
  background-color: #eff6ff;
}

.summary-item .label {
  font-size: 12px;
  font-weight: 500;
}

.summary-item .value {
  font-size: 14px;
  font-weight: 600;
}

.summary-item .value.large {
  font-size: 18px;
}

.summary-item.success .label { color: #166534; }
.summary-item.success .value { color: #15803d; }
.summary-item.error .label { color: #991b1b; }
.summary-item.error .value { color: #dc2626; }
.summary-item.primary .label { color: #1e40af; }
.summary-item.primary .value { color: #2563eb; }

.detail-breakdown {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--color-border);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--color-text-muted);
  padding: 2px 0;
}

.summary-empty {
  text-align: center;
  padding: 32px 0;
  color: var(--color-text-muted);
}

.summary-empty .icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 12px;
  color: var(--color-border);
}

.action-buttons {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.approval-row {
  display: flex;
  gap: 8px;
}

.distribute-badge {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 12px;
  background: #dcfce7; border: 1px solid #86efac; border-radius: 7px;
  font-size: 12.5px; font-weight: 600; color: #15803d;
}

.distribute-warn {
  font-size: 12px; color: #dc2626; margin: 0;
}

.summary-tab-content {
  max-width: 800px;
}

.summary-results {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.reverse-result {
  background-color: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 12px;
  padding: 20px;
}

.reverse-result h3 {
  font-size: 14px;
  font-weight: 600;
  color: #1e40af;
  margin-bottom: 16px;
}

.result-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.result-item {
  background-color: white;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.result-item.highlight {
  border: 2px solid #22c55e;
}

.result-item .label {
  font-size: 11px;
  color: var(--color-text-muted);
  margin-bottom: 4px;
}

.result-item .value {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-base);
}

.result-note {
  font-size: 13px;
  color: #1e40af;
  background-color: white;
  padding: 12px;
  border-radius: 6px;
}

.breakdown-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.breakdown-card {
  background-color: var(--color-bg-card);
  border: 0.5px solid var(--color-border);
  border-radius: 12px;
  padding: 16px;
}

.breakdown-card h3 {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-base);
  margin-bottom: 16px;
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

.breakdown-row .value {
  font-weight: 500;
  color: #15803d;
}

.breakdown-total {
  display: flex;
  justify-content: space-between;
  padding: 12px 0 0;
  margin-top: 8px;
  border-top: 2px solid #bbf7d0;
  font-weight: 600;
  font-size: 14px;
}

.breakdown-total .value {
  color: #15803d;
}

.net-pay-summary {
  background-color: var(--color-bg-card);
  border: 0.5px solid var(--color-border);
  border-radius: 12px;
  padding: 24px;
  text-align: center;
}

.net-pay-summary h3 {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-base);
  margin-bottom: 8px;
}

.net-pay-value {
  font-size: 32px;
  font-weight: 600;
  color: var(--color-primary);
  margin-bottom: 8px;
}

.net-pay-employee {
  font-size: 13px;
  color: var(--color-text-base);
  margin-bottom: 4px;
}

.net-pay-period {
  font-size: 11px;
  color: var(--color-text-muted);
}

.sdl-details,
.leave-details {
  background-color: var(--color-bg-card);
  border: 0.5px solid var(--color-border);
  border-radius: 12px;
  padding: 16px;
}

.sdl-details h3,
.leave-details h3 {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-base);
  margin-bottom: 16px;
}

.sdl-grid,
.leave-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.sdl-item,
.leave-item {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.sdl-item span:first-child,
.leave-item span:first-child {
  color: var(--color-text-muted);
}

.summary-empty-state {
  text-align: center;
  padding: 48px;
  background-color: var(--color-bg-card);
  border: 0.5px solid var(--color-border);
  border-radius: 12px;
}

.summary-empty-state .icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  color: var(--color-border);
}

.summary-empty-state h3 {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-base);
  margin-bottom: 8px;
}

.summary-empty-state p {
  font-size: 13px;
  color: var(--color-text-muted);
  margin-bottom: 16px;
}

@media (max-width: 1024px) {
  .form-layout {
    grid-template-columns: 1fr;
  }
  
  .summary-column {
    order: -1;
  }
  
  .summary-card.sticky {
    position: static;
  }
  
  .breakdown-grid,
  .sdl-grid,
  .leave-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .main-content {
    margin-left: 0;
    padding: 16px;
  }
  
  .payroll-layout {
    flex-direction: column;
  }
  
  .form-row-3 {
    grid-template-columns: 1fr;
  }
  
  .form-group.span-2 {
    grid-column: span 1;
  }
  
  .metric-cards {
    flex-direction: column;
  }
}
</style>
