<template #reference>

</template>
<script lang="ts" setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue';
import * as echarts from 'echarts';
import { monitorStatus, hardInfo } from '/@/api/run/run';
import { debounce } from 'lodash';
</script>
<style lang="scss" scoped>
</style>