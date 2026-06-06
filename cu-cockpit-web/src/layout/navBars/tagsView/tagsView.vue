<template>

</template>
<script setup lang="ts" name="layoutTagsView">
import { defineAsyncComponent, reactive, onMounted, computed, ref, nextTick, onBeforeUpdate, onBeforeMount, onUnmounted, watch } from 'vue';
import { useRoute, useRouter, onBeforeRouteUpdate } from 'vue-router';
import Sortable from 'sortablejs';
import { ElMessage } from 'element-plus';
import { storeToRefs } from 'pinia';
import pinia from '/@/stores/index';
import { useTagsViewRoutes } from '/@/stores/tagsViewRoutes';
import { useThemeConfig } from '/@/stores/themeConfig';
import { useKeepALiveNames } from '/@/stores/keepAliveNames';
import { Session } from '/@/utils/storage';
import { isObjectValueEqual } from '/@/utils/arrayOperation';
import other from '/@/utils/other';
import mittBus from '/@/utils/mitt';
</script>
<style scoped lang="scss">
</style>
