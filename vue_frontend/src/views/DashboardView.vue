<template>
  <div class="dashboard">

    <!-- Page header -->
    <div class="dashboard-header">
      <div>
        <h1 class="page-title">Dashboard</h1>
        <p class="page-subtitle">{{ greeting }}, {{ firstName }}. Here's what needs your attention.</p>
      </div>
      <router-link
        v-if="hasRole(['super_admin', 'accountant'])"
        to="/payroll/bulk"
        class="btn btn-primary"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/>
          <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/>
        </svg>
        Run Payroll
      </router-link>
    </div>

    <!-- Skeleton while loading -->
    <SkeletonDashboard v-if="loading" />

    <template v-else>

      <!-- ── Stat cards ─────────────────────────────────────── -->
      <div class="stats-grid">

        <!-- Companies -->
        <div class="stat-card">
          <div class="stat-value">{{ stats.companies ?? '—' }}</div>
          <div class="stat-label">
            {{ stats.companies === 1 ? 'Company' : 'Companies' }}
          </div>
        </div>

        <!-- Active employees -->
        <div class="stat-card">
          <div class="stat-value">{{ stats.employees?.active ?? '—' }}</div>
          <div class="stat-label">Active Employees</div>
          <div class="stat-sub">{{ stats.employees?.inactive ?? 0 }} inactive</div>
        </div>

        <!-- Payroll net pay -->
        <div class="stat-card">
          <div class="stat-value">R {{ fmtMoney(stats.current_month?.total_net_pay) }}</div>
          <div class="stat-label">{{ stats.current_month?.period || 'This Month' }} Net Payroll</div>
          <div class="stat-sub">{{ stats.current_month?.employees_processed ?? 0 }} employees processed</div>
        </div>

        <!-- Pending approvals — warning accent when > 0 -->
        <div class="stat-card" :class="{ 'stat-card--warn': stats.pending_approvals > 0 }">
          <div class="stat-value">{{ stats.pending_approvals ?? 0 }}</div>
          <div class="stat-label">Pending Approvals</div>
          <router-link
            v-if="stats.pending_approvals > 0"
            to="/payroll/bulk"
            class="stat-link"
          >Review &rarr;</router-link>
        </div>

      </div>

      <!-- ── Approval queue (super_admin only) ──────────────── -->
      <div v-if="hasRole(['super_admin'])" class="approvals-grid">

        <router-link
          to="/approvals/leave"
          class="approval-cell"
          :class="{ 'approval-cell--active': stats.pending_leave > 0 }"
        >
          <div class="approval-cell-body">
            <span class="approval-count">{{ stats.pending_leave || 0 }}</span>
            <span class="approval-label">Leave Requests</span>
          </div>
          <svg v-if="stats.pending_leave > 0" class="approval-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </router-link>

        <router-link
          to="/approvals/documents"
          class="approval-cell"
          :class="{ 'approval-cell--active': stats.pending_documents > 0 }"
        >
          <div class="approval-cell-body">
            <span class="approval-count">{{ stats.pending_documents || 0 }}</span>
            <span class="approval-label">Documents Pending</span>
          </div>
          <svg v-if="stats.pending_documents > 0" class="approval-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </router-link>

        <router-link
          to="/approvals/banking"
          class="approval-cell"
          :class="{ 'approval-cell--active': stats.pending_banking > 0 }"
        >
          <div class="approval-cell-body">
            <span class="approval-count">{{ stats.pending_banking || 0 }}</span>
            <span class="approval-label">Banking Changes</span>
          </div>
          <svg v-if="stats.pending_banking > 0" class="approval-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </router-link>

      </div>

      <!-- ── Quick actions ───────────────────────────────────── -->
      <div>
        <p class="section-label" style="margin-bottom: var(--space-3);">Quick Actions</p>
        <div class="actions-row">

          <router-link to="/payroll" class="btn btn-secondary">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="color: var(--color-text-muted);">
              <rect x="2" y="3" width="8" height="10" rx="1"/><rect x="14" y="3" width="8" height="6" rx="1"/>
              <rect x="14" y="13" width="8" height="8" rx="1"/><rect x="2" y="17" width="8" height="4" rx="1"/>
            </svg>
            Single Payslip
          </router-link>

          <router-link
            v-if="hasRole(['super_admin', 'accountant'])"
            to="/payroll/bulk"
            class="btn btn-secondary"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="color: var(--color-text-muted);">
              <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/>
            </svg>
            Run Bulk Payroll
          </router-link>

          <router-link to="/companies" class="btn btn-secondary">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="color: var(--color-text-muted);">
              <path d="M3 21h18M3 7l9-4 9 4M4 7v14M20 7v14M9 21v-4a3 3 0 016 0v4"/>
            </svg>
            Manage Companies
          </router-link>

          <router-link
            v-if="hasRole(['super_admin', 'accountant'])"
            to="/hr-reports"
            class="btn btn-secondary"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="color: var(--color-text-muted);">
              <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6m4 0h14M13 19v-10a2 2 0 00-2-2H9"/>
            </svg>
            HR Reports
          </router-link>

        </div>
      </div>

      <!-- ── Recent document uploads ────────────────────────── -->
      <div
        v-if="hasRole(['super_admin', 'accountant']) && recentDocUploads.length > 0"
        class="card card-sm"
      >
        <div class="doc-card-header">
          <div class="doc-card-title">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="color: var(--color-text-muted); flex-shrink: 0;">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/>
            </svg>
            Recent Document Uploads
          </div>
          <router-link to="/approvals/documents" class="btn-text" style="font-size: var(--text-sm);">
            View all &rarr;
          </router-link>
        </div>

        <ul class="doc-list" role="list">
          <li
            v-for="n in recentDocUploads"
            :key="n.id"
            class="doc-row"
          >
            <div class="doc-row-body">
              <p class="doc-row-msg truncate">{{ n.message }}</p>
              <p class="doc-row-time">{{ fmtTime(n.created_at) }}</p>
            </div>
            <router-link to="/approvals/documents" class="btn-text" style="font-size: var(--text-sm); white-space: nowrap;">
              Review
            </router-link>
          </li>
        </ul>
      </div>

      <!-- ── Two-column: Alerts + Recent Activity ───────────── -->
      <div class="two-col">

        <!-- Alerts -->
        <div class="card card-sm">
          <div class="card-section-heading">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="color: #D97706; flex-shrink: 0;">
              <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            Alerts
            <span class="badge badge-neutral" style="margin-left: 4px;">{{ stats.alerts?.length || 0 }}</span>
          </div>

          <div v-if="!stats.alerts?.length" class="empty-state" style="padding: var(--space-8) var(--space-4);">
            <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true" style="color: var(--color-success);">
              <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
            <p>All employees have complete records.</p>
          </div>

          <ul v-else class="alert-list" role="list">
            <li v-for="(alert, i) in stats.alerts" :key="i" class="alert-item">
              <p class="alert-name">{{ alert.employee_name }}</p>
              <p class="alert-missing">Missing: {{ alert.missing.join(', ') }}</p>
            </li>
          </ul>
        </div>

        <!-- Recent Activity -->
        <div v-if="hasRole(['super_admin', 'accountant'])" class="card card-sm">
          <div class="card-section-heading">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="color: var(--color-text-muted); flex-shrink: 0;">
              <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
            </svg>
            Recent Activity
          </div>

          <div v-if="!stats.recent_activity?.length" class="empty-state" style="padding: var(--space-8) var(--space-4);">
            <p>No recent activity.</p>
          </div>

          <ul v-else class="activity-list" role="list">
            <li v-for="event in stats.recent_activity" :key="event.id" class="activity-item">
              <span class="badge" :class="actionClass(event.action)">{{ actionLabel(event.action) }}</span>
              <div class="activity-meta">
                <span class="activity-user truncate">{{ event.user_name || 'System' }}</span>
                <span class="activity-time">{{ fmtTime(event.timestamp) }}</span>
              </div>
            </li>
          </ul>

          <router-link to="/audit" class="audit-link">View full audit log &rarr;</router-link>
        </div>

      </div>

    </template>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import SkeletonDashboard from '../components/ui/SkeletonDashboard.vue'

