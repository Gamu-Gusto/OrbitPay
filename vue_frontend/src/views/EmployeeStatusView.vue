<template>
  <div class="max-w-4xl mx-auto py-8 px-4">
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center space-x-2">
        <button class="btn-light" @click="$router.push('/')">← Back</button>
        <h1 class="text-2xl font-bold text-gray-900">Status Tracking</h1>
      </div>
      <button @click="saveStatus" :disabled="isLoading" class="btn-primary" :class="{ 'opacity-50 cursor-not-allowed': isLoading }">
        {{ isLoading ? 'Saving...' : 'Update Status' }}
      </button>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Current Status -->
      <div class="bg-white rounded-lg shadow border border-gray-200">
        <div class="p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">Current Employment Status</h2>

          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <div class="flex items-center space-x-3">
                <select v-model="status.employment_status" class="form-input flex-1">
                  <option value="active">Active</option>
                  <option value="on_leave">On Leave</option>
                  <option value="terminated">Terminated</option>
                  <option value="retired">Retired</option>
                </select>
                <div :class="getStatusBadgeClass(status.employment_status)" class="px-3 py-1 rounded-full text-sm font-medium">
                  {{ getStatusLabel(status.employment_status) }}
                </div>
              </div>
            </div>

            <div v-if="status.employment_status === 'on_leave'" class="space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Leave Start Date</label>
                <input v-model="status.leave_start_date" type="date" class="form-input w-full" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Expected Return Date</label>
                <input v-model="status.leave_end_date" type="date" class="form-input w-full" />
              </div>
            </div>

            <div v-if="status.employment_status === 'terminated'" class="space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Termination Date</label>
                <input v-model="status.termination_date" type="date" class="form-input w-full" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Termination Reason</label>
                <textarea v-model="status.termination_reason" rows="3" class="form-input w-full" placeholder="Reason for termination..."></textarea>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Status History -->
      <div class="bg-white rounded-lg shadow border border-gray-200">
        <div class="p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">Status History</h2>

          <div v-if="statusHistory.length === 0" class="text-center py-8 text-gray-500">
            <svg class="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
            </svg>
            <p>No status history available</p>
          </div>

          <div v-else class="space-y-3">
            <div v-for="record in statusHistory" :key="record.id" class="border-l-4 border-blue-500 pl-4 pb-3">
              <div class="flex items-start justify-between">
                <div>
                  <div class="flex items-center space-x-2 mb-1">
                    <span class="font-medium text-gray-900">{{ getStatusLabel(record.status) }}</span>
                    <span class="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                      {{ formatDate(record.date) }}
                    </span>
                  </div>
                  <p v-if="record.reason" class="text-sm text-gray-600">{{ record.reason }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Leave Balance -->
    <div class="mt-6 bg-white rounded-lg shadow border border-gray-200">
      <div class="p-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Leave Information</h2>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="text-center p-4 bg-green-50 rounded-lg border border-green-200">
            <div class="text-2xl font-bold text-green-700">{{ leaveBalance.annual_leave || 0 }}</div>
            <div class="text-sm text-green-600">Annual Leave Days</div>
          </div>

          <div class="text-center p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div class="text-2xl font-bold text-blue-700">{{ leaveBalance.sick_leave || 0 }}</div>
            <div class="text-sm text-blue-600">Sick Leave Days</div>
          </div>

          <div class="text-center p-4 bg-purple-50 rounded-lg border border-purple-200">
            <div class="text-2xl font-bold text-purple-700">{{ leaveBalance.family_responsibility || 0 }}</div>
            <div class="text-sm text-purple-600">Family Responsibility Days</div>
          </div>
        </div>

        <div class="mt-4 p-4 bg-gray-50 rounded-lg">
          <h3 class="font-medium text-gray-900 mb-2">Leave Policy</h3>
          <ul class="text-sm text-gray-600 space-y-1">
            <li>• Annual leave: 21 days per year (as per BCEA)</li>
            <li>• Sick leave: 30 days over 3 years</li>
            <li>• Family responsibility leave: 3 days per year</li>
            <li>• Maternity leave: 4 months</li>
          </ul>
        </div>
      </div>
    </div>

    <div v-if="error" class="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
      <p class="text-red-800">{{ error }}</p>
    </div>

    <div v-if="success" class="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
      <p class="text-green-800">{{ success }}</p>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

export default {
  name: 'EmployeeStatusView',
  setup() {
    const auth = useAuthStore()
    const isLoading = ref(false)
    const error = ref('')
    const success = ref('')

    const status = reactive({
      employment_status: 'active',
      leave_start_date: '',
      leave_end_date: '',
      termination_date: '',
      termination_reason: ''
    })

    const leaveBalance = reactive({
      annual_leave: 15,
      sick_leave: 10,
      family_responsibility: 2
    })

    const statusHistory = ref([
      {
        id: 1,
        status: 'active',
        date: '2024-01-01',
        reason: 'New employment started'
      }
    ])

    const API = 'http://localhost:8002'

    const loadStatus = async () => {
      try {
        // Get current user's employee profile
        const { data } = await axios.get(`${API}/my-profile`)

        // Set status data from profile
        Object.assign(status, {
          employment_status: data.employment_status || 'active',
          leave_start_date: data.leave_start_date || '',
          leave_end_date: data.leave_end_date || '',
          termination_date: data.termination_date || '',
          termination_reason: data.termination_reason || ''
        })

        // Set leave balance (mock data for now)
        leaveBalance.annual_leave = 21 - (data.leave_days_taken || 0)
        leaveBalance.sick_leave = 30
        leaveBalance.family_responsibility = 3
      } catch (e) {
        error.value = 'Failed to load status data'
        console.error('Error loading status:', e)
      }
    }

    const saveStatus = async () => {
      isLoading.value = true
      error.value = ''
      success.value = ''

      try {
        await axios.put(`${API}/my-profile`, status)
        success.value = 'Status updated successfully!'
        setTimeout(() => {
          success.value = ''
        }, 3000)
      } catch (e) {
        error.value = 'Failed to save status'
        console.error('Error saving status:', e)
      } finally {
        isLoading.value = false
      }
    }

    const getStatusLabel = (statusValue) => {
      const labels = {
        active: 'Active',
        on_leave: 'On Leave',
        terminated: 'Terminated',
        retired: 'Retired'
      }
      return labels[statusValue] || statusValue
    }

    const getStatusBadgeClass = (statusValue) => {
      const classes = {
        active: 'bg-green-100 text-green-800',
        on_leave: 'bg-yellow-100 text-yellow-800',
        terminated: 'bg-red-100 text-red-800',
        retired: 'bg-gray-100 text-gray-800'
      }
      return classes[statusValue] || 'bg-gray-100 text-gray-800'
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString('en-ZA', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    onMounted(loadStatus)

    return {
      auth,
      status,
      leaveBalance,
      statusHistory,
      isLoading,
      error,
      success,
      saveStatus,
      getStatusLabel,
      getStatusBadgeClass,
      formatDate
    }
  }
}
</script>
