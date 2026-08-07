<template>
	<div class="assistant-page"></div>
</template>

<script setup lang="ts" name="assistantIndex">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue';
import { storeToRefs } from 'pinia';
import { ElMessage, ElMessageBox } from 'element-plus';
import { assistantRequest } from '/@/api/system/assistant';
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

const loadWorkspace = async () => {
	loading.value = true;
	try {
		await permissionStore.refreshUserPermission();
		const [status, metrics, rules, events, runbookData] = await Promise.all([
			assistantRequest<any>('/system/ai/status'),
			assistantRequest<any>('/system/monitoring/samples', 'get', undefined, { hours: 24, limit: 500 }),
			assistantRequest<any>('/system/monitoring/alert-rules'),
			assistantRequest<any>('/system/monitoring/alert-events', 'get', undefined, { limit: 100 }),
			assistantRequest<any>('/system/ai/runbooks'),
		]);
		Object.assign(provider, status.provider);
		toolCount.value = status.tools?.length || 0;
		metricSamples.value = metrics.items || [];
		alertRules.value = rules.items || [];
		alertEvents.value = events.items || [];
		runbooks.value = runbookData.items || [];
		if (!selectedRunbookId.value && runbooks.value.length) selectedRunbookId.value = runbooks.value[0].id;
		refreshedAt.value = new Date().toISOString();
	} catch (error) {
		ElMessage.error('AI 运维工作台加载失败');
		console.error('load assistant workspace failed:', error);
	} finally {
		loading.value = false;
	}
};

const createOperationPlan = async () => {
	if (!operationRequest.value.trim()) return ElMessage.warning('请输入运维需求');
	if (!provider.available) return ElMessage.warning(provider.reason || 'AI Provider 不可用');
	planLoading.value = true;
	operationResult.value = null;
	try {
		const response = await assistantRequest<any>('/system/ai/plans', 'post', {
			request: operationRequest.value.trim(),
		});
		operationPlan.value = response.plan;
		ElMessage.success('受控运维计划已生成');
	} catch (error) {
		console.error('create AI plan failed:', error);
	} finally {
		planLoading.value = false;
	}
};

const executeOperationPlan = async () => {
	if (!operationPlan.value) return;
	if (operationPlan.value.risk !== 'readonly' && !isAdmin.value) {
		return ElMessage.warning('该变更计划需要管理员权限');
	}
	await ElMessageBox.confirm(
		`确认执行 ${operationPlan.value.tool_calls?.[0]?.tool || '受控工具'}？风险级别：${operationPlan.value.risk}`,
		'执行 AI 运维计划',
		{ type: operationPlan.value.risk === 'readonly' ? 'info' : 'warning', confirmButtonText: '确认执行' },
	);
	executionLoading.value = true;
	try {
		const response = await assistantRequest<any>(
			`/system/ai/plans/${operationPlan.value.id}/execute`, 'post', { confirmed: true },
		);
		operationPlan.value = response.plan;
		operationResult.value = response.plan.result;
		ElMessage.success('计划执行完成');
		await loadWorkspace();
	} catch (error) {
		console.error('execute AI plan failed:', error);
	} finally {
		executionLoading.value = false;
	}
};

const analyzeLogs = async () => {
	let logs: any[];
	try {
		logs = JSON.parse(logsInput.value);
		if (!Array.isArray(logs)) throw new Error('logs must be an array');
	} catch (error) {
		return ElMessage.warning('请输入有效的 JSON 日志数组');
	}
	analysisLoading.value = true;
	try {
		analysisResult.value = await assistantRequest<any>('/system/ai/analyze/logs', 'post', { logs });
	} catch (error) {
		console.error('analyze logs failed:', error);
	} finally {
		analysisLoading.value = false;
	}
};

const explainOutput = async () => {
	if (!outputInput.value.trim()) return ElMessage.warning('请输入命令输出');
	analysisLoading.value = true;
	try {
		analysisResult.value = await assistantRequest<any>('/system/ai/explain-output', 'post', {
			output: outputInput.value,
		});
	} catch (error) {
		console.error('explain command output failed:', error);
	} finally {
		analysisLoading.value = false;
	}
};

const reviewConfig = async () => {
	if (!snapshotId.value) return ElMessage.warning('请输入配置快照 ID');
	analysisLoading.value = true;
	try {
		analysisResult.value = await assistantRequest<any>('/system/ai/review-config', 'post', {
			snapshot_id: snapshotId.value,
		});
	} catch (error) {
		console.error('review config failed:', error);
	} finally {
		analysisLoading.value = false;
	}
};

const askKnowledge = async () => {
	if (!knowledgeQuestion.value.trim()) return ElMessage.warning('请输入运维问题');
	analysisLoading.value = true;
	try {
		analysisResult.value = await assistantRequest<any>('/system/ai/knowledge', 'post', {
			question: knowledgeQuestion.value.trim(),
		});
	} catch (error) {
		console.error('answer knowledge question failed:', error);
	} finally {
		analysisLoading.value = false;
	}
};

const createAlertRule = async () => {
	if (!isAdmin.value) return ElMessage.warning('创建告警规则需要管理员权限');
	alertSaving.value = true;
	try {
		await assistantRequest('/system/monitoring/alert-rules/create', 'post', { ...alertForm });
		alertDialog.value = false;
		ElMessage.success('告警规则已创建');
		await loadWorkspace();
	} catch (error) {
		console.error('create alert rule failed:', error);
	} finally {
		alertSaving.value = false;
	}
};

const toggleAlertRule = async (rule: any, enabled: string | number | boolean) => {
	if (!isAdmin.value) return ElMessage.warning('修改告警规则需要管理员权限');
	alertSaving.value = true;
	try {
		await assistantRequest(`/system/monitoring/alert-rules/${rule.id}/toggle`, 'post', {
			enabled: Boolean(enabled),
		});
		ElMessage.success(enabled ? '告警规则已启用' : '告警规则已停用');
		await loadWorkspace();
	} catch (error) {
		console.error('toggle alert rule failed:', error);
	} finally {
		alertSaving.value = false;
	}
};

const acknowledgeAlert = async (event: any) => {
	try {
		await assistantRequest(`/system/monitoring/alert-events/${event.id}/acknowledge`, 'post');
		ElMessage.success('告警已确认，等待指标恢复');
		await loadWorkspace();
	} catch (error) {
		console.error('acknowledge alert failed:', error);
	}
};
</script>
