<template>
  <div class="sk-portal">
    <!-- Welcome card -->
    <div class="card sk-welcome">
      <SkeletonLoader type="circle" width="56px" height="56px" />
      <div class="sk-welcome-info">
        <SkeletonLoader type="line" width="160px" height="18px" style="margin-bottom:8px" />
        <SkeletonLoader type="line" width="120px" height="13px" style="margin-bottom:6px" />
        <SkeletonLoader type="line" width="200px" height="12px" />
      </div>
    </div>
    <!-- Cards grid -->
    <div class="sk-cards-grid">
      <div v-for="i in 4" :key="i" class="card sk-dash-card">
        <SkeletonLoader type="line" width="100px" height="12px" style="margin-bottom:14px" />
        <SkeletonLoader type="line" width="100%" height="14px" style="margin-bottom:8px" />
        <SkeletonLoader type="line" width="80%" height="14px" style="margin-bottom:8px" />
        <SkeletonLoader type="line" width="90%" height="14px" />
      </div>
    </div>
  </div>
</template>

<script>
import SkeletonLoader from './SkeletonLoader.vue'
export default {
  name: 'SkeletonEmployeePortal',
  components: { SkeletonLoader },
}
</script>

<style scoped>
.sk-portal { display: flex; flex-direction: column; gap: 20px; }
.sk-welcome { display: flex; align-items: center; gap: 20px; }
.sk-welcome-info { flex: 1; }
.sk-cards-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.sk-dash-card { padding: 18px; }
@media (max-width: 768px) { .sk-cards-grid { grid-template-columns: 1fr 1fr; } }
</style>
