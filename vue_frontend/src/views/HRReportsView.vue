<template>
  <div class="view-content">

    <!-- Page Header -->
    <div class="page-header" style="margin-bottom:0">
      <div>
        <h1 class="page-title">HR Reports</h1>
        <div class="breadcrumb">
          <span>HR Reports</span>
          <span class="sep">/</span>
          <span>Dashboard</span>
        </div>
      </div>
      <button
        @click="exportEmployeesCsv"
        class="btn btn-secondary"
        :disabled="loading || filteredEmployeeList.length === 0"
      >
        Export CSV
      </button>
    </div>

    <!-- Error -->
    <div v-if="errorMessage" class="info-box info-red">{{ errorMessage }}</div>

    <!-- Company Selector -->
    <div class="card card-sm">
      <div class="form-group" style="max-width:320px">
        <label class="form-label">Select Company</label>
        <select
          v-model.number="selectedCompanyId"
          @change="onCompanyChange"
          class="form-input"
          :disabled="loading"
        >
          <option v-for="company in companies" :key="company.id" :value="company.id">
            {{ company.name }}
          </option>
        </select>
      </div>
    </div>

    <!-- Skeleton while loading -->
    <SkeletonDashboard v-if="loading" />

    <template v-else>
      <!-- Metric Cards -->
      <div class="metrics-grid">
        <MetricCard label="Active Employees"  :value="headcount.active"     />
        <MetricCard label="Terminated"        :value="headcount.terminated" type="error" />
        <MetricCard label="Turnover Rate"     :value="turnoverRate + '%'"   />
        <MetricCard label="Leave Taken"       :value="leaveStats.taken"     />
      </div>

      <!-- Employee Salary Details -->
      <div class="card" style="padding:0;overflow:hidden">
        <!-- Card header -->
        <div class="card-header" style="padding:16px 20px;margin-bottom:0">
          <h2 class="card-title">Employee Salary Details</h2>
          <button
            @click="exportEmployeesCsv"
            class="btn btn-secondary btn-sm"
            :disabled="loading || filteredEmployeeList.length === 0"
          >
            Export CSV
          </button>
        </div>

        <!-- Filters -->
        <div style="display:flex;flex-wrap:wrap;align-items:flex-end;gap:16px;padding:14px 20px;border-bottom:1px solid var(--color-border)">
          <div class="form-group" style="min-width:140px">
            <label class="form-label">Status</label>
            <select v-model="statusFilter" class="form-input">
              <option value="all">All</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
          <div class="form-group" style="min-width:200px">
            <label class="form-label">Position</label>
            <select v-model="positionFilter" class="form-input">
              <option value="">All positions</option>
              <option v-for="pos in uniquePositions" :key="pos" :value="pos">{{ pos }}</option>
            </select>
          </div>
        </div>

        <!-- Table -->
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Employee #</th>
                <th>Name</th>
                <th>Position</th>
                <th class="col-right">Basic Salary</th>
                <th class="col-right">Allowances</th>
                <th class="col-right">Deductions</th>
                <th class="col-right">Gross Salary</th>
                <th style="text-align:center">Status</th>
                <th>Bank Details</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="filteredEmployeeList.length === 0">
                <td colspan="9">
                  <div class="empty-state" style="padding:40px 24px">
                    <p>No employees found for the selected filters.</p>
                  </div>
                </td>
              </tr>
              <tr v-for="employee in filteredEmployeeList" :key="employee.id">
                <td class="cell-muted">{{ employee.employee_no || 'N/A' }}</td>
                <td class="cell-primary">{{ employee.full_name }}</td>
                <td>{{ employee.position || 'N/A' }}</td>
                <td class="col-right">{{ formatCurrency(employee.basic_salary) }}</td>
                <td class="col-right">{{ formatCurrency(employee.total_allowances) }}</td>
                <td class="col-right">{{ formatCurrency(employee.total_deductions) }}</td>
                <td class="col-right" style="font-weight:600">{{ formatCurrency(employee.gross_salary) }}</td>
                <td style="text-align:center">
                  <span
                    class="badge"
                    :class="employee.is_active ? 'badge-success' : 'badge-neutral'"
                  >
                    {{ employee.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </td>
                <td>
                  <template v-if="employee.bank_name">
                    <div class="cell-primary" style="font-size:12px">{{ employee.bank_name }}</div>
                    <div class="cell-muted">{{ employee.account_number || 'N/A' }}</div>
                  </template>
                  <span v-else class="cell-muted">No bank details</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Summary footer -->
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;padding:14px 20px;background:var(--color-bg-subtle);border-top:1px solid var(--color-border)">
          <div>
            <div class="section-label" style="margin-bottom:4px">Total Employees</div>
            <div style="font-size:14px;font-weight:600;color:var(--color-text-primary)">{{ filteredEmployeeList.length }}</div>
          </div>
          <div>
            <div class="section-label" style="margin-bottom:4px">Total Basic Salaries</div>
            <div style="font-size:14px;font-weight:600;color:var(--color-text-primary)">{{ formatCurrency(totalBasicSalaries) }}</div>
          </div>
          <div>
            <div class="section-label" style="margin-bottom:4px">Total Allowances</div>
            <div style="font-size:14px;font-weight:600;color:var(--color-text-primary)">{{ formatCurrency(totalAllowances) }}</div>
          </div>
          <div>
            <div class="section-label" style="margin-bottom:4px">Total Gross Salaries</div>
            <div style="font-size:14px;font-weight:600;color:var(--color-success)">{{ formatCurrency(totalGrossSalaries) }}</div>
          </div>
        </div>
      </div>
    </template>

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
import SkeletonDashboard from '../components/ui/SkeletonDashboard.vue'

export default {
  name: 'HRReportsView',
  components: { MetricCard, SkeletonDashboard },
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
.view-content {
  padding: 24px;
  max-width: 1280px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

@media (max-width: 1024px) {
  .metrics-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 640px) {
  .view-content { padding: 16px; }
  .metrics-grid { grid-template-columns: 1fr; }
}
</style>
