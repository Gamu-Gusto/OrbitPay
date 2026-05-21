<template>
  <aside class="app-sidebar" :class="{ 'is-open': isOpen, 'is-collapsed': isCollapsed }">

    <!-- Brand -->
    <div class="sidebar-brand" :title="isCollapsed ? 'OrbitPay' : ''">
      <img src="/OrbitPayfinal.jpeg" alt="OrbitPay" class="brand-logo-img" :class="{ 'collapsed': isCollapsed }" />
    </div>

    <!-- Mobile close -->
    <button class="sidebar-mobile-close" @click="$emit('close')" aria-label="Close menu">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
    </button>

    <!-- Navigation -->
    <nav class="sidebar-nav">
      <span class="nav-section-label">Main Menu</span>

      <router-link to="/" class="nav-link" :class="{ 'is-active': isDashboard }" @click="$emit('close')" data-label="Dashboard">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
          <rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/>
        </svg>
        <span>Dashboard</span>
      </router-link>

      <router-link to="/payroll" class="nav-link" :class="{ 'is-active': isPayroll }" @click="$emit('close')" data-label="Payroll">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <rect x="2" y="3" width="8" height="10" rx="1"/><rect x="14" y="3" width="8" height="6" rx="1"/>
          <rect x="14" y="13" width="8" height="8" rx="1"/><rect x="2" y="17" width="8" height="4" rx="1"/>
        </svg>
        <span>Payroll</span>
      </router-link>

      <router-link
        v-if="auth.hasPermission('RUN_PAYROLL')"
        to="/payroll/bulk"
        class="nav-link"
        :class="{ 'is-active': isBulk }"
        @click="$emit('close')"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
          <circle cx="9" cy="7" r="4"/>
          <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/>
        </svg>
        <span>Bulk Payroll</span>
      </router-link>

      <router-link to="/companies" class="nav-link" :class="{ 'is-active': isCompanies }" @click="$emit('close')" data-label="Companies">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M3 21h18M3 7l9-4 9 4M4 7v14M20 7v14M9 21v-4a3 3 0 016 0v4"/>
        </svg>
        <span>Companies</span>
      </router-link>

      <router-link
        v-if="auth.hasPermission('VIEW_HR_REPORTS')"
        to="/hr-reports"
        class="nav-link"
        :class="{ 'is-active': isHR }"
        @click="$emit('close')"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6m4 0h14M13 19v-10a2 2 0 00-2-2H9"/>
          <path d="M17 19V9a2 2 0 00-2-2h-2"/>
        </svg>
        <span>HR Reports</span>
      </router-link>

      <router-link
        v-if="auth.hasPermission('MANAGE_ASSIGNMENTS')"
        to="/admin/assignments"
        class="nav-link"
        :class="{ 'is-active': isAdmin }"
        @click="$emit('close')"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
          <path d="M18 14l2 2 4-4" stroke-linecap="round"/>
        </svg>
        <span>Admin</span>
      </router-link>

      <span v-if="auth.hasPermission('APPROVE_LEAVE')" class="nav-section-label" style="margin-top:8px">Approvals</span>

      <router-link
        v-if="auth.hasPermission('APPROVE_LEAVE')"
        to="/approvals/leave"
        class="nav-link"
        :class="{ 'is-active': isLeaveApprovals }"
        @click="$emit('close')"
        data-label="Leave Approvals"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/>
          <line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
          <path d="M9 16l2 2 4-4"/>
        </svg>
        <span>Leave Approvals</span>
        <span v-if="pendingCounts.leave > 0" class="nav-badge">{{ pendingCounts.leave }}</span>
      </router-link>

      <router-link
        v-if="auth.hasPermission('REVIEW_DOCUMENTS')"
        to="/approvals/documents"
        class="nav-link"
        :class="{ 'is-active': isDocApprovals }"
        @click="$emit('close')"
        data-label="Document Approvals"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
          <path d="M9 15l2 2 4-4"/>
        </svg>
        <span>Doc Approvals</span>
        <span v-if="pendingCounts.documents > 0" class="nav-badge">{{ pendingCounts.documents }}</span>
      </router-link>

      <router-link
        v-if="auth.hasPermission('APPROVE_BANKING')"
        to="/approvals/banking"
        class="nav-link"
        :class="{ 'is-active': isBankApprovals }"
        @click="$emit('close')"
        data-label="Banking Approvals"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M3 21h18M3 10h18M5 21V10M19 21V10M12 6l9 4H3l9-4z"/>
        </svg>
        <span>Banking Approvals</span>
        <span v-if="pendingCounts.banking > 0" class="nav-badge">{{ pendingCounts.banking }}</span>
      </router-link>

      <router-link
        v-if="auth.hasPermission('VIEW_AUDIT_LOGS')"
        to="/audit"
        class="nav-link"
        :class="{ 'is-active': isAudit }"
        @click="$emit('close')"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/>
          <polyline points="10 9 9 9 8 9"/>
        </svg>
        <span>Audit Log</span>
      </router-link>

      <router-link
        v-if="auth.hasPermission('VIEW_PAYROLL_REPORTS')"
        to="/reports"
        class="nav-link"
        :class="{ 'is-active': isReports }"
        @click="$emit('close')"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/>
          <line x1="6" y1="20" x2="6" y2="14"/>
        </svg>
        <span>Reports</span>
      </router-link>

      <router-link
        v-if="auth.hasPermission('VIEW_OWN_PAYSLIPS')"
        to="/portal"
        class="nav-link"
        :class="{ 'is-active': isPortal }"
        @click="$emit('close')"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
        </svg>
        <span>My Portal</span>
      </router-link>

      <router-link
        to="/leave"
        class="nav-link"
        :class="{ 'is-active': isLeave }"
        @click="$emit('close')"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/>
          <line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
          <path d="M8 14l2 2 4-4"/>
        </svg>
        <span>Leave</span>
      </router-link>

      <router-link
        v-if="auth.hasPermission('VIEW_PAYROLL_REPORTS')"
        to="/compliance"
        class="nav-link"
        :class="{ 'is-active': isCompliance }"
        @click="$emit('close')"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M12 2L3 7v6c0 5.25 3.75 10.15 9 11.35C17.25 23.15 21 18.25 21 13V7L12 2z"/>
          <polyline points="9 12 11 14 15 10"/>
        </svg>
        <span>Compliance</span>
      </router-link>
    </nav>

    <!-- Collapse toggle -->
    <button class="sidebar-collapse-btn" @click="$emit('toggle-collapse')" :title="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
        <polyline v-if="isCollapsed" points="9 18 15 12 9 6"/>
        <polyline v-else points="15 18 9 12 15 6"/>
      </svg>
    </button>

    <!-- User footer -->
    <div class="sidebar-user">
      <div class="user-avatar">{{ initials }}</div>
      <div class="user-details">
        <span class="user-name">{{ fullName }}</span>
        <span class="user-role">{{ formattedRole }}</span>
      </div>
      <button class="logout-btn" @click="logout" title="Sign out">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
        </svg>
      </button>
    </div>

  </aside>
