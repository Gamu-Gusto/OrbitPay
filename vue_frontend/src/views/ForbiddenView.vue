<template>
  <div class="forbidden-page">
    <div class="forbidden-card card">
      <div class="forbidden-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="10"/>
          <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>
        </svg>
      </div>
      <h1 class="forbidden-title">Access Denied</h1>
      <p class="forbidden-sub">You don't have permission to view this page.</p>
      <div class="forbidden-actions">
        <button @click="goBack" class="btn-secondary">← Go Back</button>
        <router-link to="/" class="btn-primary">Dashboard</router-link>
      </div>
    </div>
  </div>
</template>

<script>
import { useRouter } from 'vue-router'

export default {
  name: 'ForbiddenView',
  setup() {
    const router = useRouter()
    const goBack = () => {
      if (window.history.length > 2) router.go(-1)
      else router.push('/')
    }
    return { goBack }
  }
}
</script>

<style scoped>
.forbidden-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-page);
  padding: 24px;
}
.forbidden-card {
  max-width: 420px;
  width: 100%;
  text-align: center;
  padding: 48px 32px;
}
.forbidden-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 24px;
  color: var(--color-error, #ef4444);
  opacity: 0.8;
}
.forbidden-icon svg { width: 100%; height: 100%; }
.forbidden-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--color-text-base);
  margin: 0 0 10px;
}
.forbidden-sub {
  font-size: 14px;
  color: var(--color-text-muted);
  margin: 0 0 32px;
  line-height: 1.5;
}
.forbidden-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}
</style>
