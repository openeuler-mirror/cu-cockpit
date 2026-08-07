<template>
	<div class="assistant-page"></div>
</template>

<script setup lang="ts" name="assistantIndex">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue';
import { storeToRefs } from 'pinia';
import { userPermissiom } from '/@/stores/userPermissiom';
import { useThemeConfig } from '/@/stores/themeConfig';

const permissionStore = userPermissiom();
const { u_Permission } = storeToRefs(permissionStore);
const themeStore = useThemeConfig();
const { themeConfig } = storeToRefs(themeStore);
const isAdmin = computed(() => u_Permission.value === 'root');
const activeTab = ref('operations');
const loading = ref(false);
const refreshedAt = ref('');
const provider = reactive({ available: false, model: '', reason: '正在检查 AI Provider' });
const toolCount = ref(0);
const operationRequest = ref('查看 8080 端口由哪个进程监听');
const operationPlan = ref<any>(null);
const operationResult = ref<any>(null);
const planLoading = ref(false);
const executionLoading = ref(false);
</script>
