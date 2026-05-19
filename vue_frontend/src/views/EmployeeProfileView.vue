<template>
  <div class="max-w-4xl mx-auto py-8 px-4">
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center space-x-2">
        <button class="btn-light" @click="$router.push('/')">← Back</button>
        <h1 class="text-2xl font-bold text-gray-900">Employee Profile</h1>
      </div>
      <button @click="saveProfile" :disabled="isLoading" class="btn-primary" :class="{ 'opacity-50 cursor-not-allowed': isLoading }">
        {{ isLoading ? 'Saving...' : 'Save Profile' }}
      </button>
    </div>

    <div class="bg-white rounded-lg shadow border border-gray-200">
      <div class="p-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Basic Information -->
          <div class="md:col-span-2">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">Basic Information</h2>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">First Names *</label>
            <input v-model="profile.first_names" type="text" class="form-input w-full" required />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Last Name *</label>
            <input v-model="profile.last_name" type="text" class="form-input w-full" required />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Employee Number</label>
            <input v-model="profile.employee_no" type="text" class="form-input w-full" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">ID/Passport Number</label>
            <input v-model="profile.id_no" type="text" class="form-input w-full" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Tax Reference</label>
            <input v-model="profile.tax_ref" type="text" class="form-input w-full" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Employment Date</label>
            <input v-model="profile.emp_date" type="date" class="form-input w-full" />
          </div>

          <!-- Contact Information -->
          <div class="md:col-span-2 mt-6">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">Contact Information</h2>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
            <input v-model="profile.phone" type="tel" class="form-input w-full" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
            <input v-model="profile.email" type="email" class="form-input w-full" />
          </div>

          <!-- Job Details -->
          <div class="md:col-span-2 mt-6">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">Job Details</h2>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Position</label>
            <input v-model="profile.position" type="text" class="form-input w-full" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Job Title</label>
            <input v-model="profile.job_title" type="text" class="form-input w-full" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Department</label>
            <input v-model="profile.department" type="text" class="form-input w-full" />
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
  name: 'EmployeeProfileView',
  setup() {
    const auth = useAuthStore()
    const isLoading = ref(false)
    const error = ref('')
    const success = ref('')

    const profile = reactive({
      first_names: '',
      last_name: '',
      employee_no: '',
      id_no: '',
      tax_ref: '',
      emp_date: '',
      phone: '',
      email: '',
      position: '',
      job_title: '',
      department: ''
    })

    const API = 'http://localhost:8002'

    const loadProfile = async () => {
      try {
        const { data } = await axios.get(`${API}/my-profile`)
        Object.assign(profile, data)
      } catch (e) {
        error.value = 'Failed to load profile data'
        console.error('Error loading profile:', e)
      }
    }

    const saveProfile = async () => {
      isLoading.value = true
      error.value = ''
      success.value = ''

      try {
        await axios.put(`${API}/my-profile`, profile)
        success.value = 'Profile updated successfully!'
        setTimeout(() => {
          success.value = ''
        }, 3000)
      } catch (e) {
        error.value = 'Failed to save profile'
        console.error('Error saving profile:', e)
      } finally {
        isLoading.value = false
      }
    }

    onMounted(loadProfile)

    return {
      auth,
      profile,
      isLoading,
      error,
      success,
      saveProfile
    }
  }
}
</script>
