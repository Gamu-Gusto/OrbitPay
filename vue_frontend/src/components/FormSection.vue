<template>
  <div class="form-section-card">
    <h3 class="section-title">
      <svg v-if="icon" class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path v-if="icon === 'import'" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
        <path v-else-if="icon === 'user'" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
        <path v-else-if="icon === 'building'" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5"/>
        <path v-else-if="icon === 'calendar'" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
        <path v-else-if="icon === 'calculator'" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
        <path v-else-if="icon === 'money'" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        <path v-else-if="icon === 'document'" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
        <path v-else d="M13 10V3L4 14h7v7l9-11h-7z"/>
      </svg>
      {{ title }}
    </h3>
    <div class="section-content">
      <slot></slot>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FormSection',
  props: {
    title: {
      type: String,
      required: true
    },
    icon: {
      type: String,
      default: ''
    }
  }
}
</script>

<style scoped>
.form-section-card {
  background-color: var(--color-bg-card);
  border: 0.5px solid var(--color-border);
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 16px;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-base);
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-icon {
  width: 16px;
  height: 16px;
  color: var(--color-primary);
  flex-shrink: 0;
}

.section-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

@media (max-width: 768px) {
  .section-content {
    grid-template-columns: 1fr;
  }
}
</style>
