<template>
  <div class="max-w-4xl mx-auto py-8 px-4">
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center space-x-2">
        <button class="btn-light" @click="$router.push('/')">← Back</button>
        <h1 class="text-2xl font-bold text-gray-900">My Payslip</h1>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Payslip Generator -->
      <div class="bg-white rounded-lg shadow border border-gray-200">
        <div class="p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">Generate Payslip</h2>

          <div class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Period Start</label>
                <input v-model="payslipForm.period_start" type="date" class="form-input w-full" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Period End</label>
                <input v-model="payslipForm.period_end" type="date" class="form-input w-full" />
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Payment Date</label>
              <input v-model="payslipForm.payment_date" type="date" class="form-input w-full" />
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Basic Pay (R)</label>
                <input v-model.number="payslipForm.basic_pay" type="number" step="0.01" class="form-input w-full" placeholder="0.00" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Other Earnings (R)</label>
                <input v-model.number="payslipForm.other_earnings" type="number" step="0.01" class="form-input w-full" placeholder="0.00" />
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Pension (R)</label>
                <input v-model.number="payslipForm.pension" type="number" step="0.01" class="form-input w-full" placeholder="0.00" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Medical Aid (R)</label>
                <input v-model.number="payslipForm.medical" type="number" step="0.01" class="form-input w-full" placeholder="0.00" />
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Leave Days Taken</label>
                <input v-model.number="payslipForm.leave_days_taken" type="number" min="0" max="31" class="form-input w-full" placeholder="0" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Available Leave Days</label>
                <input v-model.number="payslipForm.total_leave_days_available" type="number" min="0" max="31" class="form-input w-full" placeholder="21" />
              </div>
            </div>

            <button
              @click="calculatePayslip"
              :disabled="isCalculating"
              class="btn-primary w-full"
            >
              {{ isCalculating ? 'Calculating...' : 'Calculate & Generate Payslip' }}
            </button>
          </div>

          <div v-if="calculationError" class="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p class="text-red-800">{{ calculationError }}</p>
          </div>
        </div>
      </div>

      <!-- Payslip Preview -->
      <div class="bg-white rounded-lg shadow border border-gray-200">
        <div class="p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">Payslip Preview</h2>

          <div v-if="!calculatedData" class="text-center py-8 text-gray-500">
            <svg class="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path>
            </svg>
            <p>Generate a payslip to see preview</p>
          </div>

          <div v-else class="space-y-4">
            <!-- Employee Info -->
            <div class="border-b pb-4">
              <h3 class="font-semibold text-gray-900">{{ calculatedData.employee.first_names }} {{ calculatedData.employee.last_name }}</h3>
              <p class="text-sm text-gray-600">{{ calculatedData.employee.position || 'Employee' }}</p>
              <p class="text-sm text-gray-600">{{ calculatedData.employee.employee_no || 'Employee #' }}</p>
            </div>

            <!-- Earnings -->
            <div>
              <h4 class="font-medium text-gray-900 mb-2">Earnings</h4>
              <div class="space-y-1 text-sm">
                <div v-for="[description, amount] in calculatedData.earnings" :key="description" class="flex justify-between">
                  <span>{{ description }}</span>
                  <span class="font-medium">R{{ formatCurrency(amount) }}</span>
                </div>
                <div class="flex justify-between font-semibold border-t pt-1">
                  <span>Total Earnings</span>
                  <span>R{{ formatCurrency(calculatedData.total_earnings) }}</span>
                </div>
              </div>
            </div>

            <!-- Deductions -->
            <div>
              <h4 class="font-medium text-gray-900 mb-2">Deductions</h4>
              <div class="space-y-1 text-sm">
                <div v-for="[description, amount] in calculatedData.deductions" :key="description" class="flex justify-between">
                  <span>{{ description }}</span>
                  <span class="font-medium">R{{ formatCurrency(amount) }}</span>
                </div>
                <div class="flex justify-between font-semibold border-t pt-1">
                  <span>Total Deductions</span>
                  <span>R{{ formatCurrency(calculatedData.total_deductions) }}</span>
                </div>
              </div>
            </div>

            <!-- Net Pay -->
            <div class="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <div class="flex justify-between items-center">
                <span class="font-semibold text-blue-900">Net Pay</span>
                <span class="text-xl font-bold text-blue-900">R{{ formatCurrency(calculatedData.net_pay) }}</span>
              </div>
            </div>

            <!-- Download Button -->
            <button
              @click="downloadPayslip"
              :disabled="isDownloading"
              class="btn-secondary w-full flex items-center justify-center"
            >
              <svg v-if="isDownloading" class="animate-spin -ml-1 mr-3 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <svg v-else class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
              </svg>
              {{ isDownloading ? 'Generating PDF...' : 'Download PDF' }}
            </button>
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

