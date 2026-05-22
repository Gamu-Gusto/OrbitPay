<template>
  <div class="sk-profile card">
    <!-- Avatar + name -->
    <div class="sk-profile-header">
      <SkeletonLoader type="circle" width="72px" height="72px" />
      <div class="sk-profile-name">
        <SkeletonLoader type="line" width="160px" height="20px" style="margin-bottom:8px" />
        <SkeletonLoader type="line" width="120px" height="14px" />
      </div>
    </div>
    <!-- Fields grid -->
    <div class="sk-fields">
      <div v-for="i in 8" :key="i" class="sk-field">
        <SkeletonLoader type="line" width="80px" height="11px" style="margin-bottom:6px" />
        <SkeletonLoader type="block" width="100%" height="36px" />
      </div>
    </div>
  </div>
</template>

<script>
import SkeletonLoader from './SkeletonLoader.vue'
export default {
  name: 'SkeletonProfile',
  components: { SkeletonLoader },
}
</script>

<style scoped>
.sk-profile { padding: 24px; }
.sk-profile-header { display: flex; align-items: center; gap: 20px; margin-bottom: 28px; }
.sk-profile-name { flex: 1; }
.sk-fields { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.sk-field { display: flex; flex-direction: column; }
@media (max-width: 600px) { .sk-fields { grid-template-columns: 1fr; } }
</style>
