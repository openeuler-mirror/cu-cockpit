<template>
	<div class="assistant-page" v-loading="loading">
		<header class="assistant-hud">
			<div class="assistant-identity">
				<span class="assistant-identity__mark"><el-icon><MagicStick /></el-icon></span>
				<div>
					<h1>AI 运维助手</h1>
					<p>CONTROLLED OPERATIONS · VERIFIED TOOLS · HUMAN CONFIRMATION</p>
				</div>
			</div>
			<div class="assistant-hud__status">
				<div class="provider-state" :class="{ 'is-online': provider.available }">
					<span class="provider-state__dot"></span>
					<div>
						<strong>{{ provider.available ? 'AI Provider 在线' : 'AI Provider 未就绪' }}</strong>
						<small>{{ provider.model || provider.reason }}</small>
					</div>
				</div>
				<span class="assistant-sync">同步 {{ formatTime(refreshedAt) }}</span>
				<el-button class="assistant-icon-button" :icon="Refresh" circle :loading="loading" @click="loadWorkspace" />
			</div>
		</header>

		<section class="assistant-summary">
			<div class="assistant-summary__item"><el-icon><Key /></el-icon><span>受控工具</span><strong>{{ toolCount }}</strong></div>
			<div class="assistant-summary__item"><el-icon><Connection /></el-icon><span>最新 CPU</span><strong>{{ latestMetric.cpu_percent == null ? '—' : `${Number(latestMetric.cpu_percent).toFixed(1)}%` }}</strong></div>
			<div class="assistant-summary__item is-alert"><el-icon><Bell /></el-icon><span>活动告警</span><strong>{{ activeAlertCount }}</strong></div>
			<div class="assistant-summary__item"><el-icon><Guide /></el-icon><span>Runbook</span><strong>{{ runbooks.length }}</strong></div>
		</section>

		<nav class="assistant-tabs" aria-label="AI 运维工作区">
			<button :class="{ 'is-active': activeTab === 'operations' }" @click="activeTab = 'operations'"><MagicStick />自然语言运维</button>
			<button :class="{ 'is-active': activeTab === 'analysis' }" @click="activeTab = 'analysis'"><Search />智能分析</button>
			<button :class="{ 'is-active': activeTab === 'alerts' }" @click="activeTab = 'alerts'"><Bell />历史与告警</button>
			<button :class="{ 'is-active': activeTab === 'runbooks' }" @click="activeTab = 'runbooks'"><Guide />Runbook</button>
		</nav>

		<main class="assistant-workspace">
			<section v-if="activeTab === 'operations'" class="assistant-grid assistant-grid--operations">
				<article class="assistant-panel operation-composer">
					<div class="assistant-panel__head">
						<div><span class="panel-index">01</span><h2>运维需求</h2></div>
						<el-tag effect="dark" type="info">自然语言</el-tag>
					</div>
					<el-input
						v-model="operationRequest" type="textarea" :rows="8" maxlength="2000"
						show-word-limit placeholder="例如：查看 8080 端口占用，或每天凌晨 2 点执行 df -h"
					/>
					<div class="assistant-panel__actions">
						<el-button :icon="MagicStick" type="primary" :loading="planLoading" :disabled="!provider.available" @click="createOperationPlan">生成受控计划</el-button>
					</div>
				</article>

				<article class="assistant-panel operation-plan">
					<div class="assistant-panel__head">
						<div><span class="panel-index">02</span><h2>执行计划</h2></div>
						<el-tag v-if="operationPlan" effect="dark" :type="operationPlan.risk === 'readonly' ? 'success' : 'warning'">{{ operationPlan.risk }}</el-tag>
					</div>
					<template v-if="operationPlan">
						<div class="plan-facts">
							<div><span>意图</span><strong>{{ operationPlan.intent }}</strong></div>
							<div><span>状态</span><strong>{{ operationPlan.status }}</strong></div>
							<div><span>注册工具</span><strong>{{ operationPlan.tool_calls?.[0]?.tool }}</strong></div>
						</div>
						<p class="plan-summary">{{ operationPlan.summary || '等待用户审查' }}</p>
						<pre class="assistant-code">{{ formatJson(operationPlan.tool_calls?.[0]?.arguments) }}</pre>
						<el-alert v-if="operationPlan.risk !== 'readonly'" title="该计划会修改系统，执行前需要管理员权限和再次确认。" type="warning" :closable="false" show-icon />
						<div class="assistant-panel__actions">
							<el-button
								:icon="operationPlan.risk === 'readonly' ? VideoPlay : Key" type="primary"
								:loading="executionLoading" :disabled="operationPlan.status !== 'draft'"
								@click="executeOperationPlan"
							>确认并执行</el-button>
						</div>
						<pre v-if="operationResult" class="assistant-code assistant-code--result">{{ formatJson(operationResult) }}</pre>
					</template>
					<el-empty v-else :image-size="72" description="尚未生成计划" />
				</article>
			</section>
		</main>
	</div>
</template>

