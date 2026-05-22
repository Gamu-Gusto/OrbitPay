<template>
  <div class="view-content">

    <!-- Page header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Audit Log</h1>
        <p class="page-subtitle">System activity and event history</p>
      </div>
    </div>

    <!-- Filters bar -->
    <div class="filters-bar">
      <select v-model="filterAction" class="form-input filters-bar__select" @change="load">
        <option value="">All Actions</option>
        <option value="user.login">Login</option>
        <option value="employee.create">Employee Created</option>
        <option value="employee.update">Employee Updated</option>
        <option value="employee.delete">Employee Deleted</option>
        <option value="employee.import">CSV Import</option>
        <option value="payroll.bulk_run">Bulk Payroll Run</option>
        <option value="payroll.submit">Payroll Submitted</option>
        <option value="payroll.approve">Payroll Approved</option>
        <option value="payroll.reject">Payroll Rejected</option>
      </select>

      <button @click="load" :disabled="loading" class="btn btn-secondary">
        <span v-if="loading" class="spinner spinner-sm"></span>
        <span>{{ loading ? 'Loading…' : 'Refresh' }}</span>
      </button>

      <span v-if="total > 0" class="filters-bar__count text-sm text-muted">
        {{ total }} total events
      </span>
    </div>

    <!-- Table card -->
    <div class="card" style="padding: 0;">
      <div class="table-wrap">
        <SkeletonTable v-if="loading" :rows="8" :cols="5" />

        <table v-else-if="events.length" class="data-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>User</th>
              <th>Action</th>
              <th>Entity</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="e in events" :key="e.id">
              <!-- Timestamp -->
              <td class="cell-ts mono text-sm text-muted" style="white-space: nowrap;">
                {{ fmtTime(e.timestamp) }}
              </td>

              <!-- User -->
              <td>
                <span class="cell-primary font-medium">{{ e.user_name || 'System' }}</span>
                <span v-if="e.user_email" class="cell-muted" style="display: block;">{{ e.user_email }}</span>
              </td>

              <!-- Action badge -->
              <td>
                <span class="badge" :class="actionBadgeClass(e.action)">
                  {{ actionLabel(e.action) }}
                </span>
              </td>

              <!-- Entity -->
              <td style="white-space: nowrap;">
                <span
                  v-if="e.entity_type"
                  class="text-xs"
                  style="background: var(--color-bg-subtle); border: 1px solid var(--color-border); border-radius: var(--radius-sm); padding: 1px 6px; margin-right: 4px;"
                >{{ e.entity_type }}</span>
                <span v-if="e.entity_id" class="text-xs text-muted">#{{ e.entity_id }}</span>
              </td>

              <!-- Details (truncated) -->
              <td class="cell-details">
                <span
                  class="text-sm text-muted truncate"
                  style="display: block; max-width: 280px; cursor: default;"
                  :title="e.payload"
                >{{ fmtPayload(e.payload) }}</span>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-else class="empty-state">
          <svg class="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
          </svg>
          <p class="empty-title">No audit events found</p>
          <p>Try adjusting the action filter.</p>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="total > pageSize" class="audit-pagination">
        <button @click="prevPage" :disabled="page === 0" class="btn btn-light btn-sm">← Prev</button>
        <span class="text-sm text-muted">Page {{ page + 1 }} of {{ totalPages }}</span>
        <button @click="nextPage" :disabled="page >= totalPages - 1" class="btn btn-light btn-sm">Next →</button>
      </div>
    </div>

  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import SkeletonTable from '../components/ui/SkeletonTable.vue'

const PAGE_SIZE = 50

export default {
  name: 'AuditLogView',
  components: { SkeletonTable },
  setup() {
    const events = ref([])
    const total = ref(0)
    const loading = ref(false)
    const filterAction = ref('')
    const page = ref(0)
    const pageSize = PAGE_SIZE

    const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

    const load = async () => {
      loading.value = true
      try {
        const params = { limit: pageSize, offset: page.value * pageSize }
        if (filterAction.value) params.action = filterAction.value
        const { data } = await axios.get('/audit', { params })
        events.value = data.events
        total.value = data.total
      } catch {}
      loading.value = false
    }

    const prevPage = () => { if (page.value > 0) { page.value--; load() } }
    const nextPage = () => { if (page.value < totalPages.value - 1) { page.value++; load() } }

    const fmtTime = (iso) => {
      if (!iso) return ''
      const d = new Date(iso)
      return d.toLocaleString('en-ZA', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })
    }

    const fmtPayload = (raw) => {
      if (!raw) return '—'
      let text
      try {
        const obj = JSON.parse(raw)
        text = Object.entries(obj).map(([k, v]) => `${k}: ${v}`).join(', ')
      } catch { text = raw }
      return text.length > 60 ? text.slice(0, 60) + '…' : text
    }

    const actionLabel = (action) => ({
      'user.login': 'Login',
      'employee.create': 'Create Employee',
      'employee.update': 'Update Employee',
      'employee.delete': 'Delete Employee',
      'employee.import': 'CSV Import',
      'payroll.bulk_run': 'Bulk Payroll',
      'payroll.submit': 'Submit',
      'payroll.approve': 'Approve',
      'payroll.reject': 'Reject'
    }[action] || action)

    const actionBadgeClass = (action) => {
      if (action.includes('delete') || action.includes('reject')) return 'badge-danger'
      if (action.includes('approve')) return 'badge-success'
      if (action.includes('create') || action.includes('import')) return 'badge-info'
      if (action.includes('update')) return 'badge-neutral'
      if (action.includes('login')) return 'badge-success'
      return 'badge-neutral'
    }

    onMounted(load)

    return {
      events, total, loading, filterAction, page, pageSize, totalPages,
      load, prevPage, nextPage, fmtTime, fmtPayload, actionLabel, actionBadgeClass
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

.filters-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.filters-bar__select { width: 220px; }
.filters-bar__count  { margin-left: auto; }

.audit-pagination {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
  padding: 12px 16px;
  border-top: 1px solid var(--color-border);
}
</style>
