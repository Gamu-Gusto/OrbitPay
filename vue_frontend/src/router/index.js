import { createRouter, createWebHistory } from 'vue-router'
import CompaniesView from '../views/CompaniesView.vue'
import EmployeesView from '../views/EmployeesView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import AdminAssignmentsView from '../views/AdminAssignmentsView.vue'
import { useAuthStore } from '../stores/auth'

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
      path: '/register',
      name: 'register',
      component: RegisterView
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
    }
  ]
})

router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()

  if (auth.accessToken && !auth.isAuthenticated) {
    await auth.initializeAuth()
  }

  const publicRoutes = ['/login', '/register', '/payslip']

  if (publicRoutes.includes(to.path)) {
    auth.isAuthenticated ? next('/') : next()
  } else {
    if (!auth.isAuthenticated) {
      next('/login')
      return
    }
    // Redirect pure-employee users away from admin-oriented pages
    const isEmployeeOnly = auth.roles.includes('employee') &&
      !auth.roles.some(r => ['super_admin', 'accountant'].includes(r))
    if (isEmployeeOnly && to.path === '/') {
      next('/portal')
      return
    }

    const requiredPermission = to.meta?.permission
    if (requiredPermission && !auth.hasPermission(requiredPermission)) {
      next(isEmployeeOnly ? '/portal' : '/')
      return
    }
    next()
  }
})

export default router