export default {
  name: 'EmployeePayslipView',
  setup() {
    const auth = useAuthStore()
    const isCalculating = ref(false)
    const isDownloading = ref(false)
    const calculationError = ref('')
    const calculatedData = ref(null)

    const payslipForm = reactive({
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
        name: '',
        registration_number: '',
        address: '',
        uif_reference: '',
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
      leave_days_taken: 0,
      total_leave_days_available: 21
    })

    const API = 'http://localhost:8002'

    const loadEmployeeData = async () => {
      try {
        // Get current user's employee profile
        const { data } = await axios.get(`${API}/my-profile`)

        // Set employee data in form
        payslipForm.employee = {
          first_names: data.first_names,
          last_name: data.last_name,
          id_no: data.id_no,
          employee_no: data.employee_no,
          position: data.position,
          tax_ref: data.tax_ref,
          emp_date: data.emp_date
        }

        // Load company data
        if (data.company_id) {
          const companyResponse = await axios.get(`${API}/companies/${data.company_id}`)
          payslipForm.company = companyResponse.data
        }
      } catch (e) {
        console.error('Error loading employee data:', e)
      }
    }

    const calculatePayslip = async () => {
      isCalculating.value = true
      calculationError.value = ''

      try {
        const response = await axios.post(`${API}/calculate-payroll`, {
          employee: payslipForm.employee,
          company: payslipForm.company,
          period_start: payslipForm.period_start,
          period_end: payslipForm.period_end,
          payment_date: payslipForm.payment_date,
          basic_pay: payslipForm.basic_pay,
          other_earnings: payslipForm.other_earnings,
          pension: payslipForm.pension,
          medical: payslipForm.medical,
          leave_days_taken: payslipForm.leave_days_taken,
          total_leave_days_available: payslipForm.total_leave_days_available,
          annual_payroll: 0,
          excluded_amounts: 0
        })

        calculatedData.value = response.data
      } catch (e) {
        calculationError.value = 'Failed to calculate payslip'
        console.error('Error calculating payslip:', e)
      } finally {
        isCalculating.value = false
      }
    }

    const downloadPayslip = async () => {
      if (!calculatedData.value) return

      isDownloading.value = true

      try {
        const response = await axios.post(`${API}/my-payslip`, calculatedData.value, {
          responseType: 'blob'
        })

        // Create download link
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `payslip_${payslipForm.employee.last_name}_${payslipForm.employee.first_names}_${payslipForm.period_start}.pdf`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
      } catch (e) {
        console.error('Error downloading payslip:', e)
        alert('Error generating payslip. Please try again.')
      } finally {
        isDownloading.value = false
      }
    }

    const formatCurrency = (amount) => {
      return new Intl.NumberFormat('en-ZA', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(amount || 0)
    }

    onMounted(loadEmployeeData)

    return {
      auth,
      payslipForm,
      isCalculating,
      isDownloading,
      calculationError,
      calculatedData,
      calculatePayslip,
      downloadPayslip,
      formatCurrency
    }
  }
}
</script>