export default {
  name: 'DashboardView',
  components: { SkeletonDashboard },
  setup() {
    const auth = useAuthStore()
    const stats = ref({})
    const loading = ref(true)
    const recentDocUploads = ref([])

    const hasRole = (roles) => auth.roles?.some(r => roles.includes(r))

    const firstName = computed(() =>
      auth.user?.first_name || auth.user?.email?.split('@')[0] || 'there'
    )

    const greeting = computed(() => {
      const h = new Date().getHours()
      if (h < 12) return 'Good morning'
      if (h < 17) return 'Good afternoon'
      return 'Good evening'
    })

    const fmtMoney = (n) =>
      Number(n || 0).toLocaleString('en-ZA', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })

    const fmtTime = (iso) => {
      if (!iso) return ''
      return new Date(iso).toLocaleString('en-ZA', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
      })
    }

    const actionLabel = (action) => {
      const map = {
        'user.login':        'Login',
        'employee.create':   'New Employee',
        'employee.update':   'Employee Edit',
        'employee.delete':   'Deleted',
        'employee.import':   'CSV Import',
        'payroll.bulk_run':  'Bulk Payroll',
        'payroll.submit':    'Submitted',
        'payroll.approve':   'Approved',
        'payroll.reject':    'Rejected',
      }
      return map[action] || action
    }

    const actionClass = (action) => {
      if (action.includes('delete') || action.includes('reject')) return 'badge-red'
      if (action.includes('approve'))  return 'badge-green'
      if (action.includes('payroll'))  return 'badge-blue'
      return 'badge-gray'
    }

    const load = async () => {
      loading.value = true
      try {
        const [statsRes, notifRes] = await Promise.allSettled([
          axios.get('/dashboard/stats'),
          axios.get('/notifications'),
        ])
        if (statsRes.status === 'fulfilled') stats.value = statsRes.value.data
        if (notifRes.status === 'fulfilled') {
          recentDocUploads.value = (notifRes.value.data || [])
            .filter(n => n.type === 'DOCUMENT_UPLOADED')
            .slice(0, 5)
        }
      } catch { /* non-fatal — skeleton stays hidden */ }
      loading.value = false
    }

    onMounted(load)

    return {
      stats,
      loading,
      recentDocUploads,
      hasRole,
      firstName,
      greeting,
      fmtMoney,
      fmtTime,
      actionLabel,
      actionClass,
    }
  },
}
</script>

