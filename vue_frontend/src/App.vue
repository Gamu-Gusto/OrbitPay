<template>
  <div id="app" :class="{ 'sidebar-collapsed': sidebarCollapsed }">

    <!-- ── Authenticated layout ───────────────────────────── -->
    <template v-if="auth.isAuthenticated">

      <!-- Mobile backdrop -->
      <Transition name="backdrop-fade">
        <div v-if="sidebarOpen" class="sidebar-backdrop" @click="sidebarOpen = false" />
      </Transition>

      <!-- Global sidebar -->
      <AppPrimaryNav
        :is-open="sidebarOpen"
        :is-collapsed="sidebarCollapsed"
        @close="sidebarOpen = false"
        @toggle-collapse="toggleCollapse"
      />

      <!-- Content area (offset by sidebar on desktop) -->
      <div class="content-area">
        <!-- Mobile-only hamburger bar -->
        <AppHeader @toggle="sidebarOpen = !sidebarOpen" />

        <!-- Desktop sticky topbar -->
        <AppTopBar :collapsed="sidebarCollapsed" @toggle-sidebar="toggleCollapse" />

        <!-- Router view -->
        <main class="page-main">
          <router-view />
        </main>
      </div>

    </template>

    <!-- ── Unauthenticated pages (login / register) ──────── -->
    <template v-else>
      <router-view />
    </template>

    <!-- ── Toast notifications ───────────────────────────── -->
    <div class="toast-container">
      <Transition v-for="t in toastStore.toasts" :key="t.id" name="toast-slide">
        <div
          class="toast-item"
          :class="{
            'toast-success': t.type === 'success',
            'toast-error':   t.type === 'error',
            'toast-info':    t.type === 'info'
          }"
        >
          <div class="toast-dot" />
          <div class="toast-message">{{ t.message }}</div>
          <button class="toast-close" @click="toastStore.remove(t.id)">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      </Transition>
    </div>

  </div>
</template>

<script>
import { ref } from 'vue'
import { useAuthStore } from './stores/auth'
import { useToastStore } from './stores/toast'
import AppHeader from './components/layout/AppHeader.vue'
import AppPrimaryNav from './components/layout/AppPrimaryNav.vue'
import AppTopBar from './components/layout/AppTopBar.vue'

export default {
  name: 'App',
  components: { AppHeader, AppPrimaryNav, AppTopBar },
  setup() {
    const auth        = useAuthStore()
    const toastStore  = useToastStore()
    const sidebarOpen = ref(false)

    const stored = localStorage.getItem('sidebar-collapsed')
    const sidebarCollapsed = ref(stored === 'true')

    const toggleCollapse = () => {
      sidebarCollapsed.value = !sidebarCollapsed.value
      localStorage.setItem('sidebar-collapsed', sidebarCollapsed.value)
    }

    return { auth, toastStore, sidebarOpen, sidebarCollapsed, toggleCollapse }
  }
}
</script>

<style scoped>
/* ── App shell ───────────────────────────────────────────────────────────── */
#app {
  min-height: 100vh;
  background-color: var(--color-bg-page);
}

/* ── Content area ────────────────────────────────────────────────────────── */
.content-area {
  margin-left: var(--sidebar-width);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  transition: margin-left 0.22s cubic-bezier(0.4, 0, 0.2, 1);
}

#app.sidebar-collapsed .content-area {
  margin-left: 60px;
}

.page-main {
  flex: 1;
}

/* ── Mobile backdrop ─────────────────────────────────────────────────────── */
.sidebar-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 140;
  backdrop-filter: blur(2px);
}

/* ── Toast container ─────────────────────────────────────────────────────── */
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 600;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
}

.toast-item {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 260px;
  max-width: 360px;
  padding: 12px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 450;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  pointer-events: all;
  background: #fff;
  border: 1px solid var(--color-border);
}

.toast-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.toast-success { border-left: 3px solid var(--color-success); }
.toast-success .toast-dot { background: var(--color-success); }

.toast-error   { border-left: 3px solid var(--color-error); }
.toast-error .toast-dot   { background: var(--color-error); }

.toast-info    { border-left: 3px solid var(--color-accent); }
.toast-info .toast-dot    { background: var(--color-accent); }

.toast-message { flex: 1; line-height: 1.4; color: var(--color-text-base); }

.toast-close {
  display: flex;
  align-items: center;
  color: var(--color-text-muted);
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px;
  border-radius: 4px;
  opacity: 0.6;
}
.toast-close:hover { opacity: 1; background: var(--color-bg-page); }

/* ── Transitions ─────────────────────────────────────────────────────────── */
.backdrop-fade-enter-active, .backdrop-fade-leave-active { transition: opacity 0.2s; }
.backdrop-fade-enter-from, .backdrop-fade-leave-to { opacity: 0; }

.toast-slide-enter-active { transition: all 0.22s ease-out; }
.toast-slide-leave-active { transition: all 0.18s ease-in; }
.toast-slide-enter-from { opacity: 0; transform: translateX(20px); }
.toast-slide-leave-to   { opacity: 0; transform: translateX(20px); }

/* ── Mobile ──────────────────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .content-area {
    margin-left: 0 !important;
  }

  .toast-container {
    top: calc(var(--header-height) + 12px);
    right: 12px;
    left: 12px;
  }
  .toast-item {
    min-width: unset;
    max-width: 100%;
  }
}
</style>
