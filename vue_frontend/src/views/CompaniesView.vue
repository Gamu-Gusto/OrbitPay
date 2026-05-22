<template>
  <div class="companies-layout">
    <div class="companies-content">
      <!-- Page Header -->
      <div class="page-header">
        <div class="header-left">
          <h1 class="page-title">Companies</h1>
          <div class="breadcrumb">
            <span>Companies</span>
            <span class="separator">/</span>
            <span>All Companies</span>
          </div>
        </div>
        <div class="header-right">
          <button @click="openCreateCompany" class="btn-primary">New Company</button>
        </div>
      </div>

      <!-- Loading skeleton -->
      <SkeletonTable v-if="loading" :rows="4" :cols="3" />

      <!-- Companies Table -->
      <div v-else class="card">
        <table class="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Registration #</th>
              <th>UIF Reference</th>
              <th>Email</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="company in companies" :key="company.id">
              <td class="font-medium">{{ company.name }}</td>
              <td>{{ company.registration_number || '-' }}</td>
              <td>{{ company.uif_reference || '-' }}</td>
              <td>{{ company.email || '-' }}</td>
              <td class="actions">
                <button @click="openEditCompany(company)" class="btn-text">Edit</button>
                <button @click="deleteCompany(company.id)" class="btn-text danger">Delete</button>
                <button @click="manageEmployees(company)" class="btn-text">Employees</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="companies.length === 0" class="empty-state">
          <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
          </svg>
          <p>No companies yet.</p>
          <button @click="openCreateCompany" class="btn-primary">Add your first company</button>
        </div>
      </div>

      <!-- Modal -->
      <div v-if="showModal" class="modal-overlay">
        <div class="modal">
          <div class="modal-header">
            <h2>{{ editingCompany ? 'Edit Company' : 'New Company' }}</h2>
            <button @click="closeModal" class="modal-close">✕</button>
          </div>
          <div class="modal-body">
            <div class="form-grid">
              <div class="form-group">
                <label class="form-label">Name</label>
                <input v-model="form.name" type="text" class="form-input" />
              </div>
              <div class="form-group">
                <label class="form-label">Registration #</label>
                <input v-model="form.registration_number" type="text" class="form-input" />
              </div>
              <div class="form-group span-2">
                <label class="form-label">Address</label>
                <textarea v-model="form.address" rows="2" class="form-input"></textarea>
              </div>
              <div class="form-group">
                <label class="form-label">UIF Reference</label>
                <input v-model="form.uif_reference" type="text" class="form-input" />
              </div>
              <div class="form-group">
                <label class="form-label">Phone</label>
                <input v-model="form.phone" type="text" class="form-input" />
              </div>
              <div class="form-group span-2">
                <label class="form-label">Email</label>
                <input v-model="form.email" type="email" class="form-input" />
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button @click="closeModal" class="btn-secondary">Cancel</button>
            <button @click="saveCompany" class="btn-primary">Save</button>
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
import { useRouter } from 'vue-router'
import SkeletonTable from '../components/ui/SkeletonTable.vue'
export default {
  name: 'CompaniesView',
  components: { SkeletonTable },
  setup(_, { emit, expose }) {
    const companies = ref([])
    const loading = ref(false)
    const showModal = ref(false)
    const editingCompany = ref(null)
    const router = useRouter()
    const form = reactive({
      name: '',
      registration_number: '',
      address: '',
      uif_reference: '',
      phone: '',
      email: ''
    })

        const authStore = useAuthStore()

    // Using relative URLs to go through Vite proxy

    const loadCompanies = async () => {
      loading.value = true
      try {
        console.log('Loading companies')
        const { data } = await axios.get('/companies', {
          headers: { Authorization: `Bearer ${authStore.accessToken}` }
        })
        console.log('Companies loaded successfully:', data)
        companies.value = data
      } catch (error) {
        console.error('Error loading companies:', error)
        console.error('Error type:', typeof error)
        console.error('Error response:', error.response)
        console.error('Error response data:', error.response?.data)
        
        let errorMessage = 'Failed to load companies'
        
        if (error.response?.data?.detail) {
          errorMessage = String(error.response.data.detail)
        } else if (error.response?.data?.message) {
          errorMessage = String(error.response.data.message)
        } else if (error.response?.data?.error) {
          errorMessage = String(error.response.data.error)
        } else if (error.message) {
          errorMessage = String(error.message)
        } else if (typeof error === 'string') {
          errorMessage = String(error)
        } else if (error.response?.statusText) {
          errorMessage = `HTTP ${error.response.status}: ${error.response.statusText}`
        }
        
        console.log('Final error message:', errorMessage)
        alert(`Error: ${errorMessage}`)
      } finally {
        loading.value = false
      }
    }

    const openCreateCompany = () => {
      console.log('Opening create company modal')
      editingCompany.value = null
      Object.assign(form, { name: '', registration_number: '', address: '', uif_reference: '', phone: '', email: '' })
      showModal.value = true
    }

    const openEditCompany = (company) => {
      editingCompany.value = company
      Object.assign(form, company)
      showModal.value = true
    }

    const closeModal = () => { showModal.value = false }

    const saveCompany = async () => {
      // Client-side validation
      if (!form.name || form.name.trim() === '') { 
        alert('Company name is required'); 
        return 
      }
      
      // Validate email format if provided
      if (form.email && form.email.trim() !== '') {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        if (!emailRegex.test(form.email)) {
          alert('Please enter a valid email address')
          return
        }
      }
      
      try {
        console.log('Saving company with data:', form)
        
        // Clean the data - remove empty strings and convert to null for optional fields
        const cleanData = {
          name: form.name.trim(),
          registration_number: form.registration_number?.trim() || null,
          address: form.address?.trim() || null,
          uif_reference: form.uif_reference?.trim() || null,
          phone: form.phone?.trim() || null,
          email: form.email?.trim() || null
        }
        
        console.log('Cleaned data:', cleanData)
        
        if (editingCompany.value) {
          console.log('Updating company:', editingCompany.value.id)
          await axios.put(`/companies/${editingCompany.value.id}`, cleanData, {
          headers: { Authorization: `Bearer ${authStore.accessToken}` }
        })
        } else {
          console.log('Creating new company')
          await axios.post('/companies', cleanData, {
          headers: { Authorization: `Bearer ${authStore.accessToken}` }
        })
        }
        console.log('Company saved successfully')
        showModal.value = false
        await loadCompanies()
      } catch (error) {
        console.error('Error saving company:', error)
        console.error('Error type:', typeof error)
        console.error('Error response:', error.response)
        console.error('Error response data:', error.response?.data)
        
        let errorMessage = 'Failed to save company'
        
        // Handle 422 validation errors specifically
        if (error.response?.status === 422 && error.response?.data?.detail) {
          const validationErrors = error.response.data.detail
          if (Array.isArray(validationErrors)) {
            const errorMessages = validationErrors.map(err => {
              const field = err.loc ? err.loc.join('.') : 'field'
              return `${field}: ${err.msg}`
            })
            errorMessage = `Validation errors:\n${errorMessages.join('\n')}`
          } else {
            errorMessage = String(validationErrors)
          }
        } else if (error.response?.data?.detail) {
          errorMessage = String(error.response.data.detail)
        } else if (error.response?.data?.message) {
          errorMessage = String(error.response.data.message)
        } else if (error.response?.data?.error) {
          errorMessage = String(error.response.data.error)
        } else if (error.message) {
          errorMessage = String(error.message)
        } else if (typeof error === 'string') {
          errorMessage = String(error)
        } else if (error.response?.statusText) {
          errorMessage = `HTTP ${error.response.status}: ${error.response.statusText}`
        }
        
        console.log('Final error message:', errorMessage)
        alert(`Error: ${errorMessage}`)
      }
    }

    const deleteCompany = async (id) => {
      if (!confirm('Delete this company?')) return
      
      try {
        await axios.delete(`/companies/${id}`, {
          headers: { Authorization: `Bearer ${authStore.accessToken}` }
        })
        await loadCompanies()
      } catch (error) {
        console.error('Error deleting company:', error)
        let errorMessage = 'Failed to delete company'
        
        if (error.response?.data?.detail) {
          errorMessage = error.response.data.detail
        } else if (error.response?.data?.message) {
          errorMessage = error.response.data.message
        } else if (error.message) {
          errorMessage = error.message
        } else if (typeof error === 'string') {
          errorMessage = error
        }
        
        alert(`Error: ${errorMessage}`)
      }
    }

    const manageEmployees = (company) => {
      router.push({ name: 'companyEmployees', params: { companyId: company.id } })
    }

    const handleSidebarNav = (section) => {
      // Handle sidebar navigation if needed
      console.log('Navigating to:', section)
    }

    onMounted(() => {
      console.log('CompaniesView mounted, loading companies...')
      loadCompanies()
    })

    return { companies, loading, showModal, editingCompany, form, openCreateCompany, openEditCompany, closeModal, saveCompany, deleteCompany, manageEmployees, handleSidebarNav }
  }
}
</script>