<style scoped>
/* ── Page shell ──────────────────────────────────────────────── */
.dashboard {
  padding: var(--space-6);
  max-width: 1200px;
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

/* ── Header ──────────────────────────────────────────────────── */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-4);
}

/* ── Stat cards grid ─────────────────────────────────────────── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-4);
}

.stat-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: border-color var(--transition-fast);
}

/* Orange left-border accent for pending-approvals card when count > 0 */
.stat-card--warn {
  border-left: 3px solid #F59E0B;
}

.stat-value {
  font-size: 22px;
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1.15;
  letter-spacing: -0.02em;
}

.stat-label {
  font-size: var(--text-sm);
  font-weight: 400;
  color: var(--color-text-muted);
}

.stat-sub {
  font-size: var(--text-xs);
  color: var(--color-text-disabled);
}

.stat-link {
  margin-top: 4px;
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--color-accent);
  text-decoration: none;
}
.stat-link:hover { text-decoration: underline; }

/* ── Approval queue ──────────────────────────────────────────── */
.approvals-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-4);
}

.approval-cell {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  text-decoration: none;
  color: inherit;
  transition: border-color var(--transition-fast), background-color var(--transition-fast);
}
.approval-cell:hover {
  border-color: var(--color-border-strong);
}

.approval-cell--active {
  background: #FFFBEB;
  border-color: #FCD34D;
}
.approval-cell--active:hover {
  border-color: #F59E0B;
}

.approval-cell-body {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 1;
  min-width: 0;
}

.approval-count {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1.2;
  letter-spacing: -0.02em;
}

.approval-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.approval-arrow {
  color: var(--color-text-muted);
  flex-shrink: 0;
}

/* ── Quick actions ───────────────────────────────────────────── */
.actions-row {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}

/* ── Document uploads card ───────────────────────────────────── */
.doc-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.doc-card-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text-primary);
}

.doc-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.doc-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: 10px 0;
  border-bottom: 1px solid var(--color-border);
}
.doc-row:last-child { border-bottom: none; }

.doc-row-body { flex: 1; min-width: 0; }

.doc-row-msg {
  font-size: var(--text-base);
  color: var(--color-text-base);
  margin: 0 0 2px;
}

.doc-row-time {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin: 0;
}

/* ── Alerts + Activity column headings ───────────────────────── */
.card-section-heading {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--space-4);
}

/* ── Alert list ──────────────────────────────────────────────── */
.alert-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.alert-item {
  padding: 10px var(--space-3);
  background: #FFFBEB;
  border: 1px solid #FCD34D;
  border-radius: var(--radius-md);
}

.alert-name {
  font-size: var(--text-base);
  font-weight: 500;
  color: var(--color-text-primary);
  margin: 0 0 2px;
}

.alert-missing {
  font-size: var(--text-xs);
  color: #92400e;
  margin: 0;
}

/* ── Activity list ───────────────────────────────────────────── */
.activity-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 8px 0;
  border-bottom: 1px solid var(--color-border);
}
.activity-item:last-child { border-bottom: none; }

.activity-meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.activity-user {
  font-size: var(--text-base);
  color: var(--color-text-base);
}

.activity-time {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.audit-link {
  display: block;
  text-align: center;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-accent);
  text-decoration: none;
  margin-top: var(--space-4);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border);
}
.audit-link:hover { color: var(--color-accent-hover); }

/* ── Two-column layout ───────────────────────────────────────── */
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-5);
}

/* ── Responsive ──────────────────────────────────────────────── */
@media (max-width: 900px) {
  .stats-grid    { grid-template-columns: 1fr 1fr; }
  .approvals-grid { grid-template-columns: 1fr 1fr; }
  .two-col       { grid-template-columns: 1fr; }
}

@media (max-width: 600px) {
  .dashboard     { padding: var(--space-4); gap: var(--space-4); }
  .stats-grid    { grid-template-columns: 1fr; }
  .approvals-grid { grid-template-columns: 1fr; }
  .actions-row   { flex-direction: column; }
}
</style>
