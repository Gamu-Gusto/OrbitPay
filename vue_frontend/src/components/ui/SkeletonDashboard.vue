<template>
  <div class="sk-dashboard">
    <!-- Stat cards -->
    <div class="sk-stats">
      <div v-for="i in 4" :key="i" class="sk-stat-card card">
        <div class="sk-stat-icon"><SkeletonLoader type="circle" width="40px" height="40px" /></div>
        <div class="sk-stat-body">
          <SkeletonLoader type="line" width="60px" height="22px" style="margin-bottom:6px" />
          <SkeletonLoader type="line" width="100px" height="13px" />
        </div>
      </div>
    </div>
    <!-- Table section -->
    <div class="card" style="margin-top:20px">
      <SkeletonLoader type="line" width="140px" height="16px" style="margin-bottom:16px" />
      <SkeletonTable :rows="5" :cols="4" />
    </div>
  </div>
</template>

<script>
import SkeletonLoader from './SkeletonLoader.vue'
import SkeletonTable from './SkeletonTable.vue'
export default {
  name: 'SkeletonDashboard',
  components: { SkeletonLoader, SkeletonTable },
}
</script>

<style scoped>
.sk-dashboard { display: flex; flex-direction: column; }
.sk-stats { display: flex; gap: 12px; flex-wrap: wrap; }
.sk-stat-card { display: flex; align-items: center; gap: 14px; flex: 1; min-width: 180px; }
.sk-stat-icon { flex-shrink: 0; }
.sk-stat-body { flex: 1; }
</style>
