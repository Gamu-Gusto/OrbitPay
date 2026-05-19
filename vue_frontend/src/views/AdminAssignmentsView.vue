<template>
  <div class="admin-layout">
    <div class="admin-content">
      <!-- Page Header -->
      <div class="page-header">
        <div class="header-left">
          <h1 class="page-title">Assignments</h1>
          <div class="breadcrumb">
            <span>Admin</span>
            <span class="separator">/</span>
            <span>User Assignments</span>
          </div>
        </div>
      </div>

      <!-- Assignment Cards -->
      <div class="assignments-grid">
        <!-- Assign Accountant -->
        <FormSection title="Assign Accountant to Company" icon="user">
          <div class="form-group span-2">
            <label class="form-label">Select Accountant User</label>
            <select v-model.number="accountant_user_id" class="form-input">
              <option :value="0">Select accountant user</option>
              <option v-for="u in accountants" :key="u.id" :value="u.id">
                {{ u.first_name }} {{ u.last_name }} ({{ u.email }})
              </option>
            </select>
          </div>
          <div class="form-group span-2">
            <label class="form-label">Select Company</label>
            <select v-model.number="company_id_a" class="form-input">
              <option :value="0">Select company</option>
              <option v-for="c in companies" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          <div class="form-group span-2">
            <button @click="assignAccountant" class="btn-primary w-full">Assign Accountant</button>
          </div>
        </FormSection>

        <!-- Assign Client Admin -->
        <FormSection title="Assign Client Admin to Company" icon="user">
          <div class="form-group span-2">
            <label class="form-label">Select Client Admin User</label>
            <select v-model.number="client_admin_user_id" class="form-input">
              <option :value="0">Select client admin user</option>
              <option v-for="u in clientAdmins" :key="u.id" :value="u.id">
                {{ u.first_name }} {{ u.last_name }} ({{ u.email }})
              </option>
            </select>
          </div>
          <div class="form-group span-2">
            <label class="form-label">Select Company</label>
            <select v-model.number="company_id_c" class="form-input">
              <option :value="0">Select company</option>
              <option v-for="c in companies" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          <div class="form-group span-2">
            <button @click="assignClientAdmin" class="btn-primary w-full">Assign Client Admin</button>
          </div>
        </FormSection>
      </div>

      <!-- Link Employee -->
      <FormSection title="Link Employee User to Employee Record" icon="import" class="mt-6">
        <div class="form-group">
          <label class="form-label">Select Employee User</label>
          <select v-model.number="employee_user_id" class="form-input">
            <option :value="0">Select employee user</option>
            <option v-for="u in employeesUsers" :key="u.id" :value="u.id">
              {{ u.first_name }} {{ u.last_name }} ({{ u.email }})
            </option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Select Company</label>
          <select v-model.number="company_id_e" class="form-input" @change="loadCompanyEmployees">
            <option :value="0">Select company</option>
            <option v-for="c in companies" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Select Employee Record</label>
          <select v-model.number="employee_id" class="form-input">
            <option :value="0">Select employee</option>
            <option v-for="e in employees" :key="e.id" :value="e.id">{{ e.first_names }} {{ e.last_name }}</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">&nbsp;</label>
          <button @click="linkEmployee" class="btn-primary w-full">Link Employee</button>
        </div>
      </FormSection>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'

import FormSection from '../components/FormSection.vue'

export default {
  name: 'AdminAssignmentsView',
  components: { FormSection },
  setup() {
    const API = ''
    const companies = ref([])
    const accountants = ref([])
    const clientAdmins = ref([])
    const employeesUsers = ref([])
    const employees = ref([])

    const accountant_user_id = ref(0)
    const client_admin_user_id = ref(0)
    const employee_user_id = ref(0)
    const company_id_a = ref(0)
    const company_id_c = ref(0)
    const company_id_e = ref(0)
    const company_id = ref(0)
    const employee_id = ref(0)

    const loadCompanies = async () => {
      try { const { data } = await axios.get(`${API}/companies`); companies.value = data } catch {}
    }
    const loadUsers = async () => {
      try {
        // Load accountants
        const accountantsResponse = await axios.get(`${API}/users/accountants`)
        accountants.value = accountantsResponse.data
        
        // Load client admins
        const clientAdminsResponse = await axios.get(`${API}/users/client-admins`)
        clientAdmins.value = clientAdminsResponse.data
        
        // Load employee users
        const employeesResponse = await axios.get(`${API}/users/employees`)
        employeesUsers.value = employeesResponse.data
        
        console.log('Loaded users:', {
          accountants: accountants.value.length,
          clientAdmins: clientAdmins.value.length,
          employeeUsers: employeesUsers.value.length
        })
      } catch (error) {
        console.error('Error loading users:', error)
      }
    }
    const loadCompanyEmployees = async () => {
      employees.value = []
      if (company_id_e.value) {
        try { const { data } = await axios.get(`${API}/companies/${company_id_e.value}/employees`); employees.value = data } catch {}
      }
    }

    const assignAccountant = async () => {
      await axios.post(`${API}/assignments/accountant`, { accountant_user_id: accountant_user_id.value, company_id: company_id_a.value })
      alert('Assigned')
    }
    const assignClientAdmin = async () => {
      await axios.post(`${API}/assignments/client-admin`, { user_id: client_admin_user_id.value, company_id: company_id_c.value })
      alert('Assigned')
    }
    const linkEmployee = async () => {
      await axios.post(`${API}/assignments/employee-link`, { user_id: employee_user_id.value, employee_id: employee_id.value })
      alert('Linked')
    }

    onMounted(() => { loadCompanies(); loadUsers() })
    return { companies, accountants, clientAdmins, employeesUsers, employees, accountant_user_id, client_admin_user_id, employee_user_id, company_id_a, company_id_c, company_id_e, employee_id, assignAccountant, assignClientAdmin, linkEmployee, loadCompanyEmployees }
  }
}
</script>

<style scoped>
.admin-layout {
  min-height: 100vh;
  background-color: var(--color-bg-page);
}

.admin-content {
  padding: 24px;
  max-width: 960px;
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

.assignments-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group.span-2 {
  grid-column: span 2;
}

.mt-6 {
  margin-top: 24px;
}

:deep(.section-content) {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

@media (max-width: 1024px) {
  .assignments-grid {
    grid-template-columns: 1fr;
  }
  
  .form-group.span-2 {
    grid-column: span 1;
  }
  
  :deep(.section-content) {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .main-content {
    margin-left: 0;
    padding: 16px;
  }
  
  .admin-layout {
    flex-direction: column;
  }
}
</style>
