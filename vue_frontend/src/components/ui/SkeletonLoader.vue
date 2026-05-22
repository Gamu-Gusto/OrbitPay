<template>
  <div
    class="skeleton"
    :class="[`skeleton--${type}`]"
    :style="{ width: width, height: computedHeight, borderRadius: computedRadius }"
    aria-hidden="true"
  ></div>
</template>

<script>
export default {
  name: 'SkeletonLoader',
  props: {
    type: { type: String, default: 'line' }, // line | block | circle | card
    width: { type: String, default: '100%' },
    height: { type: String, default: null },
  },
  computed: {
    computedHeight() {
      if (this.height) return this.height
      return { line: '14px', block: '40px', circle: '40px', card: '120px' }[this.type] || '14px'
    },
    computedRadius() {
      return { line: '4px', block: '8px', circle: '50%', card: '12px' }[this.type] || '4px'
    },
  },
}
</script>

<style scoped>
@keyframes skeleton-pulse {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}
.skeleton {
  display: block;
  background: linear-gradient(
    90deg,
    #f1f5f9 25%,
    #e2e8f0 50%,
    #f1f5f9 75%
  );
  background-size: 200% 100%;
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}
.skeleton--circle { width: 40px; height: 40px; }
</style>
