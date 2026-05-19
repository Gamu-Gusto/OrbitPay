<template>
  <div class="metric-card">
    <div class="metric-value" :class="{ 'text-success': type === 'success', 'text-error': type === 'error' }">
      {{ formattedValue }}
    </div>
    <div class="metric-label">{{ label }}</div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'MetricCard',
  props: {
    label: {
      type: String,
      required: true
    },
    value: {
      type: [Number, String],
      default: 0
    },
    type: {
      type: String,
      default: 'default' // 'default', 'success', 'error'
    },
    prefix: {
      type: String,
      default: ''
    }
  },
  setup(props) {
    const formattedValue = computed(() => {
      if (typeof props.value === 'number') {
        return props.prefix + new Intl.NumberFormat('en-ZA', {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2
        }).format(props.value)
      }
      return props.prefix + props.value
    })

    return { formattedValue }
  }
}
</script>

<style scoped>
.metric-card {
  background-color: var(--color-bg-card);
  border: 0.5px solid var(--color-border);
  border-radius: 8px;
  padding: 12px 16px;
  min-width: 140px;
}

.metric-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-base);
  line-height: 1.2;
}

.metric-value.text-success {
  color: var(--color-success);
}

.metric-value.text-error {
  color: var(--color-error);
}

.metric-label {
  font-size: 11px;
  color: var(--color-text-muted);
  margin-top: 4px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}
</style>
