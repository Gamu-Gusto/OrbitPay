<template>
  <header class="mobile-header">
    <button class="hamburger-btn" @click="$emit('toggle')" aria-label="Open menu">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
        <line x1="3" y1="6"  x2="21" y2="6"/>
        <line x1="3" y1="12" x2="21" y2="12"/>
        <line x1="3" y1="18" x2="21" y2="18"/>
      </svg>
    </button>

    <div class="mobile-brand">
      <img src="/OrbitPayfinal.jpeg" alt="OrbitPay" class="mobile-brand-logo" />
    </div>

    <div class="mobile-right">
      <div class="mobile-avatar">{{ initials }}</div>
    </div>
  </header>
</template>

<script>
import { computed } from 'vue'
import { useAuthStore } from '../../stores/auth'

export default {
  name: 'AppHeader',
  emits: ['toggle'],
  setup() {
    const auth = useAuthStore()
    const initials = computed(() => {
      const u = auth.user
      if (!u) return '?'
      return ((u.first_name?.[0] || '') + (u.last_name?.[0] || '')).toUpperCase() || '?'
    })
    return { initials }
  }
}
</script>

<style scoped>
/* Hidden on desktop — only renders on mobile */
.mobile-header {
  display: none;
}

@media (max-width: 768px) {
  .mobile-header {
    display: flex;
    align-items: center;
    gap: 12px;
    position: sticky;
    top: 0;
    z-index: 100;
    height: var(--header-height);
    background: var(--color-bg-sidebar);
    padding: 0 16px;
    box-shadow: 0 1px 0 rgba(255,255,255,0.06);
    flex-shrink: 0;
  }

  .hamburger-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: 8px;
    border: none;
    background: rgba(255,255,255,0.08);
    color: rgba(255,255,255,0.85);
    cursor: pointer;
    flex-shrink: 0;
  }
  .hamburger-btn:hover { background: rgba(255,255,255,0.14); }

  .mobile-brand {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 15px;
    font-weight: 600;
    color: #fff;
    letter-spacing: -0.2px;
  }

  .mobile-brand-logo {
    height: 44px;
    width: auto;
    max-width: 140px;
    object-fit: contain;
    flex-shrink: 0;
    border-radius: 4px;
  }

  .mobile-right {
    display: flex;
    align-items: center;
  }

  .mobile-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg, #475569, #334155);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 600;
    color: #fff;
  }
}
</style>