</template>

<script>
import { computed, reactive, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import axios from 'axios'

export default {
  name: 'AppPrimaryNav',
  props: {
    isOpen: { type: Boolean, default: false },
    isCollapsed: { type: Boolean, default: false }
  },
  emits: ['close', 'toggle-collapse'],
  setup() {
    const route = useRoute()
    const auth  = useAuthStore()

    const isDashboard    = computed(() => route.path === '/')
    const isPayroll      = computed(() => route.path === '/payroll')
    const isBulk         = computed(() => route.path === '/payroll/bulk')
    const isCompanies    = computed(() => route.path.startsWith('/companies'))
    const isHR           = computed(() => route.path.startsWith('/hr-reports'))
    const isAdmin        = computed(() => route.path.startsWith('/admin'))
    const isAudit        = computed(() => route.path === '/audit')
    const isReports      = computed(() => route.path === '/reports')
    const isPortal       = computed(() => route.path === '/portal')
    const isLeave        = computed(() => route.path === '/leave')
    const isCompliance   = computed(() => route.path === '/compliance')
    const isLeaveApprovals = computed(() => route.path === '/approvals/leave')
    const isDocApprovals   = computed(() => route.path === '/approvals/documents')
    const isBankApprovals  = computed(() => route.path === '/approvals/banking')

    const pendingCounts = reactive({ leave: 0, documents: 0, banking: 0 })

    const fetchPendingCounts = async () => {
      if (!auth.hasPermission('APPROVE_LEAVE')) return
      try {
        const { data } = await axios.get('/dashboard/stats')
        pendingCounts.leave     = data.pending_leave     || 0
        pendingCounts.documents = data.pending_documents || 0
        pendingCounts.banking   = data.pending_banking   || 0
      } catch {}
    }

    let interval = null
    onMounted(() => {
      fetchPendingCounts()
      interval = setInterval(fetchPendingCounts, 300000)
    })
    onUnmounted(() => clearInterval(interval))

    const initials = computed(() => {
      const u = auth.user
      if (!u) return '?'
      return ((u.first_name?.[0] || '') + (u.last_name?.[0] || '')).toUpperCase() || '?'
    })

    const fullName = computed(() => {
      const u = auth.user
      if (!u) return ''
      return `${u.first_name || ''} ${u.last_name || ''}`.trim()
    })

    const formattedRole = computed(() => {
      const roles = auth.roles
      if (!roles?.length) return ''
      return roles[0].replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
    })

    const logout = () => { auth.logout() }

    return { auth, isDashboard, isPayroll, isBulk, isCompanies, isHR, isAdmin, isAudit, isReports, isPortal, isLeave, isCompliance, isLeaveApprovals, isDocApprovals, isBankApprovals, pendingCounts, initials, fullName, formattedRole, logout }
  }
}
</script>

<style scoped>
/* ── Sidebar shell ────────────────────────────────────────────────────────── */
.app-sidebar {
  width: var(--sidebar-width);
  background: var(--color-bg-sidebar);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 150;
  overflow: hidden;
  transition: width 0.22s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ── Collapsed state ─────────────────────────────────────────────────────── */
.app-sidebar.is-collapsed { width: 60px; }

.app-sidebar.is-collapsed .nav-section-label,
.app-sidebar.is-collapsed .nav-link span,
.app-sidebar.is-collapsed .user-details,
.app-sidebar.is-collapsed .logout-btn {
  display: none;
}

.app-sidebar.is-collapsed .nav-link { justify-content: center; padding: 9px; gap: 0; }
.app-sidebar.is-collapsed .nav-link.is-active::before { display: none; }
.app-sidebar.is-collapsed .sidebar-user { justify-content: center; padding: 12px 0 16px; gap: 0; }
.app-sidebar.is-collapsed .sidebar-collapse-btn { justify-content: center; margin: 0 auto; }
.app-sidebar.is-collapsed .nav-icon { opacity: 1; }

.app-sidebar.is-collapsed .nav-link:hover::after {
  content: attr(data-label);
  position: absolute;
  left: 64px;
  background: #1e293b;
  color: #fff;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 6px;
  white-space: nowrap;
  pointer-events: none;
  z-index: 200;
  box-shadow: 0 4px 12px rgba(0,0,0,0.25);
}

/* ── Brand ───────────────────────────────────────────────────────────────── */
.sidebar-brand {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 16px 16px 14px;
  border-bottom: 1px solid rgba(255,255,255,0.07);
  flex-shrink: 0;
}

.app-sidebar.is-collapsed .sidebar-brand {
  justify-content: center;
  padding: 14px 0;
}

.brand-logo-img {
  height: 52px;
  width: auto;
  max-width: 180px;
  object-fit: contain;
  display: block;
  border-radius: 6px;
  transition: max-width 0.22s, height 0.22s;
}

.brand-logo-img.collapsed {
  height: 40px;
  max-width: 44px;
}

/* ── Mobile close button ─────────────────────────────────────────────────── */
.sidebar-mobile-close {
  display: none;
  position: absolute;
  top: 14px;
  right: 12px;
  width: 30px;
  height: 30px;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  border: none;
  background: rgba(255,255,255,0.1);
  color: rgba(255,255,255,0.7);
  cursor: pointer;
}
.sidebar-mobile-close:hover { background: rgba(255,255,255,0.18); }

/* ── Navigation ──────────────────────────────────────────────────────────── */
.sidebar-nav {
  display: flex;
  flex-direction: column;
  padding: 12px 8px;
  gap: 2px;
  overflow-y: auto;
  flex: 1;
}

.nav-section-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.06em;
  color: var(--color-text-sidebar-muted);
  text-transform: uppercase;
  padding: 4px 8px 8px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border-radius: 7px;
  font-size: 13.5px;
  font-weight: 450;
  color: var(--color-text-sidebar);
  text-decoration: none;
  transition: background 0.12s, color 0.12s;
  position: relative;
}

.nav-link:hover {
  background: var(--color-bg-sidebar-hover);
  color: #fff;
}

.nav-link.is-active {
  background: var(--color-bg-sidebar-active);
  color: var(--color-text-sidebar-active);
  font-weight: 500;
}

.nav-link.is-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 6px;
  bottom: 6px;
  width: 3px;
  background: #3b82f6;
  border-radius: 0 2px 2px 0;
}