<script setup lang="ts" name="assistantIndex">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue';
import { storeToRefs } from 'pinia';
import {
	Bell, CircleCheck, Connection, Document, Guide, Key,
	MagicStick, Plus, Refresh, Search, VideoPlay, Warning,
} from '@element-plus/icons-vue';
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
const latestMetric = computed(() => metricSamples.value[metricSamples.value.length - 1] || {});
const metricLabels: Record<string, string> = {
	cpu_percent: 'CPU 使用率', memory_percent: '内存使用率',
	root_percent: '根文件系统', inode_percent: '根 inode',
};
const runbookStatusLabels: Record<string, string> = {
	draft: '草稿', running: '运行中', paused: '等待确认', completed: '已完成',
	failed: '失败', cancelled: '已取消', pending: '待执行',
	awaiting_confirmation: '等待确认', succeeded: '成功', skipped: '已跳过',
};

const formatTime = (value?: string) => value
	? new Intl.DateTimeFormat('zh-CN', {
		year: 'numeric', month: '2-digit', day: '2-digit',
		hour: '2-digit', minute: '2-digit', second: '2-digit',
	}).format(new Date(value))
	: '—';

const formatJson = (value: unknown) => {
	try {
		return JSON.stringify(value, null, 2);
	} catch (error) {
		return String(value ?? '');
	}
};

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

const analyzeAlert = async (event: any) => {
	analysisLoading.value = true;
	try {
		alertAnalysis.value = await assistantRequest<any>(
			`/system/monitoring/alert-events/${event.id}/analyze`, 'post',
		);
	} catch (error) {
		console.error('analyze alert failed:', error);
	} finally {
		analysisLoading.value = false;
	}
};

const generateRunbook = async () => {
	if (!runbookPrompt.value.trim()) return ElMessage.warning('请输入 Runbook 需求');
	if (!provider.available) return ElMessage.warning(provider.reason || 'AI Provider 不可用');
	runbookLoading.value = true;
	try {
		const response = await assistantRequest<any>('/system/ai/runbooks/generate', 'post', {
			request: runbookPrompt.value.trim(),
		});
		selectedRunbookId.value = response.runbook.id;
		ElMessage.success('受控 Runbook 已生成');
		await loadWorkspace();
	} catch (error) {
		console.error('generate Runbook failed:', error);
	} finally {
		runbookLoading.value = false;
	}
};

const advanceRunbook = async () => {
	if (!currentRunbook.value) return;
	runbookLoading.value = true;
	try {
		const response = await assistantRequest<any>(
			`/system/ai/runbooks/${currentRunbook.value.id}/advance`, 'post',
		);
		confirmationToken.value = response.confirmation_token || '';
		if (response.action === 'confirmation_required') {
			ElMessage.warning('当前步骤会修改系统，请确认后继续');
		} else {
			ElMessage.success(response.action === 'completed' ? 'Runbook 已完成' : '当前步骤执行成功');
		}
		await loadWorkspace();
	} catch (error) {
		console.error('advance Runbook failed:', error);
	} finally {
		runbookLoading.value = false;
	}
};

const confirmRunbook = async () => {
	if (!currentRunbook.value || !confirmationToken.value) {
		return ElMessage.warning('当前会话没有可用的一次性确认令牌');
	}
	runbookLoading.value = true;
	try {
		await assistantRequest(`/system/ai/runbooks/${currentRunbook.value.id}/confirm`, 'post', {
			confirmation_token: confirmationToken.value,
		});
		confirmationToken.value = '';
		ElMessage.success('步骤已确认，请执行当前步骤');
		await loadWorkspace();
	} catch (error) {
		console.error('confirm Runbook failed:', error);
	} finally {
		runbookLoading.value = false;
	}
};

const retryRunbook = async () => {
	if (!currentRunbook.value) return;
	runbookLoading.value = true;
	try {
		await assistantRequest(`/system/ai/runbooks/${currentRunbook.value.id}/retry`, 'post');
		confirmationToken.value = '';
		ElMessage.success('失败步骤已重置');
		await loadWorkspace();
	} catch (error) {
		console.error('retry Runbook failed:', error);
	} finally {
		runbookLoading.value = false;
	}
};

const skipRunbook = async () => {
	if (!currentRunbook.value) return;
	runbookLoading.value = true;
	try {
		await assistantRequest(`/system/ai/runbooks/${currentRunbook.value.id}/skip`, 'post');
		ElMessage.success('失败的只读步骤已跳过');
		await loadWorkspace();
	} catch (error) {
		console.error('skip Runbook step failed:', error);
	} finally {
		runbookLoading.value = false;
	}
};

const cancelRunbook = async () => {
	if (!currentRunbook.value) return;
	await ElMessageBox.confirm(
		'取消后不会执行未开始步骤，已成功步骤不会自动回滚。',
		'取消 Runbook',
		{ type: 'warning', confirmButtonText: '确认取消' },
	);
	runbookLoading.value = true;
	try {
		await assistantRequest(`/system/ai/runbooks/${currentRunbook.value.id}/cancel`, 'post');
		confirmationToken.value = '';
		ElMessage.success('Runbook 已取消');
		await loadWorkspace();
	} catch (error) {
		console.error('cancel Runbook failed:', error);
	} finally {
		runbookLoading.value = false;
	}
};

const mountAssistantTheme = () => document.documentElement.classList.add('theme-tech-dark');
const restoreAssistantTheme = () => {
	if (!themeConfig.value.isTechTheme) document.documentElement.classList.remove('theme-tech-dark');
};
onMounted(mountAssistantTheme);
onMounted(loadWorkspace);
onUnmounted(restoreAssistantTheme);
</script>
