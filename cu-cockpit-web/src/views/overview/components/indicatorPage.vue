<template>

</template>
<script lang="ts" setup name="indicator">
import { reactive, onMounted, ref, onUnmounted } from 'vue';
import * as echarts from 'echarts';
import { monitorStatus, hardInfo } from '/@/api/run/run';
import { useRouter } from 'vue-router';
</script>
<style scoped lang="scss">
</style>