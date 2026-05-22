<template>
  <div class="audit-content">

    <div class="page-header">
      <div>
        <h1 class="page-title">Audit Log</h1>
        <div class="breadcrumb"><span>Admin</span><span class="sep">/</span><span>Audit Log</span></div>
      </div>
    </div>

    <!-- Filters -->
    <div class="filter-bar">
      <select v-model="filterAction" class="form-input filter-select" @change="load">
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
      <button @click="load" :disabled="loading" class="btn-secondary">
        {{ loading ? 'Loading…' : 'Refresh' }}
      </button>
      <span class="total-label" v-if="total > 0">{{ total }} total events</span>
    </div>

    <!-- Table -->
    <div class="card">
      <div class="table-wrap">
        <table class="data-table" v-if="events.length">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Action</th>
              <th>User</th>
              <th>Entity</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="e in events" :key="e.id">
              <td class="ts-col">{{ fmtTime(e.timestamp) }}</td>
              <td>
                <span class="badge" :class="actionBadgeClass(e.action)">{{ actionLabel(e.action) }}</span>
              </td>
              <td>
                <div class="user-cell">
                  <span class="user-name">{{ e.user_name || 'System' }}</span>
                  <span class="user-email" v-if="e.user_email">{{ e.user_email }}</span>
                </div>
              </td>
              <td class="entity-col">
                <span v-if="e.entity_type" class="entity-tag">{{ e.entity_type }}</span>
                <span v-if="e.entity_id" class="entity-id">#{{ e.entity_id }}</span>
              </td>
              <td class="payload-col">
                <span class="payload-text" :title="e.payload">{{ fmtPayload(e.payload) }}</span>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else-if="!loading" class="empty-state">No audit events found.</div>
        <SkeletonTable v-if="loading" :rows="8" :cols="4" />
      </div>

      <!-- Pagination -->
      <div class="pagination" v-if="total > pageSize">
        <button @click="prevPage" :disabled="page === 0" class="btn-light page-btn">← Prev</button>
        <span class="page-info">Page {{ page + 1 }} of {{ totalPages }}</span>
        <button @click="nextPage" :disabled="page >= totalPages - 1" class="btn-light page-btn">Next →</button>
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
      try {
        const obj = JSON.parse(raw)
        return Object.entries(obj).map(([k, v]) => `${k}: ${v}`).join(', ')
      } catch { return raw }
    }

    const actionLabel = (action) => ({
      'user.login': 'Login', 'employee.create': 'Create Employee', 'employee.update': 'Update Employee',
      'employee.delete': 'Delete Employee', 'employee.import': 'CSV Import',
      'payroll.bulk_run': 'Bulk Payroll', 'payroll.submit': 'Submit', 'payroll.approve': 'Approve',
      'payroll.reject': 'Reject'
    }[action] || action)

    const actionBadgeClass = (action) => {
      if (action.includes('delete') || action.includes('reject')) return 'badge-red'
      if (action.includes('approve')) return 'badge-green'
      if (action.includes('payroll') || action.includes('import')) return 'badge-blue'
      if (action.includes('login')) return 'badge-purple'
      return 'badge-gray'
    }

    onMounted(load)

    return { events, total, loading, filterAction, page, pageSize, totalPages,
      load, prevPage, nextPage, fmtTime, fmtPayload, actionLabel, actionBadgeClass }
  }
}
</script>

<style scoped>
.audit-content {
  padding: 24px;
  max-width: 1200px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-title { font-size: 16px; font-weight: 500; color: var(--color-text-base); margin: 0 0 4px; }
.breadcrumb { font-size: 11px; color: var(--color-text-muted); }
.sep { margin: 0 6px; }

.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.filter-select { width: 220px; }
.total-label { font-size: 12px; color: var(--color-text-muted); margin-left: auto; }

.card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  overflow: hidden;
}

.table-wrap { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.data-table th {
  padding: 10px 14px; text-align: left; font-size: 11px; font-weight: 600;
  color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.04em;
  border-bottom: 1px solid var(--color-border); background: var(--color-bg-page);
  white-space: nowrap;
}
.data-table td {
  padding: 10px 14px; border-bottom: 1px solid var(--color-border); color: var(--color-text-base); vertical-align: top;
}
.data-table tbody tr:last-child td { border-bottom: none; }
.data-table tbody tr:hover td { background: var(--color-bg-page); }

.ts-col { white-space: nowrap; font-variant-numeric: tabular-nums; font-size: 12px; color: var(--color-text-muted); }
.entity-col { white-space: nowrap; }
.entity-tag { font-size: 11px; background: var(--color-bg-page); border: 1px solid var(--color-border); border-radius: 4px; padding: 1px 6px; margin-right: 4px; }
.entity-id { font-size: 11px; color: var(--color-text-muted); }
.payload-col { max-width: 260px; }
.payload-text { font-size: 11.5px; color: var(--color-text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; cursor: default; }
.user-cell { display: flex; flex-direction: column; }
.user-name { font-size: 12.5px; font-weight: 500; }
.user-email { font-size: 11px; color: var(--color-text-muted); }

.badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; white-space: nowrap; }
.badge-blue { background: #dbeafe; color: #1d4ed8; }
.badge-green { background: #dcfce7; color: #15803d; }
.badge-red { background: #fee2e2; color: #b91c1c; }
.badge-purple { background: #ede9fe; color: #7c3aed; }
.badge-gray { background: var(--color-bg-page); color: var(--color-text-muted); }

.empty-state, .loading-state {
  padding: 40px; text-align: center; color: var(--color-text-muted); font-size: 13px;
  display: flex; align-items: center; justify-content: center; gap: 10px;
}
.spinner { width: 18px; height: 18px; border: 2px solid var(--color-border); border-top-color: var(--color-accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.pagination { display: flex; align-items: center; gap: 14px; justify-content: center; padding: 14px; border-top: 1px solid var(--color-border); }
.page-info { font-size: 12.5px; color: var(--color-text-muted); }
.page-btn { min-width: 80px; }
</style>
