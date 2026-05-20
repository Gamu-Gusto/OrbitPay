<template>
  <div class="dashboard-content">

    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Dashboard</h1>
        <p class="page-sub">{{ greeting }}, {{ firstName }}. Here's what needs your attention.</p>
      </div>
      <div class="header-actions">
        <router-link to="/payroll/bulk" class="btn-primary" v-if="hasRole(['super_admin','accountant'])">Run Payroll</router-link>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-row">
      <div class="spinner"></div>
      <span>Loading dashboard…</span>
    </div>

    <template v-else>
      <!-- Stat cards -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon blue">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <path d="M3 21h18M3 7l9-4 9 4M4 7v14M20 7v14M9 21v-4a3 3 0 016 0v4"/>
            </svg>
          </div>
          <div class="stat-body">
            <span class="stat-val">{{ stats.companies }}</span>
            <span class="stat-label">{{ stats.companies === 1 ? 'Company' : 'Companies' }}</span>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon green">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/>
            </svg>
          </div>
          <div class="stat-body">
            <span class="stat-val">{{ stats.employees?.active }}</span>
            <span class="stat-label">Active Employees</span>
            <span class="stat-sub">{{ stats.employees?.inactive }} inactive</span>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon purple">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <rect x="2" y="3" width="8" height="10" rx="1"/><rect x="14" y="3" width="8" height="6" rx="1"/>
              <rect x="14" y="13" width="8" height="8" rx="1"/><rect x="2" y="17" width="8" height="4" rx="1"/>
            </svg>
          </div>
          <div class="stat-body">
            <span class="stat-val">R {{ fmtMoney(stats.current_month?.total_net_pay) }}</span>
            <span class="stat-label">{{ stats.current_month?.period }} Net Payroll</span>
            <span class="stat-sub">{{ stats.current_month?.employees_processed }} employees processed</span>
          </div>
        </div>

        <div class="stat-card" :class="stats.pending_approvals > 0 ? 'card-warn' : ''">
          <div class="stat-icon" :class="stats.pending_approvals > 0 ? 'orange' : 'gray'">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
            </svg>
          </div>
          <div class="stat-body">
            <span class="stat-val">{{ stats.pending_approvals }}</span>
            <span class="stat-label">Pending Approvals</span>
            <router-link v-if="stats.pending_approvals > 0" to="/payroll/bulk" class="stat-action">Review →</router-link>
          </div>
        </div>
      </div>

      <!-- Approval Queue Cards (super_admin only) -->
      <div v-if="hasRole(['super_admin'])" class="approvals-grid">
        <router-link to="/approvals/leave" class="approval-card" :class="stats.pending_leave > 0 ? 'approval-card--active' : ''">
          <div class="approval-icon" :class="stats.pending_leave > 0 ? 'orange' : 'gray'">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/>
              <line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
          </div>
          <div class="approval-body">
            <span class="approval-count">{{ stats.pending_leave || 0 }}</span>
            <span class="approval-label">Leave Requests Pending</span>
          </div>
          <span v-if="stats.pending_leave > 0" class="approval-arrow">→</span>
        </router-link>

        <router-link to="/approvals/documents" class="approval-card" :class="stats.pending_documents > 0 ? 'approval-card--active' : ''">
          <div class="approval-icon" :class="stats.pending_documents > 0 ? 'orange' : 'gray'">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
            </svg>
          </div>
          <div class="approval-body">
            <span class="approval-count">{{ stats.pending_documents || 0 }}</span>
            <span class="approval-label">Documents Pending</span>
          </div>
          <span v-if="stats.pending_documents > 0" class="approval-arrow">→</span>
        </router-link>

        <router-link to="/approvals/banking" class="approval-card" :class="stats.pending_banking > 0 ? 'approval-card--active' : ''">
          <div class="approval-icon" :class="stats.pending_banking > 0 ? 'orange' : 'gray'">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/>
            </svg>
          </div>
          <div class="approval-body">
            <span class="approval-count">{{ stats.pending_banking || 0 }}</span>
            <span class="approval-label">Banking Changes Pending</span>
          </div>
          <span v-if="stats.pending_banking > 0" class="approval-arrow">→</span>
        </router-link>
      </div>

      <!-- Quick Actions -->
      <div class="quick-actions">
        <h2 class="section-title">Quick Actions</h2>
        <div class="actions-row">
          <router-link to="/payroll" class="action-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <path d="M12 5v14M5 12h14"/>
            </svg>
            Single Payslip
          </router-link>
          <router-link to="/payroll/bulk" v-if="hasRole(['super_admin','accountant'])" class="action-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/>
            </svg>
            Run Bulk Payroll
          </router-link>
          <router-link to="/companies" class="action-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <path d="M3 21h18M3 7l9-4 9 4M4 7v14M20 7v14M9 21v-4a3 3 0 016 0v4"/>
            </svg>
            Manage Companies
          </router-link>
          <router-link to="/hr-reports" v-if="hasRole(['super_admin','accountant'])" class="action-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6m4 0h14M13 19v-10a2 2 0 00-2-2H9"/>
            </svg>
            HR Reports
          </router-link>
        </div>
      </div>

      <!-- Two-column: Alerts + Recent Activity -->
      <div class="two-col">

        <!-- Alerts -->
        <div class="card">
          <h2 class="section-title">
            <svg class="title-icon warn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            Alerts ({{ stats.alerts?.length || 0 }})
          </h2>
          <div v-if="!stats.alerts?.length" class="empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="empty-icon">
              <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
            <span>All employees have complete records.</span>
          </div>
          <ul v-else class="alert-list">
            <li v-for="(alert, i) in stats.alerts" :key="i" class="alert-item">
              <div class="alert-name">{{ alert.employee_name }}</div>
              <div class="alert-missing">Missing: {{ alert.missing.join(', ') }}</div>
            </li>
          </ul>
        </div>

        <!-- Recent Activity -->
        <div class="card" v-if="hasRole(['super_admin','accountant'])">
          <h2 class="section-title">
            <svg class="title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
            </svg>
            Recent Activity
          </h2>
          <div v-if="!stats.recent_activity?.length" class="empty-state">
            <span>No recent activity.</span>
          </div>
          <ul v-else class="activity-list">
            <li v-for="event in stats.recent_activity" :key="event.id" class="activity-item">
              <span class="activity-badge" :class="actionClass(event.action)">{{ actionLabel(event.action) }}</span>
              <div class="activity-meta">
                <span class="activity-user">{{ event.user_name || 'System' }}</span>
                <span class="activity-time">{{ fmtTime(event.timestamp) }}</span>
              </div>
            </li>
          </ul>
          <router-link to="/audit" class="view-all-link">View full audit log →</router-link>
        </div>

      </div>
    </template>

  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

