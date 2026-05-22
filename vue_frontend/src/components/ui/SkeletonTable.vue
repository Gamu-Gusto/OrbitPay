<template>
  <div class="sk-table-wrap">
    <!-- Header -->
    <div class="sk-table-header">
      <SkeletonLoader v-for="i in cols" :key="i" type="line" :width="headerWidths[i-1] || '80px'" />
    </div>
    <!-- Rows -->
    <div v-for="r in rows" :key="r" class="sk-table-row">
      <SkeletonLoader v-for="c in cols" :key="c" type="line" :width="rowWidths[(c-1) % rowWidths.length]" />
    </div>
  </div>
</template>

<script>
import SkeletonLoader from './SkeletonLoader.vue'
export default {
  name: 'SkeletonTable',
  components: { SkeletonLoader },
  props: {
    rows: { type: Number, default: 5 },
    cols: { type: Number, default: 4 },
  },
  data() {
    return {
      headerWidths: ['120px', '100px', '80px', '90px', '70px', '80px'],
      rowWidths:    ['160px', '120px', '80px', '100px', '70px', '80px'],
    }
  },
}
</script>

<style scoped>
.sk-table-wrap { display: flex; flex-direction: column; gap: 0; padding: 0 4px; }
.sk-table-header {
  display: flex; gap: 16px; align-items: center;
  padding: 12px 14px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}
.sk-table-row {
  display: flex; gap: 16px; align-items: center;
  padding: 14px 14px;
  border-bottom: 1px solid #e2e8f0;
}
.sk-table-row:last-child { border-bottom: none; }
</style>