.nav-icon {
  width: 17px;
  height: 17px;
  flex-shrink: 0;
  opacity: 0.85;
}

.nav-link.is-active .nav-icon { opacity: 1; }

.nav-badge {
  margin-left: auto;
  background: #ef4444;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 5px;
  flex-shrink: 0;
}

/* ── Collapse toggle ──────────────────────────────────────────────────────── */
.sidebar-collapse-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 4px 8px;
  padding: 7px 10px;
  border: none;
  background: none;
  border-radius: 6px;
  color: var(--color-text-sidebar-muted);
  cursor: pointer;
  font-size: 12px;
  font-family: inherit;
  transition: background 0.12s, color 0.12s;
  flex-shrink: 0;
}
.sidebar-collapse-btn:hover { background: var(--color-bg-sidebar-hover); color: rgba(255,255,255,0.8); }

/* ── User footer ─────────────────────────────────────────────────────────── */
.sidebar-user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 12px 16px;
  border-top: 1px solid rgba(255,255,255,0.07);
  flex-shrink: 0;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #475569 0%, #334155 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  flex-shrink: 0;
}

.user-details {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.user-name {
  font-size: 12.5px;
  font-weight: 500;
  color: rgba(255,255,255,0.9);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}

.user-role {
  font-size: 10.5px;
  color: var(--color-text-sidebar-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}

.logout-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: rgba(255,255,255,0.45);
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.12s, color 0.12s;
}
.logout-btn:hover { background: rgba(255,255,255,0.1); color: rgba(255,255,255,0.9); }

/* ── Mobile responsive ───────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .app-sidebar {
    transform: translateX(-100%);
    transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    width: 260px;
  }
  .app-sidebar.is-open {
    transform: translateX(0);
    box-shadow: 4px 0 24px rgba(0,0,0,0.35);
  }
  .sidebar-mobile-close {
    display: flex;
  }
}
</style>
