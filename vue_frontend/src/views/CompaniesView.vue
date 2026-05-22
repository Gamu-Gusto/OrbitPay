<template>
  <div class="view-content">

    <!-- Page header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Companies</h1>
        <p class="page-subtitle">
          {{ companies.length }} {{ companies.length === 1 ? 'company' : 'companies' }} registered
        </p>
      </div>
      <button @click="openCreateCompany" class="btn btn-primary">
        <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
        </svg>
        Add Company
      </button>
    </div>

    <!-- Skeleton while loading -->
    <SkeletonTable v-if="loading" :rows="4" :cols="5" />

    <!-- Companies table card -->
    <div v-else class="card" style="padding: 0;">
      <div class="table-wrap">
        <table v-if="companies.length" class="data-table">
          <thead>
            <tr>
              <th>Company Name</th>
              <th>Reg Number</th>
              <th>UIF Reference</th>
              <th>Email</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="company in companies" :key="company.id">
              <td class="cell-primary font-medium">{{ company.name }}</td>
              <td class="cell-muted">{{ company.registration_number || '—' }}</td>
              <td class="cell-muted">{{ company.uif_reference || '—' }}</td>
              <td class="cell-muted">{{ company.email || '—' }}</td>
              <td>
                <div class="col-actions">
                  <button
                    @click="manageEmployees(company)"
                    class="btn btn-secondary btn-sm"
                  >View Employees</button>
                  <button
                    @click="openEditCompany(company)"
                    class="btn btn-ghost btn-sm"
                  >Edit</button>
                  <button
                    @click="openDeleteConfirm(company)"
                    class="btn btn-danger btn-sm"
                  >Delete</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Empty state -->
        <div v-else class="empty-state">
          <svg class="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
              d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
          </svg>
          <p class="empty-title">No companies yet</p>
          <p>Add your first company to get started.</p>
          <button @click="openCreateCompany" class="btn btn-primary btn-sm">Add Company</button>
        </div>
      </div>
    </div>

    <!-- ── Add / Edit company modal ── -->
    <teleport to="body">
      <div v-if="showModal" class="modal-overlay" @mousedown.self="closeModal">
        <div class="modal">
          <div class="modal-header">
            <h2>{{ editingCompany ? 'Edit Company' : 'New Company' }}</h2>
            <button @click="closeModal" class="modal-close" aria-label="Close">✕</button>
          </div>

          <div class="modal-body">
            <div class="form-grid">
              <div class="form-group">
                <label class="form-label">Company Name <span style="color:var(--color-error)">*</span></label>
                <input v-model="form.name" type="text" class="form-input" placeholder="Acme Corp" />
              </div>

              <div class="form-group">
                <label class="form-label">Registration Number</label>
                <input v-model="form.registration_number" type="text" class="form-input" placeholder="2023/123456/07" />
              </div>

              <div class="form-group span-2">
                <label class="form-label">Address</label>
                <textarea v-model="form.address" rows="2" class="form-input" placeholder="123 Main Street, Johannesburg, 2001"></textarea>
              </div>

              <div class="form-group">
                <label class="form-label">UIF Reference</label>
                <input v-model="form.uif_reference" type="text" class="form-input" placeholder="UIF-000000" />
              </div>

              <div class="form-group">
                <label class="form-label">Phone</label>
                <input v-model="form.phone" type="text" class="form-input" placeholder="+27 11 000 0000" />
              </div>

              <div class="form-group span-2">
                <label class="form-label">Email</label>
                <input v-model="form.email" type="email" class="form-input" placeholder="info@company.co.za" />
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button @click="closeModal" class="btn btn-secondary">Cancel</button>
            <button @click="saveCompany" class="btn btn-primary">
              {{ editingCompany ? 'Save Changes' : 'Create Company' }}
            </button>
          </div>
        </div>
      </div>
    </teleport>

    <!-- ── Delete confirmation modal ── -->
    <teleport to="body">
      <div v-if="showDeleteModal" class="modal-overlay" @mousedown.self="closeDeleteModal">
        <div class="modal modal-narrow">
          <div class="modal-header">
            <h2>Delete Company</h2>
            <button @click="closeDeleteModal" class="modal-close" aria-label="Close">✕</button>
          </div>

          <div class="modal-body">
            <p class="text-base" style="color: var(--color-text-secondary); line-height: 1.6;">
              Are you sure you want to delete
              <strong style="color: var(--color-text-primary);">{{ companyToDelete?.name }}</strong>?
              This action cannot be undone.
            </p>
          </div>

          <div class="modal-footer">
            <button @click="closeDeleteModal" class="btn btn-secondary">Cancel</button>
            <button @click="confirmDelete" class="btn btn-danger">Delete Company</button>
          </div>
        </div>
      </div>
    </teleport>

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

    // Delete confirmation state
    const showDeleteModal = ref(false)
    const companyToDelete = ref(null)

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
        alert('Company name is required')
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

    const openDeleteConfirm = (company) => {
      companyToDelete.value = company
      showDeleteModal.value = true
    }

    const closeDeleteModal = () => {
      showDeleteModal.value = false
      companyToDelete.value = null
    }

    const confirmDelete = async () => {
      if (!companyToDelete.value) return
      const id = companyToDelete.value.id
      closeDeleteModal()

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

    // Kept for backward compatibility — original used confirm(); now replaced by modal
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

    return {
      companies, loading, showModal, editingCompany, form,
      showDeleteModal, companyToDelete,
      openCreateCompany, openEditCompany, closeModal, saveCompany,
      openDeleteConfirm, closeDeleteModal, confirmDelete,
      deleteCompany, manageEmployees, handleSidebarNav
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
</style>