export default {
  name: 'DashboardView',
  setup() {
    const auth = useAuthStore()
    const stats = ref({})
    const loading = ref(true)

    const hasRole = (roles) => auth.roles?.some(r => roles.includes(r))

    const firstName = computed(() => auth.user?.first_name || auth.user?.email?.split('@')[0] || 'there')

    const greeting = computed(() => {
      const h = new Date().getHours()
      if (h < 12) return 'Good morning'
      if (h < 17) return 'Good afternoon'
      return 'Good evening'
    })

    const fmtMoney = (n) => Number(n || 0).toLocaleString('en-ZA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

    const fmtTime = (iso) => {
      if (!iso) return ''
      const d = new Date(iso)
      return d.toLocaleString('en-ZA', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
    }

    const actionLabel = (action) => {
      const map = {
        'user.login': 'Login', 'employee.create': 'New Employee', 'employee.update': 'Employee Edit',
        'employee.delete': 'Deleted', 'employee.import': 'CSV Import',
        'payroll.bulk_run': 'Bulk Payroll', 'payroll.submit': 'Submitted', 'payroll.approve': 'Approved',
        'payroll.reject': 'Rejected'
      }
      return map[action] || action
    }

    const actionClass = (action) => {
      if (action.includes('delete') || action.includes('reject')) return 'badge-red'
      if (action.includes('approve')) return 'badge-green'
      if (action.includes('payroll')) return 'badge-blue'
      return 'badge-gray'
    }

    const load = async () => {
      loading.value = true
      try {
        const { data } = await axios.get('/dashboard/stats')
        stats.value = data
      } catch {}
      loading.value = false
    }

    onMounted(load)

    return { stats, loading, hasRole, firstName, greeting, fmtMoney, fmtTime, actionLabel, actionClass }
  }
}
</script>

<style scoped>
.dashboard-content {
  padding: 24px;
  max-width: 1100px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Header */
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-title { font-size: 18px; font-weight: 600; color: var(--color-text-base); margin: 0 0 4px; }
.page-sub { font-size: 12.5px; color: var(--color-text-muted); margin: 0; }
.header-actions { display: flex; gap: 10px; }

/* Loading */
.loading-row { display: flex; align-items: center; gap: 10px; color: var(--color-text-muted); font-size: 13px; }
.spinner { width: 18px; height: 18px; border: 2px solid var(--color-border); border-top-color: var(--color-accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Stats grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 16px;
  display: flex;
  align-items: flex-start;
  gap: 14px;
}
.stat-card.card-warn { border-color: #fde68a; background: #fffbeb; }

.stat-icon {
  width: 40px; height: 40px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.stat-icon svg { width: 20px; height: 20px; }
.stat-icon.blue { background: #eff6ff; color: #3b82f6; }
.stat-icon.green { background: #f0fdf4; color: #22c55e; }
.stat-icon.purple { background: #f5f3ff; color: #8b5cf6; }
.stat-icon.orange { background: #fff7ed; color: #f59e0b; }
.stat-icon.gray { background: var(--color-bg-page); color: var(--color-text-muted); }

.stat-body { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.stat-val { font-size: 22px; font-weight: 700; color: var(--color-text-base); line-height: 1.1; }
.stat-label { font-size: 11.5px; color: var(--color-text-muted); }
.stat-sub { font-size: 11px; color: var(--color-text-muted); opacity: 0.75; }
.stat-action { font-size: 11.5px; color: var(--color-accent); text-decoration: none; margin-top: 2px; }
.stat-action:hover { text-decoration: underline; }

/* Quick actions */
.quick-actions { display: flex; flex-direction: column; gap: 10px; }
.section-title {
  font-size: 12px; font-weight: 600; color: var(--color-text-muted);
  text-transform: uppercase; letter-spacing: 0.05em;
  display: flex; align-items: center; gap: 6px; margin: 0 0 12px;
}
.title-icon { width: 14px; height: 14px; flex-shrink: 0; }
.warn-icon { color: #f59e0b; }

.actions-row { display: flex; gap: 10px; flex-wrap: wrap; }
.action-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 16px; background: var(--color-bg-card);
  border: 1px solid var(--color-border); border-radius: 8px;
  font-size: 13px; font-weight: 500; color: var(--color-text-base);
  text-decoration: none; transition: border-color 0.12s, background 0.12s;
  white-space: nowrap;
}
.action-btn svg { width: 16px; height: 16px; flex-shrink: 0; color: var(--color-accent); }
.action-btn:hover { border-color: var(--color-accent); background: #eff6ff; }

/* Two column */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.card { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 10px; padding: 20px; }

/* Alerts */
.empty-state { display: flex; align-items: center; gap: 8px; color: var(--color-text-muted); font-size: 13px; }
.empty-icon { width: 18px; height: 18px; color: #22c55e; flex-shrink: 0; }
.alert-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.alert-item { padding: 10px 12px; background: #fffbeb; border: 1px solid #fde68a; border-radius: 7px; }
.alert-name { font-size: 13px; font-weight: 500; color: var(--color-text-base); }
.alert-missing { font-size: 11.5px; color: #92400e; margin-top: 2px; }

/* Activity */
.activity-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; }
.activity-item { display: flex; align-items: center; gap: 10px; padding: 6px 0; border-bottom: 1px solid var(--color-border); }
.activity-item:last-child { border-bottom: none; }
.activity-badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; white-space: nowrap; flex-shrink: 0; }
.badge-blue { background: #dbeafe; color: #1d4ed8; }
.badge-green { background: #dcfce7; color: #15803d; }
.badge-red { background: #fee2e2; color: #b91c1c; }
.badge-gray { background: var(--color-bg-page); color: var(--color-text-muted); }
.activity-meta { display: flex; flex-direction: column; min-width: 0; flex: 1; }
.activity-user { font-size: 12.5px; color: var(--color-text-base); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.activity-time { font-size: 11px; color: var(--color-text-muted); }
.view-all-link { display: block; text-align: center; font-size: 12px; color: var(--color-accent); text-decoration: none; margin-top: 12px; }
.view-all-link:hover { text-decoration: underline; }

/* Approval queue cards */
.approvals-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.approval-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  text-decoration: none;
  transition: border-color 0.12s, box-shadow 0.12s;
}
.approval-card:hover { border-color: var(--color-accent); box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.approval-card--active { border-color: #fde68a; background: #fffbeb; }
.approval-card--active:hover { border-color: #f59e0b; }

.approval-icon {
  width: 40px; height: 40px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.approval-icon svg { width: 20px; height: 20px; }
.approval-icon.orange { background: #fff7ed; color: #f59e0b; }
.approval-icon.gray { background: var(--color-bg-page); color: var(--color-text-muted); }

.approval-body { display: flex; flex-direction: column; gap: 2px; flex: 1; min-width: 0; }
.approval-count { font-size: 22px; font-weight: 700; color: var(--color-text-base); line-height: 1.1; }
.approval-label { font-size: 11.5px; color: var(--color-text-muted); }
.approval-arrow { font-size: 16px; color: var(--color-accent); flex-shrink: 0; }

@media (max-width: 900px) {
  .stats-grid { grid-template-columns: 1fr 1fr; }
  .approvals-grid { grid-template-columns: 1fr 1fr; }
  .two-col { grid-template-columns: 1fr; }
}
@media (max-width: 540px) {
  .stats-grid { grid-template-columns: 1fr; }
  .approvals-grid { grid-template-columns: 1fr; }
  .actions-row { flex-direction: column; }
}
</style>
