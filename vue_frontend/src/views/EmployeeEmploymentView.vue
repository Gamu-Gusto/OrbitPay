<template>
  <div class="max-w-4xl mx-auto py-8 px-4">
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center space-x-2">
        <button class="btn-light" @click="$router.push('/')">← Back</button>
        <h1 class="text-2xl font-bold text-gray-900">Employment Details</h1>
      </div>
      <button @click="saveEmployment" :disabled="isLoading" class="btn-primary" :class="{ 'opacity-50 cursor-not-allowed': isLoading }">
        {{ isLoading ? 'Saving...' : 'Save Details' }}
      </button>
    </div>

    <div class="bg-white rounded-lg shadow border border-gray-200">
      <div class="p-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Contract Details -->
          <div class="md:col-span-2">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">Contract Details</h2>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Contract Type</label>
            <select v-model="employment.contract_type" class="form-input w-full">
              <option value="">Select contract type</option>
              <option value="permanent">Permanent</option>
              <option value="temporary">Temporary</option>
              <option value="contractor">Contractor</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Job Title</label>
            <input v-model="employment.job_title" type="text" class="form-input w-full" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Contract Start Date</label>
            <input v-model="employment.contract_start_date" type="date" class="form-input w-full" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Contract End Date</label>
            <input v-model="employment.contract_end_date" type="date" class="form-input w-full" />
          </div>

          <!-- Reporting Structure -->
          <div class="md:col-span-2 mt-6">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">Reporting Structure</h2>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Manager</label>
            <select v-model="employment.manager_id" class="form-input w-full">
              <option value="">Select manager</option>
              <option v-for="emp in allEmployees" :key="emp.id" :value="emp.id">
                {{ emp.first_names }} {{ emp.last_name }} ({{ emp.position || emp.job_title }})
              </option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Supervisor</label>
            <select v-model="employment.supervisor_id" class="form-input w-full">
              <option value="">Select supervisor</option>
              <option v-for="emp in allEmployees" :key="emp.id" :value="emp.id">
                {{ emp.first_names }} {{ emp.last_name }} ({{ emp.position || emp.job_title }})
              </option>
            </select>
          </div>

          <!-- Employment Status -->
          <div class="md:col-span-2 mt-6">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">Employment Status</h2>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Current Status</label>
            <select v-model="employment.employment_status" class="form-input w-full">
              <option value="active">Active</option>
              <option value="on_leave">On Leave</option>
              <option value="terminated">Terminated</option>
              <option value="retired">Retired</option>
            </select>
          </div>

          <div v-if="employment.employment_status === 'on_leave'">
            <label class="block text-sm font-medium text-gray-700 mb-1">Leave Start Date</label>
            <input v-model="employment.leave_start_date" type="date" class="form-input w-full" />
          </div>

          <div v-if="employment.employment_status === 'on_leave'">
            <label class="block text-sm font-medium text-gray-700 mb-1">Expected Return Date</label>
            <input v-model="employment.leave_end_date" type="date" class="form-input w-full" />
          </div>

          <div v-if="employment.employment_status === 'terminated'" class="md:col-span-2">
            <label class="block text-sm font-medium text-gray-700 mb-1">Termination Date</label>
            <input v-model="employment.termination_date" type="date" class="form-input w-full" />
          </div>

          <div v-if="employment.employment_status === 'terminated'" class="md:col-span-2">
            <label class="block text-sm font-medium text-gray-700 mb-1">Termination Reason</label>
            <textarea v-model="employment.termination_reason" rows="3" class="form-input w-full" placeholder="Reason for termination..."></textarea>
          </div>
        </div>

        <div v-if="error" class="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p class="text-red-800">{{ error }}</p>
        </div>

        <div v-if="success" class="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <p class="text-green-800">{{ success }}</p>
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
  name: 'EmployeeEmploymentView',
  setup() {
    const auth = useAuthStore()
    const isLoading = ref(false)
    const error = ref('')
    const success = ref('')
    const allEmployees = ref([])

    const employment = reactive({
      contract_type: '',
      job_title: '',
      contract_start_date: '',
      contract_end_date: '',
      manager_id: '',
      supervisor_id: '',
      employment_status: 'active',
      leave_start_date: '',
      leave_end_date: '',
      termination_date: '',
      termination_reason: ''
    })

    const API = 'http://localhost:8002'

    const loadEmployment = async () => {
      try {
        // Get current user's employee profile
        const { data } = await axios.get(`${API}/my-profile`)

        // Load all employees for manager/supervisor selection
        if (data.company_id) {
          const employeesResponse = await axios.get(`${API}/companies/${data.company_id}/employees`)
          allEmployees.value = employeesResponse.data
        }

        // Set employment data from profile
        Object.assign(employment, {
          contract_type: data.contract_type || '',
          job_title: data.job_title || '',
          contract_start_date: data.contract_start_date || '',
          contract_end_date: data.contract_end_date || '',
          manager_id: data.manager_id || '',
          supervisor_id: data.supervisor_id || '',
          employment_status: data.employment_status || 'active',
          leave_start_date: data.leave_start_date || '',
          leave_end_date: data.leave_end_date || '',
          termination_date: data.termination_date || '',
          termination_reason: data.termination_reason || ''
        })
      } catch (e) {
        error.value = 'Failed to load employment data'
        console.error('Error loading employment:', e)
      }
    }

    const saveEmployment = async () => {
      isLoading.value = true
      error.value = ''
      success.value = ''

      try {
        await axios.put(`${API}/my-profile`, employment)
        success.value = 'Employment details updated successfully!'
        setTimeout(() => {
          success.value = ''
        }, 3000)
      } catch (e) {
        error.value = 'Failed to save employment details'
        console.error('Error saving employment:', e)
      } finally {
        isLoading.value = false
      }
    }

    onMounted(loadEmployment)

    return {
      auth,
      employment,
      allEmployees,
      isLoading,
      error,
      success,
      saveEmployment
    }
  }
}
</script>
