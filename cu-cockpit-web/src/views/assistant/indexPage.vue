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
const analysisMode = ref('logs');
const logsInput = ref('[\n  { "service": "sshd", "message": "Failed password for root" }\n]');
const outputInput = ref('');
const snapshotId = ref<number | null>(null);
const knowledgeQuestion = ref('如何安全排查 nginx 服务启动失败？');
const analysisResult = ref<any>(null);
const analysisLoading = ref(false);
const metricSamples = ref<any[]>([]);
const alertRules = ref<any[]>([]);
const alertEvents = ref<any[]>([]);
const alertDialog = ref(false);
const alertSaving = ref(false);
const alertAnalysis = ref<any>(null);
const alertForm = reactive({
	name: '根文件系统使用率过高', metric: 'root_percent', operator: 'gte',
	threshold: 85, recovery_threshold: 75, consecutive_hits: 3, enabled: true,
});
const activeAlertCount = computed(() => alertEvents.value.filter((item) => item.status === 'active').length);
const runbookPrompt = ref('检查 nginx 服务状态和 80 端口；必要时重启 nginx');
const runbooks = ref<any[]>([]);
const selectedRunbookId = ref<number | null>(null);
const confirmationToken = ref('');
const runbookLoading = ref(false);
const currentRunbook = computed(() => runbooks.value.find((item) => item.id === selectedRunbookId.value) || null);
</script>
