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

			<section v-else-if="activeTab === 'analysis'" class="assistant-grid assistant-grid--analysis">
				<article class="assistant-panel analysis-input">
					<div class="assistant-panel__head"><div><span class="panel-index">01</span><h2>分析输入</h2></div></div>
					<el-segmented v-model="analysisMode" :options="analysisOptions" block />
					<div v-if="analysisMode === 'logs'" class="analysis-editor">
						<el-input v-model="logsInput" type="textarea" :rows="10" placeholder="JSON 日志数组" />
						<el-button type="primary" :icon="Search" :loading="analysisLoading" @click="analyzeLogs">分析日志</el-button>
					</div>
					<div v-else-if="analysisMode === 'output'" class="analysis-editor">
						<el-input v-model="outputInput" type="textarea" :rows="10" placeholder="粘贴命令输出" />
						<el-button type="primary" :icon="Document" :loading="analysisLoading" @click="explainOutput">解释输出</el-button>
					</div>
					<div v-else-if="analysisMode === 'config'" class="analysis-editor">
						<el-input-number v-model="snapshotId" :min="1" controls-position="right" placeholder="快照 ID" />
						<el-button type="primary" :icon="Document" :loading="analysisLoading" @click="reviewConfig">审查快照</el-button>
					</div>
					<div v-else class="analysis-editor">
						<el-input v-model="knowledgeQuestion" type="textarea" :rows="7" maxlength="500" placeholder="输入运维问题" />
						<el-button type="primary" :icon="Search" :loading="analysisLoading" @click="askKnowledge">检索并回答</el-button>
					</div>
				</article>

				<article class="assistant-panel analysis-result">
					<div class="assistant-panel__head">
						<div><span class="panel-index">02</span><h2>分析结果</h2></div>
						<el-tag v-if="analysisResult?.truncated" type="warning" effect="dark">输入已截断</el-tag>
					</div>
					<template v-if="analysisResult">
						<pre class="assistant-code assistant-code--analysis">{{ formatJson(analysisResult.analysis || analysisResult.answer || analysisResult) }}</pre>
						<div v-if="analysisResult.matches?.length" class="analysis-sources">
							<span v-for="match in analysisResult.matches" :key="`${match.source}-${match.score}`">{{ match.source }}</span>
						</div>
					</template>
					<el-empty v-else :image-size="72" description="等待分析" />
				</article>
			</section>

			<section v-else-if="activeTab === 'alerts'" class="alerts-workspace">
				<div class="metric-strip">
					<div v-for="(label, key) in metricLabels" :key="key" class="metric-strip__item">
						<span>{{ label }}</span>
						<strong>{{ latestMetric[key] == null ? '—' : `${Number(latestMetric[key]).toFixed(1)}%` }}</strong>
						<small>{{ metricSamples.length }} 个历史样本</small>
					</div>
				</div>
				<article class="assistant-panel metric-history-panel">
					<div class="assistant-panel__head"><div><span class="panel-index">H24</span><h2>最近指标样本</h2></div><span class="assistant-sync">最近 24 小时</span></div>
					<el-table :data="recentMetricSamples" class="assistant-table" max-height="300" empty-text="等待采样任务写入数据">
						<el-table-column label="采样时间" min-width="170"><template #default="{ row }">{{ formatTime(row.collected_at) }}</template></el-table-column>
						<el-table-column label="CPU" width="90"><template #default="{ row }">{{ row.cpu_percent == null ? '—' : `${Number(row.cpu_percent).toFixed(1)}%` }}</template></el-table-column>
						<el-table-column label="内存" width="90"><template #default="{ row }">{{ row.memory_percent == null ? '—' : `${Number(row.memory_percent).toFixed(1)}%` }}</template></el-table-column>
						<el-table-column label="根目录" width="90"><template #default="{ row }">{{ row.root_percent == null ? '—' : `${Number(row.root_percent).toFixed(1)}%` }}</template></el-table-column>
						<el-table-column label="inode" width="90"><template #default="{ row }">{{ row.inode_percent == null ? '—' : `${Number(row.inode_percent).toFixed(1)}%` }}</template></el-table-column>
					</el-table>
				</article>

				<div class="assistant-grid assistant-grid--alerts">
					<article class="assistant-panel alert-rules-panel">
						<div class="assistant-panel__head">
							<div><span class="panel-index">01</span><h2>告警规则</h2></div>
							<el-button :icon="Plus" type="primary" :disabled="!isAdmin" @click="alertDialog = true">新建规则</el-button>
						</div>
						<el-table :data="alertRules" class="assistant-table" empty-text="暂无告警规则">
							<el-table-column prop="name" label="规则" min-width="160" />
							<el-table-column label="指标" min-width="120"><template #default="{ row }">{{ metricLabels[row.metric] || row.metric }}</template></el-table-column>
							<el-table-column label="阈值" width="110"><template #default="{ row }">{{ row.operator === 'gte' ? '≥' : '≤' }} {{ row.threshold }}%</template></el-table-column>
							<el-table-column label="连续" width="80"><template #default="{ row }">{{ row.consecutive_hits }} 次</template></el-table-column>
							<el-table-column label="状态" width="90"><template #default="{ row }"><el-switch :model-value="row.enabled" :disabled="!isAdmin || alertSaving" @change="toggleAlertRule(row, $event)" /></template></el-table-column>
						</el-table>
					</article>
					<article class="assistant-panel alert-events-panel">
						<div class="assistant-panel__head">
							<div><span class="panel-index">02</span><h2>告警事件</h2></div>
							<el-tag :type="activeAlertCount ? 'danger' : 'success'" effect="dark">{{ activeAlertCount }} 个活动</el-tag>
						</div>
						<div class="alert-event-list">
							<div v-for="event in alertEvents" :key="event.id" class="alert-event" :class="`is-${event.status}`">
								<div class="alert-event__identity">
									<span><Warning v-if="event.status === 'active'" /><CircleCheck v-else /></span>
									<div><strong>{{ event.rule.name }}</strong><small>{{ formatTime(event.started_at) }}</small></div>
								</div>
								<div class="alert-event__value"><span>触发 {{ event.trigger_value }}%</span><strong>{{ event.last_value }}%</strong></div>
								<div class="alert-event__actions">
									<el-button v-if="event.status === 'active' && !event.acknowledged_at" link @click="acknowledgeAlert(event)">确认</el-button>
									<el-tag v-else-if="event.acknowledged_at" size="small" type="info">{{ event.acknowledged_by }} 已确认</el-tag>
									<el-button link :loading="analysisLoading" @click="analyzeAlert(event)">AI 分析</el-button>
								</div>
							</div>
							<el-empty v-if="!alertEvents.length" :image-size="64" description="暂无告警事件" />
						</div>
					</article>
				</div>
				<article v-if="alertAnalysis" class="assistant-panel alert-analysis-panel">
					<div class="assistant-panel__head"><div><span class="panel-index">AI</span><h2>故障分析</h2></div></div>
					<pre class="assistant-code assistant-code--analysis">{{ formatJson(alertAnalysis.analysis || alertAnalysis) }}</pre>
				</article>
			</section>

			<section v-else class="assistant-grid assistant-grid--runbooks">
				<article class="assistant-panel runbook-composer">
					<div class="assistant-panel__head"><div><span class="panel-index">01</span><h2>生成 Runbook</h2></div></div>
					<el-input v-model="runbookPrompt" type="textarea" :rows="7" maxlength="2000" show-word-limit placeholder="描述诊断目标和允许的变更条件" />
					<el-button type="primary" :icon="Guide" :loading="runbookLoading" :disabled="!provider.available" @click="generateRunbook">生成多步骤计划</el-button>
					<div class="runbook-list">
						<button v-for="item in runbooks" :key="item.id" :class="{ 'is-active': item.id === selectedRunbookId }" @click="selectedRunbookId = item.id; confirmationToken = ''">
							<span><strong>{{ item.title }}</strong><small>{{ formatTime(item.created_at) }}</small></span>
							<em :class="`is-${item.status}`">{{ runbookStatusLabels[item.status] || item.status }}</em>
						</button>
						<el-empty v-if="!runbooks.length" :image-size="64" description="暂无 Runbook" />
					</div>
				</article>

				<article class="assistant-panel runbook-detail">
					<template v-if="currentRunbook">
						<div class="assistant-panel__head">
							<div><span class="panel-index">02</span><h2>{{ currentRunbook.title }}</h2></div>
							<el-tag effect="dark">{{ runbookStatusLabels[currentRunbook.status] || currentRunbook.status }}</el-tag>
						</div>
						<div class="runbook-steps">
							<div v-for="step in currentRunbook.steps" :key="step.id" class="runbook-step" :class="[`is-${step.status}`, { 'is-current': step.position === currentRunbook.current_step }]">
								<span class="runbook-step__index">{{ String(step.position + 1).padStart(2, '0') }}</span>
								<div class="runbook-step__body">
									<div><strong>{{ step.title }}</strong><em>{{ runbookStatusLabels[step.status] || step.status }}</em></div>
									<code>{{ step.tool_call.tool }}</code>
									<pre v-if="Object.keys(step.output || {}).length">{{ formatJson(step.output) }}</pre>
									<p v-if="step.error">{{ step.error }}</p>
								</div>
								<el-tag :type="step.risk === 'readonly' ? 'success' : 'warning'" size="small">{{ step.risk }}</el-tag>
							</div>
						</div>
						<el-alert v-if="confirmationToken" title="当前步骤会修改系统。确认只在本会话中有效，确认后仍需再次点击执行。" type="warning" :closable="false" show-icon />
						<div class="assistant-panel__actions runbook-actions">
							<el-button v-if="confirmationToken" type="warning" :icon="Key" :loading="runbookLoading" @click="confirmRunbook">确认变更步骤</el-button>
							<el-button type="primary" :icon="VideoPlay" :loading="runbookLoading" :disabled="['completed', 'cancelled'].includes(currentRunbook.status)" @click="advanceRunbook">执行当前步骤</el-button>
							<el-button v-if="currentRunbook.status === 'failed'" :loading="runbookLoading" @click="retryRunbook">重试</el-button>
							<el-button v-if="currentRunbook.status === 'failed'" :loading="runbookLoading" @click="skipRunbook">跳过只读步骤</el-button>
							<el-button type="danger" plain :disabled="['completed', 'cancelled'].includes(currentRunbook.status)" @click="cancelRunbook">取消</el-button>
						</div>
					</template>
					<el-empty v-else :image-size="72" description="请选择 Runbook" />
				</article>
			</section>
		</main>

		<el-dialog v-model="alertDialog" title="新建指标告警规则" width="min(560px, 94vw)" class="assistant-dialog">
			<el-form :model="alertForm" label-position="top">
				<el-form-item label="规则名称"><el-input v-model="alertForm.name" maxlength="128" /></el-form-item>
				<div class="alert-form-grid">
					<el-form-item label="监控指标">
						<el-select v-model="alertForm.metric"><el-option v-for="(label, key) in metricLabels" :key="key" :label="label" :value="key" /></el-select>
					</el-form-item>
					<el-form-item label="比较符"><el-select v-model="alertForm.operator"><el-option label="大于等于" value="gte" /><el-option label="小于等于" value="lte" /></el-select></el-form-item>
					<el-form-item label="触发阈值"><el-input-number v-model="alertForm.threshold" :min="0" :max="100" /></el-form-item>
					<el-form-item label="恢复阈值"><el-input-number v-model="alertForm.recovery_threshold" :min="0" :max="100" /></el-form-item>
					<el-form-item label="连续命中"><el-input-number v-model="alertForm.consecutive_hits" :min="1" :max="60" /></el-form-item>
					<el-form-item label="立即启用"><el-switch v-model="alertForm.enabled" /></el-form-item>
				</div>
			</el-form>
			<template #footer><el-button @click="alertDialog = false">取消</el-button><el-button type="primary" :loading="alertSaving" @click="createAlertRule">创建规则</el-button></template>
		</el-dialog>
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
import {
	assistantRequest,
	type AlertEvent,
	type AlertRule,
	type AnalysisResult,
	type AssistantItemsResponse,
	type AssistantPlan,
	type AssistantPlanResponse,
	type AssistantStatusResponse,
	type MetricSample,
	type Runbook,
	type RunbookResponse,
} from '/@/api/system/assistant';
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
const operationPlan = ref<AssistantPlan | null>(null);
const operationResult = ref<unknown>(null);
const planLoading = ref(false);
const executionLoading = ref(false);
const analysisMode = ref('logs');
const analysisOptions = [
	{ label: '日志', value: 'logs' },
	{ label: '命令输出', value: 'output' },
	{ label: '配置快照', value: 'config' },
	{ label: '知识问答', value: 'knowledge' },
];
const logsInput = ref('[\n  { "service": "sshd", "message": "Failed password for root" }\n]');
const outputInput = ref('');
const snapshotId = ref<number | null>(null);
const knowledgeQuestion = ref('如何安全排查 nginx 服务启动失败？');
const analysisResult = ref<AnalysisResult | null>(null);
const analysisLoading = ref(false);
const metricSamples = ref<MetricSample[]>([]);
const alertRules = ref<AlertRule[]>([]);
const alertEvents = ref<AlertEvent[]>([]);
const alertDialog = ref(false);
const alertSaving = ref(false);
const alertAnalysis = ref<AnalysisResult | null>(null);
const alertForm = reactive({
	name: '根文件系统使用率过高', metric: 'root_percent', operator: 'gte',
	threshold: 85, recovery_threshold: 75, consecutive_hits: 3, enabled: true,
});
const activeAlertCount = computed(() => alertEvents.value.filter((item) => item.status === 'active').length);
const runbookPrompt = ref('检查 nginx 服务状态和 80 端口；必要时重启 nginx');
const runbooks = ref<Runbook[]>([]);
const selectedRunbookId = ref<number | null>(null);
const confirmationToken = ref('');
const runbookLoading = ref(false);
const currentRunbook = computed(() => runbooks.value.find((item) => item.id === selectedRunbookId.value) || null);
const latestMetric = computed(() => metricSamples.value[metricSamples.value.length - 1] || {});
const recentMetricSamples = computed(() => metricSamples.value.slice(-20).reverse());
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
			assistantRequest<AssistantStatusResponse>('/system/ai/status'),
			assistantRequest<AssistantItemsResponse<MetricSample>>('/system/monitoring/samples', 'get', undefined, { hours: 24, limit: 500 }),
			assistantRequest<AssistantItemsResponse<AlertRule>>('/system/monitoring/alert-rules'),
			assistantRequest<AssistantItemsResponse<AlertEvent>>('/system/monitoring/alert-events', 'get', undefined, { limit: 100 }),
			assistantRequest<AssistantItemsResponse<Runbook>>('/system/ai/runbooks'),
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
		const response = await assistantRequest<AssistantPlanResponse>('/system/ai/plans', 'post', {
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
		const response = await assistantRequest<AssistantPlanResponse>(
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
	let logs: unknown[];
	try {
		logs = JSON.parse(logsInput.value);
		if (!Array.isArray(logs)) throw new Error('logs must be an array');
	} catch (error) {
		return ElMessage.warning('请输入有效的 JSON 日志数组');
	}
	analysisLoading.value = true;
	try {
		analysisResult.value = await assistantRequest<AnalysisResult>('/system/ai/analyze/logs', 'post', { logs });
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
		analysisResult.value = await assistantRequest<AnalysisResult>('/system/ai/explain-output', 'post', {
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
		analysisResult.value = await assistantRequest<AnalysisResult>('/system/ai/review-config', 'post', {
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
		analysisResult.value = await assistantRequest<AnalysisResult>('/system/ai/knowledge', 'post', {
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

const toggleAlertRule = async (rule: AlertRule, enabled: string | number | boolean) => {
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

const acknowledgeAlert = async (event: AlertEvent) => {
	try {
		await assistantRequest(`/system/monitoring/alert-events/${event.id}/acknowledge`, 'post');
		ElMessage.success('告警已确认，等待指标恢复');
		await loadWorkspace();
	} catch (error) {
		console.error('acknowledge alert failed:', error);
	}
};

const analyzeAlert = async (event: AlertEvent) => {
	analysisLoading.value = true;
	try {
		alertAnalysis.value = await assistantRequest<AnalysisResult>(
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
		const response = await assistantRequest<RunbookResponse>('/system/ai/runbooks/generate', 'post', {
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

<style lang="scss">
@use './tech-assistant.scss';
</style>
