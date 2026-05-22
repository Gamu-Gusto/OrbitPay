import { createRouter, createWebHistory } from 'vue-router'
import CompaniesView from '../views/CompaniesView.vue'
import EmployeesView from '../views/EmployeesView.vue'
import LoginView from '../views/LoginView.vue'
import AdminAssignmentsView from '../views/AdminAssignmentsView.vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

// Routes that employee-only users are allowed to access
const EMPLOYEE_ALLOWED = ['/portal', '/leave', '/change-password', '/forbidden']

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/payroll',
      name: 'payroll',
      component: () => import('../views/PayrollView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/admin/assignments',
      name: 'adminAssignments',
      component: AdminAssignmentsView,
      meta: { requiresAuth: true, permission: 'MANAGE_ASSIGNMENTS' }
    },
    {
      path: '/companies',
      name: 'companies',
      component: CompaniesView,
      meta: { requiresAuth: true }
    },
    {
      path: '/companies/:companyId/employees',
      name: 'companyEmployees',
      component: EmployeesView,
      meta: { requiresAuth: true }
    },
    {
      path: '/payslip',
      name: 'payslip',
      component: () => import('../components/PayslipTemplate.vue')
    },
    {
      path: '/hr-reports',
      name: 'hrReports',
      component: () => import('../views/HRReportsView.vue'),
      meta: { requiresAuth: true, permission: 'VIEW_HR_REPORTS' }
    },
    {
      path: '/payroll/bulk',
      name: 'bulkPayroll',
      component: () => import('../views/BulkPayrollView.vue'),
      meta: { requiresAuth: true, permission: 'RUN_PAYROLL' }
    },
    {
      path: '/audit',
      name: 'auditLog',
      component: () => import('../views/AuditLogView.vue'),
      meta: { requiresAuth: true, permission: 'VIEW_AUDIT_LOGS' }
    },
    {
      path: '/approvals/leave',
      name: 'leaveApprovals',
      component: () => import('../views/LeaveApprovalsView.vue'),
      meta: { requiresAuth: true, permission: 'APPROVE_LEAVE' }
    },
    {
      path: '/approvals/documents',
      name: 'documentApprovals',
      component: () => import('../views/DocumentApprovalsView.vue'),
      meta: { requiresAuth: true, permission: 'REVIEW_DOCUMENTS' }
    },
    {
      path: '/approvals/banking',
      name: 'bankingApprovals',
      component: () => import('../views/BankingApprovalsView.vue'),
      meta: { requiresAuth: true, permission: 'APPROVE_BANKING' }
    },
    {
      path: '/portal',
      name: 'employeePortal',
      component: () => import('../views/EmployeePortalView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/leave',
      name: 'leave',
      component: () => import('../views/LeaveView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/reports',
      name: 'reports',
      component: () => import('../views/ReportsView.vue'),
      meta: { requiresAuth: true, permission: 'VIEW_PAYROLL_REPORTS' }
    },
    {
      path: '/compliance',
      name: 'compliance',
      component: () => import('../views/ComplianceView.vue'),
      meta: { requiresAuth: true, permission: 'VIEW_PAYROLL_REPORTS' }
    },
    {
      path: '/change-password',
      name: 'changePassword',
      component: () => import('../views/ChangePasswordView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/manager',
      name: 'managerDashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/admin/users',
      name: 'userManagement',
      component: () => import('../views/UserManagementView.vue'),
      meta: { requiresAuth: true, permission: 'CREATE_USER' }
    },
    {
      path: '/admin/announcements',
      name: 'announcements',
      component: () => import('../views/AnnouncementsView.vue'),
      meta: { requiresAuth: true, permission: 'MANAGE_ANNOUNCEMENTS' }
    },
    {
      path: '/admin/setup',
      name: 'adminSetup',
      component: () => import('../views/AdminSetupView.vue'),
    },
    {
      path: '/activate',
      name: 'activate',
      component: () => import('../views/ActivateView.vue'),
    },
    {
      path: '/forbidden',
      name: 'forbidden',
      component: () => import('../views/ForbiddenView.vue'),
    }
  ]
})

router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()

  if (auth.accessToken && !auth.isAuthenticated) {
    await auth.initializeAuth()
  }

  const publicRoutes = ['/login', '/payslip', '/admin/setup', '/activate']

  if (to.path === '/admin/setup') {
    try {
      const { data } = await axios.get('/auth/admin/setup-status')
      if (data.setup_complete) { next('/login'); return }
    } catch {}
    next()
    return
  }

  if (publicRoutes.includes(to.path)) {
    if (auth.isAuthenticated) {
      const roles = auth.roles
      const isEmp = roles.includes('employee') &&
        !roles.some(r => ['super_admin', 'accountant', 'manager'].includes(r))
      next(isEmp ? '/portal' : '/')
    } else {
      next()
    }
    return
  }

  if (!auth.isAuthenticated) {
    next('/login')
    return
  }

  const isEmployeeOnly = auth.roles.includes('employee') &&
    !auth.roles.some(r => ['super_admin', 'accountant', 'manager'].includes(r))

  // Block employees from all admin routes
  if (isEmployeeOnly && !EMPLOYEE_ALLOWED.includes(to.path)) {
    next('/portal')
    return
  }

  // Enforce permission-gated routes
  const requiredPermission = to.meta?.permission
  if (requiredPermission && !auth.hasPermission(requiredPermission)) {
    // User is authenticated but lacks the required permission
    next('/forbidden')
    return
  }

  next()
})

export default router
