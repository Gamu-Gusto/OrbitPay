<template>
  <aside class="app-sidebar">
    <div v-for="section in sidebarSections" :key="section.title" class="sidebar-section">
      <h3 class="section-title">{{ section.title }}</h3>
      <nav class="section-nav">
        <a
          v-for="item in section.items"
          :key="item.id"
          href="#"
          class="nav-link"
          :class="{ active: activeSection === item.id }"
          @click.prevent="$emit('navigate', item.id)"
        >
          <svg v-if="item.icon" class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path v-if="item.icon === 'users'" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
            <path v-else-if="item.icon === 'calendar'" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
            <path v-else-if="item.icon === 'calculator'" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
            <path v-else-if="item.icon === 'document'" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            <path v-else-if="item.icon === 'chart'" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6m4 0h16m-4-6v-6a2 2 0 00-2-2h-4a2 2 0 00-2 2v6"/>
            <path v-else d="M13 10V3L4 14h7v7l9-11h-7z"/>
          </svg>
          <span>{{ item.label }}</span>
        </a>
      </nav>
    </div>
  </aside>
</template>

<script>
export default {
  name: 'AppSidebar',
  props: {
    activeSection: {
      type: String,
      default: 'details'
    }
  },
  emits: ['navigate'],
  setup() {
    const sidebarSections = [
      {
        title: 'Processing',
        items: [
          { id: 'payrun', label: 'Pay run', icon: 'calculator' },
          { id: 'employees', label: 'Employees', icon: 'users' },
          { id: 'periods', label: 'Pay periods', icon: 'calendar' }
        ]
      },
      {
        title: 'Calculations',
        items: [
          { id: 'earnings', label: 'Earnings', icon: 'document' },
          { id: 'deductions', label: 'Deductions', icon: 'calculator' },
          { id: 'sdl', label: 'SDL & Levies', icon: 'document' }
        ]
      },
      {
        title: 'Reports',
        items: [
          { id: 'summary', label: 'Summary', icon: 'chart' },
          { id: 'leave', label: 'Leave income', icon: 'calendar' }
        ]
      }
    ]

    return { sidebarSections }
  }
}
</script>

<style scoped>
.app-sidebar {
  width: var(--sidebar-width);
  background-color: var(--color-bg-sidebar);
  border-right: 1px solid var(--color-border);
  position: fixed;
  top: calc(var(--header-height) + var(--nav-height));
  left: 0;
  bottom: 0;
  overflow-y: auto;
  padding: 16px 0;
  z-index: 98;
}

.sidebar-section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 10px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 0 16px;
  margin-bottom: 8px;
}

.section-nav {
  display: flex;
  flex-direction: column;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  font-size: 13px;
  color: var(--color-text-base);
  text-decoration: none;
  border-left: 2px solid transparent;
  transition: all 0.15s ease;
}

.nav-link:hover {
  background-color: #f4f6fb;
}

.nav-link.active {
  background-color: var(--color-primary-light);
  border-left-color: var(--color-primary);
  color: var(--color-primary);
  font-weight: 500;
}

.nav-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}
</style>
