<template>
  <header class="app-topbar">
    <div class="topbar-left">
      <button class="topbar-toggle" @click="$emit('toggle-sidebar')" title="Toggle sidebar">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
      </button>
      <nav class="topbar-breadcrumb">
        <template v-for="(crumb, i) in breadcrumbs" :key="i">
          <span class="bc-sep" v-if="i > 0">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="9 18 15 12 9 6"/></svg>
          </span>
          <router-link v-if="crumb.to && i < breadcrumbs.length - 1" :to="crumb.to" class="bc-link">{{ crumb.label }}</router-link>
          <span v-else class="bc-current">{{ crumb.label }}</span>
        </template>
      </nav>
    </div>

    <div class="topbar-right">
      <div class="topbar-user-wrap" ref="userMenuRef">
        <button class="topbar-user" @click="userMenuOpen = !userMenuOpen">
          <div class="topbar-avatar">{{ initials }}</div>
          <span class="topbar-username">{{ fullName }}</span>
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" style="color:var(--color-text-muted)">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </button>

        <Transition name="dropdown-fade">
          <div v-if="userMenuOpen" class="topbar-dropdown">
            <div class="dd-header">
              <div class="dd-name">{{ fullName }}</div>
              <div class="dd-role">{{ formattedRole }}</div>
            </div>
            <div class="dd-divider"/>
            <button class="dd-item danger" @click="logout">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
              </svg>
              Sign out
            </button>
          </div>
        </Transition>
      </div>
    </div>
  </header>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const LABELS = {
  '/': 'Dashboard',
  '/payroll': 'Payroll',
  '/payroll/bulk': 'Bulk Payroll',
  '/companies': 'Companies',
  '/hr-reports': 'HR Reports',
  '/admin/assignments': 'Admin',
  '/audit': 'Audit Log',
  '/reports': 'Reports',
  '/portal': 'My Portal',
  '/leave': 'Leave',
  '/compliance': 'Compliance',
}

export default {
  name: 'AppTopBar',
  props: { collapsed: { type: Boolean, default: false } },
  emits: ['toggle-sidebar'],
  setup() {
    const route = useRoute()
    const auth = useAuthStore()
    const userMenuOpen = ref(false)
    const userMenuRef = ref(null)

    const breadcrumbs = computed(() => {
      const p = route.path
      if (p === '/') return [{ label: 'Dashboard' }]
      if (/^\/companies\/\d+\/employees/.test(p)) {
        return [{ label: 'Companies', to: '/companies' }, { label: 'Employees' }]
      }
      if (LABELS[p]) return [{ label: LABELS[p] }]
      return [{ label: p.split('/').filter(Boolean).map(s => s.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())).join(' / ') }]
    })

    const initials = computed(() => {
      const u = auth.user
      return u ? ((u.first_name?.[0] || '') + (u.last_name?.[0] || '')).toUpperCase() || '?' : '?'
    })
    const fullName = computed(() => {
      const u = auth.user
      return u ? `${u.first_name || ''} ${u.last_name || ''}`.trim() : ''
    })
    const formattedRole = computed(() => {
      const r = auth.roles?.[0]
      return r ? r.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : ''
    })

    const logout = () => { auth.clear(); window.location.href = '/login' }

    const handleClickOutside = (e) => {
      if (userMenuRef.value && !userMenuRef.value.contains(e.target)) userMenuOpen.value = false
    }
    onMounted(() => document.addEventListener('mousedown', handleClickOutside))
    onUnmounted(() => document.removeEventListener('mousedown', handleClickOutside))

    return { breadcrumbs, initials, fullName, formattedRole, logout, userMenuOpen, userMenuRef }
  }
}
</script>

<style scoped>
.app-topbar {
  height: 52px;
  background: var(--color-bg-card);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px 0 10px;
  position: sticky;
  top: 0;
  z-index: 80;
  gap: 12px;
  flex-shrink: 0;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.topbar-toggle {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: none;
  border-radius: 6px;
  color: var(--color-text-muted);
  cursor: pointer;
  flex-shrink: 0;
}
.topbar-toggle:hover { background: var(--color-bg-page); color: var(--color-text-base); }

.topbar-breadcrumb {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  min-width: 0;
}
.bc-sep { display: flex; align-items: center; color: var(--color-text-muted); opacity: 0.4; }
.bc-link { color: var(--color-text-muted); text-decoration: none; }
.bc-link:hover { color: var(--color-accent); }
.bc-current { color: var(--color-text-base); font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.topbar-right {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.topbar-user-wrap { position: relative; }

.topbar-user {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 4px 8px 4px 4px;
  border-radius: 8px;
  cursor: pointer;
  border: 1px solid transparent;
  background: none;
  font-family: inherit;
}
.topbar-user:hover { background: var(--color-bg-page); border-color: var(--color-border); }

.topbar-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, #475569 0%, #1e3a8a 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10.5px;
  font-weight: 600;
  color: #fff;
  flex-shrink: 0;
}

.topbar-username {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-base);
  white-space: nowrap;
}

.topbar-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  box-shadow: 0 8px 28px rgba(0,0,0,0.13);
  min-width: 190px;
  z-index: 300;
  overflow: hidden;
}
.dd-header { padding: 12px 14px 10px; }
.dd-name { font-size: 13px; font-weight: 600; color: var(--color-text-base); }
.dd-role { font-size: 11.5px; color: var(--color-text-muted); margin-top: 2px; }
.dd-divider { height: 1px; background: var(--color-border); }
.dd-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 14px;
  font-size: 13px;
  font-family: inherit;
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
}
.dd-item:hover { background: var(--color-bg-page); }
.dd-item.danger { color: var(--color-error); }
.dd-item.danger:hover { background: var(--color-error-bg); }

.dropdown-fade-enter-active { transition: opacity 0.12s, transform 0.12s; }
.dropdown-fade-leave-active { transition: opacity 0.1s, transform 0.1s; }
.dropdown-fade-enter-from, .dropdown-fade-leave-to { opacity: 0; transform: translateY(-4px); }

@media (max-width: 768px) {
  .app-topbar { display: none; }
}
</style>
