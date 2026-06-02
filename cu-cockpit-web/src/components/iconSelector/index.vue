<template #default>

</template>
<script setup lang="ts" name="iconSelector">
import { defineAsyncComponent, ref, reactive, onMounted, nextTick, computed, watch } from 'vue';
import type { TabsPaneContext } from 'element-plus';
import initIconfont from '/@/utils/getStyleSheets';
import '/@/theme/iconSelector.scss';
</script>