<style scoped>
.companies-layout {
  min-height: 100vh;
  background-color: var(--color-bg-page);
}

.companies-content {
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

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead {
  background-color: var(--color-bg-header);
}

.data-table th {
  padding: 12px 16px;
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.3px;
  border-bottom: 1px solid var(--color-border);
}

.data-table td {
  padding: 12px 16px;
  font-size: 13px;
  color: var(--color-text-base);
  border-bottom: 1px solid var(--color-border);
}

.data-table tr:hover {
  background-color: var(--color-primary-light);
}

.data-table .font-medium {
  font-weight: 500;
}

.data-table .actions {
  display: flex;
  gap: 8px;
}

.btn-text {
  font-size: 12px;
  color: var(--color-primary);
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
}

.btn-text:hover {
  background-color: var(--color-primary-light);
  border-radius: 4px;
}

.btn-text.danger {
  color: var(--color-error);
}

.btn-text.danger:hover {
  background-color: #fef2f2;
}

.empty-state {
  text-align: center;
  padding: 48px;
}

.empty-state .icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 16px;
  color: var(--color-border);
}

.empty-state p {
  font-size: 13px;
  color: var(--color-text-muted);
  margin-bottom: 16px;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  z-index: 100;
}

.modal {
  background-color: var(--color-bg-card);
  border-radius: 12px;
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border);
}

.modal-header h2 {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-base);
}

.modal-close {
  font-size: 18px;
  color: var(--color-text-muted);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  color: var(--color-text-base);
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--color-border);
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group.span-2 {
  grid-column: span 2;
}

@media (max-width: 640px) {
  .companies-content {
    padding: 16px;
  }

  .data-table {
    font-size: 12px;
  }
  
  .data-table th,
  .data-table td {
    padding: 8px 12px;
  }
  
  .data-table .actions {
    flex-direction: column;
    gap: 4px;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .form-group.span-2 {
    grid-column: span 1;
  }
}
</style>

