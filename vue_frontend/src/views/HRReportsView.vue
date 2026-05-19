<template>
  <div class="hr-reports-layout">
    <div class="hr-content">
      <!-- Page Header -->
      <div class="page-header">
        <div class="header-left">
          <h1 class="page-title">HR Reports</h1>
          <div class="breadcrumb">
            <span>HR Reports</span>
            <span class="separator">/</span>
            <span>Dashboard</span>
          </div>
        </div>
        <div class="header-right">
          <button @click="exportEmployeesCsv" class="btn-primary" :disabled="loading || filteredEmployeeList.length === 0">
            Export CSV
          </button>
        </div>
      </div>

      <!-- Loading & Error -->
      <div v-if="loading" class="text-sm text-muted mb-4">Loading reports...</div>
      <div v-if="errorMessage" class="text-sm text-error mb-4">{{ errorMessage }}</div>

      <!-- Company Selector -->
      <div class="company-selector mb-6">
        <label class="form-label">Select Company</label>
        <select v-model.number="selectedCompanyId" @change="onCompanyChange" class="form-input w-64" :disabled="loading">
          <option v-for="company in companies" :key="company.id" :value="company.id">{{ company.name }}</option>
        </select>
      </div>

      <!-- Metric Cards -->
      <div v-if="loading" class="skeleton-grid">
        <div v-for="n in 4" :key="n" class="skeleton-card">
          <div class="skeleton-line"></div>
          <div class="skeleton-value"></div>
        </div>
      </div>
      <div v-else class="metrics-grid">
        <MetricCard label="Active Employees" :value="headcount.active" />
        <MetricCard label="Terminated" :value="headcount.terminated" type="error" />
        <MetricCard label="Turnover Rate" :value="turnoverRate + '%'" />
        <MetricCard label="Leave Taken" :value="leaveStats.taken" />
      </div>
    
    <!-- Employee Salary List -->
    <div class="mt-6 bg-white p-6 rounded-lg shadow-sm">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-semibold text-gray-800">Employee Salary Details</h2>
        <div class="flex items-center gap-3">
          <button @click="exportEmployeesCsv" class="px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50" :disabled="loading || filteredEmployeeList.length === 0">
            Export CSV
          </button>
        </div>
      </div>
      <div class="flex flex-wrap items-center gap-3 mb-4">
        <label class="text-sm text-gray-700">Status</label>
        <select v-model="statusFilter" class="form-select w-40">
          <option value="all">All</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
        <label class="text-sm text-gray-700">Position</label>
        <select v-model="positionFilter" class="form-select w-56">
          <option value="">All positions</option>
          <option v-for="pos in uniquePositions" :key="pos" :value="pos">{{ pos }}</option>
        </select>
      </div>
      <div class="overflow-x-auto">
        <table class="min-w-full table-auto border-collapse border border-gray-300">
          <thead class="bg-gray-50">
            <tr>
              <th class="border border-gray-300 px-4 py-2 text-left text-sm font-medium text-gray-700">Employee #</th>
              <th class="border border-gray-300 px-4 py-2 text-left text-sm font-medium text-gray-700">Name</th>
              <th class="border border-gray-300 px-4 py-2 text-left text-sm font-medium text-gray-700">Position</th>
              <th class="border border-gray-300 px-4 py-2 text-right text-sm font-medium text-gray-700">Basic Salary</th>
              <th class="border border-gray-300 px-4 py-2 text-right text-sm font-medium text-gray-700">Allowances</th>
              <th class="border border-gray-300 px-4 py-2 text-right text-sm font-medium text-gray-700">Deductions</th>
              <th class="border border-gray-300 px-4 py-2 text-right text-sm font-medium text-gray-700">Gross Salary</th>
              <th class="border border-gray-300 px-4 py-2 text-center text-sm font-medium text-gray-700">Status</th>
              <th class="border border-gray-300 px-4 py-2 text-left text-sm font-medium text-gray-700">Bank Details</th>
            </tr>
          </thead>
          <tbody>
            <!-- Skeleton rows while loading -->
            <tr v-if="loading" v-for="i in 5" :key="'sk_'+i" class="hover:bg-gray-50 animate-pulse">
              <td class="border border-gray-300 px-4 py-3"><div class="h-3 bg-gray-200 rounded w-16"></div></td>
              <td class="border border-gray-300 px-4 py-3"><div class="h-3 bg-gray-200 rounded w-32"></div></td>
              <td class="border border-gray-300 px-4 py-3"><div class="h-3 bg-gray-200 rounded w-24"></div></td>
              <td class="border border-gray-300 px-4 py-3"><div class="h-3 bg-gray-200 rounded w-20 ml-auto"></div></td>
              <td class="border border-gray-300 px-4 py-3"><div class="h-3 bg-gray-200 rounded w-20 ml-auto"></div></td>
              <td class="border border-gray-300 px-4 py-3"><div class="h-3 bg-gray-200 rounded w-20 ml-auto"></div></td>
              <td class="border border-gray-300 px-4 py-3"><div class="h-3 bg-gray-200 rounded w-24 ml-auto"></div></td>
              <td class="border border-gray-300 px-4 py-3"><div class="h-5 bg-gray-200 rounded w-16 mx-auto"></div></td>
              <td class="border border-gray-300 px-4 py-3"><div class="h-3 bg-gray-200 rounded w-28"></div></td>
            </tr>
            <!-- Actual data rows -->
            <tr v-else v-for="employee in filteredEmployeeList" :key="employee.id" class="hover:bg-gray-50">
              <td class="border border-gray-300 px-4 py-2 text-sm">{{ employee.employee_no || 'N/A' }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm font-medium">{{ employee.full_name }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm">{{ employee.position || 'N/A' }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-right">{{ formatCurrency(employee.basic_salary) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-right">{{ formatCurrency(employee.total_allowances) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-right">{{ formatCurrency(employee.total_deductions) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-right font-semibold">{{ formatCurrency(employee.gross_salary) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-center">
                <span :class="employee.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'" 
                      class="px-2 py-1 rounded-full text-xs font-medium">
                  {{ employee.is_active ? 'Active' : 'Inactive' }}
                </span>
              </td>
              <td class="border border-gray-300 px-4 py-2 text-sm">
                <div v-if="employee.bank_name">
                  <div class="font-medium">{{ employee.bank_name }}</div>
                  <div class="text-gray-600">{{ employee.account_number || 'N/A' }}</div>
                </div>
                <div v-else class="text-gray-400">No bank details</div>
              </td>
            </tr>
            <tr v-if="!loading && filteredEmployeeList.length === 0">
              <td colspan="9" class="border border-gray-300 px-4 py-8 text-center text-gray-500">
                No employees found for the selected company
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- Summary Row -->
      <div class="mt-4 p-4 bg-gray-50 rounded-lg">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span class="font-medium text-gray-700">Total Employees:</span>
            <span class="ml-2 font-bold">{{ filteredEmployeeList.length }}</span>
          </div>
          <div>
            <span class="font-medium text-gray-700">Total Basic Salaries:</span>
            <span class="ml-2 font-bold">{{ formatCurrency(totalBasicSalaries) }}</span>
          </div>
          <div>
            <span class="font-medium text-gray-700">Total Allowances:</span>
            <span class="ml-2 font-bold">{{ formatCurrency(totalAllowances) }}</span>
          </div>
          <div>
            <span class="font-medium text-gray-700">Total Gross Salaries:</span>
            <span class="ml-2 font-bold text-green-600">{{ formatCurrency(totalGrossSalaries) }}</span>
          </div>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'
import { formatCurrencyZAR } from '../utils/format'
import { exportToCSV } from '../utils/export'

import MetricCard from '../components/MetricCard.vue'

export default {
  name: 'HRReportsView',
  components: { MetricCard },
  setup() {
    const headcount = ref({ active: 0, terminated: 0 })
    const turnoverRate = ref(0)
    const leaveStats = ref({ taken: 0, balance: 0 })
    const payrollSummary = ref({ salaries: 0, paye: 0, uif: 0, sdl: 0 })
    const selectedPeriod = ref('monthly')
    const detailedReports = ref(null)
    const auth = useAuthStore()
    const loading = ref(false)
    const errorMessage = ref('')
    const toast = useToastStore()
    
    // Company selection
    const companies = ref([])
    const selectedCompanyId = ref(0)
    
    // Employee salary data
    const employeeList = ref([])

    // Filters
    const statusFilter = ref('all') // all | active | inactive
    const positionFilter = ref('')
    const uniquePositions = computed(() => {
      const set = new Set(
        employeeList.value
          .map(e => e.position)
          .filter(p => p && p.trim().length > 0)
      )
      return Array.from(set).sort()
    })
    const filteredEmployeeList = computed(() => {
      return employeeList.value.filter(e => {
        if (statusFilter.value === 'active' && !e.is_active) return false
        if (statusFilter.value === 'inactive' && e.is_active) return false
        if (positionFilter.value && (e.position || '') !== positionFilter.value) return false
        return true
      })
    })

    const loadCompanies = async () => {
      try {
        const { data } = await axios.get('/companies', {
          headers: { Authorization: `Bearer ${auth.accessToken}` }
        })
        companies.value = data
        if (Array.isArray(data) && data.length > 0) {
          // If no selection yet or selection not in list, default to first company
          const exists = data.some(c => c.id === selectedCompanyId.value)
          if (!exists) {
            selectedCompanyId.value = data[0].id
          }
        }
      } catch (error) {
        console.error('Error loading companies:', error)
        errorMessage.value = 'Failed to load companies.'
        toast.error('Failed to load companies.')
      }
    }

    const fetchReports = async () => {
      try {
        loading.value = true
        errorMessage.value = ''
        console.log('Fetching HR reports...')
        console.log('Auth token:', auth.accessToken ? 'Present' : 'Missing')
        const params = { company_id: selectedCompanyId.value }
        console.log('Request params:', params)
        const response = await axios.get('/api/hr-reports', {
          headers: { Authorization: `Bearer ${auth.accessToken}` },
          params
        })
        console.log('HR reports response:', response.data)
        headcount.value = response.data.headcount
        turnoverRate.value = response.data.turnoverRate
        leaveStats.value = response.data.leaveStats
        payrollSummary.value = response.data.payrollSummary
        employeeList.value = response.data.employeeList || []
        toast.success('HR reports loaded')
      } catch (error) {
        console.error('Error fetching HR reports:', error)
        console.error('Error response:', error.response)
        console.error('Error status:', error.response?.status)
        console.error('Error data:', error.response?.data)
        errorMessage.value = `Failed to load HR reports: ${error.response?.data?.detail || error.message}`
        toast.error(`Failed to load HR reports`)
      } finally {
        loading.value = false
      }
    }

    const fetchDetailedReports = async () => {
      try {
        loading.value = true
        errorMessage.value = ''
        const params = {
          period: selectedPeriod.value,
          company_id: selectedCompanyId.value
        }
        const response = await axios.get('/api/hr-reports/detailed', {
          headers: { Authorization: `Bearer ${auth.accessToken}` },
          params
        })
        detailedReports.value = response.data
        toast.info('Detailed reports loaded')
      } catch (error) {
        console.error('Error fetching detailed reports:', error)
        errorMessage.value = 'Failed to load detailed reports.'
        toast.error('Failed to load detailed reports')
      } finally {
        loading.value = false
      }
    }

    // Computed properties for salary totals
    const totalBasicSalaries = computed(() => {
      return filteredEmployeeList.value.reduce((sum, emp) => sum + (emp.basic_salary || 0), 0)
    })
    
    const totalAllowances = computed(() => {
      return filteredEmployeeList.value.reduce((sum, emp) => sum + (emp.total_allowances || 0), 0)
    })
    
    const totalGrossSalaries = computed(() => {
      return filteredEmployeeList.value.reduce((sum, emp) => sum + (emp.gross_salary || 0), 0)
    })

    const terminationsList = computed(() => {
      if (detailedReports.value && detailedReports.value.turnoverDetails && detailedReports.value.turnoverDetails.terminations) {
        return detailedReports.value.turnoverDetails.terminations
      }
      return []
    })

    const hasTerminations = computed(() => {
      return terminationsList.value.length > 0
    })

    const formatDate = (dateString) => {
      if (!dateString) return '-'
      try {
        return new Date(dateString).toLocaleDateString()
      } catch (e) {
        return '-'
      }
    }

    const exportEmployeesCsv = () => {
      const headers = ['Employee #','Name','Position','Basic Salary','Allowances','Deductions','Gross Salary','Status','Bank Name','Account Number']
      const rows = filteredEmployeeList.value.map(emp => ({
        'Employee #': emp.employee_no || '',
        'Name': emp.full_name,
        'Position': emp.position || '',
        'Basic Salary': emp.basic_salary,
        'Allowances': emp.total_allowances,
        'Deductions': emp.total_deductions,
        'Gross Salary': emp.gross_salary,
        'Status': emp.is_active ? 'Active' : 'Inactive',
        'Bank Name': emp.bank_name || '',
        'Account Number': emp.account_number || ''
      }))
      exportToCSV('employee_salaries.csv', rows, headers)
      toast.success('Employee salaries exported')
    }

    const onCompanyChange = async () => {
      await fetchReports()
      await fetchDetailedReports()
    }

    onMounted(async () => {
      await loadCompanies()
      await fetchReports()
      await fetchDetailedReports()
    })

    return {
      headcount,
      turnoverRate,
      leaveStats,
      payrollSummary,
      selectedPeriod,
      detailedReports,
      fetchReports,
      fetchDetailedReports,
      onCompanyChange,
      companies,
      selectedCompanyId,
      employeeList,
      totalBasicSalaries,
      totalAllowances,
      totalGrossSalaries,
      loading,
      errorMessage,
      formatCurrency: formatCurrencyZAR,
      statusFilter,
      positionFilter,
      uniquePositions,
      filteredEmployeeList,
      exportEmployeesCsv,
      terminationsList,
      hasTerminations,
    }
  }
}
</script>

<style scoped>
.hr-reports-layout {
  min-height: 100vh;
  background-color: var(--color-bg-page);
}

.hr-content {
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

.company-selector {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.w-64 {
  width: 256px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.skeleton-card {
  background-color: var(--color-bg-card);
  border: 0.5px solid var(--color-border);
  border-radius: 8px;
  padding: 16px;
}

.skeleton-line {
  height: 12px;
  background-color: var(--color-border);
  border-radius: 4px;
  margin-bottom: 12px;
  animation: pulse 2s infinite;
}

.skeleton-value {
  height: 24px;
  width: 60%;
  background-color: var(--color-border);
  border-radius: 4px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.text-muted {
  color: var(--color-text-muted);
}

.text-error {
  color: var(--color-error);
}

.mb-4 {
  margin-bottom: 16px;
}

.mb-6 {
  margin-bottom: 24px;
}

.mt-6 {
  margin-top: 24px;
}

@media (max-width: 1024px) {
  .metrics-grid,
  .skeleton-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .hr-content {
    padding: 16px;
  }
  
  .metrics-grid,
  .skeleton-grid {
    grid-template-columns: 1fr;
  }
  
  .w-64 {
    width: 100%;
  }
}
</style>
