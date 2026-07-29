<template>
	<div class="tech-cron">
		<header class="cron-hud">
			<div class="cron-identity">
				<span class="cron-identity__mark"><el-icon><Timer /></el-icon></span>
				<div><h1 class="cron-title">定时任务</h1><div class="cron-kicker">CRON SCHEDULER · SAFE ARGV EXECUTION</div></div>
			</div>
			<div class="cron-hud__actions">
				<span class="cron-service-state" :class="{ 'is-active': cronAvailable }"><span></span>{{ cronAvailable ? 'CROND 在线' : 'CROND 不可用' }}</span>
				<el-button class="cron-action" :icon="Refresh" :loading="loading" @click="loadData">刷新</el-button>
			</div>
		</header>

		<section class="cron-summary">
			<div v-for="item in summaryItems" :key="item.label" class="cron-summary__item" :style="{ '--summary-accent': item.color }">
				<span class="cron-summary__icon"><el-icon><component :is="item.icon" /></el-icon></span>
				<div><span>{{ item.label }}</span><strong>{{ item.value }}</strong></div>
			</div>
		</section>

		<section class="cron-panel" v-loading="loading">
			<div class="cron-panel__head">
				<div><h2>调度任务</h2><span>仅允许固定安全命令，不经过 shell</span></div>
				<div class="cron-toolbar">
					<el-input v-model="search" :prefix-icon="Search" clearable placeholder="搜索名称或命令" />
					<el-button class="cron-action" :icon="Document" @click="openHistory()">执行历史</el-button>
					<el-button class="cron-action cron-action--primary" :icon="Plus" :disabled="!isAdmin || !cronAvailable" @click="openCreate">新建任务</el-button>
				</div>
			</div>
			<div class="cron-table-wrap">
				<el-table :data="filteredJobs" class="cron-table" empty-text="暂无平台定时任务">
					<el-table-column prop="name" label="任务" min-width="180">
						<template #default="{ row }"><div class="cron-job-name"><span><el-icon><Clock /></el-icon></span><strong>{{ row.name }}</strong></div></template>
					</el-table-column>
					<el-table-column prop="schedule" label="Cron 表达式" min-width="150"><template #default="{ row }"><code class="cron-code">{{ row.schedule }}</code></template></el-table-column>
					<el-table-column prop="command" label="安全命令" min-width="230" class-name="cron-col-secondary"><template #default="{ row }"><code class="cron-command">{{ row.command }}</code></template></el-table-column>
					<el-table-column label="最近执行" min-width="165" class-name="cron-col-secondary"><template #default="{ row }">{{ row.last_run_at ? formatTime(row.last_run_at) : '尚未执行' }}</template></el-table-column>
					<el-table-column label="状态" width="100">
						<template #default="{ row }"><el-switch :model-value="row.enabled" :disabled="!isAdmin || saving" @change="toggleJob(row, $event)" /></template>
					</el-table-column>
					<el-table-column label="操作" width="220" align="right">
						<template #default="{ row }">
							<el-button link :disabled="!isAdmin || saving" @click="runJob(row)">立即执行</el-button>
							<el-button link :disabled="!isAdmin || saving" @click="openEdit(row)">编辑</el-button>
							<el-button link type="danger" :disabled="!isAdmin || saving" @click="removeJob(row)">删除</el-button>
						</template>
					</el-table-column>
				</el-table>
			</div>
		</section>

		<el-dialog v-model="jobDialog" :title="editingId ? '修改定时任务' : '新建定时任务'" width="min(560px, 94vw)" class="cron-dialog">
			<el-form ref="jobFormRef" :model="jobForm" :rules="jobRules" label-position="top">
				<el-form-item label="任务名称" prop="name"><el-input v-model="jobForm.name" maxlength="128" /></el-form-item>
				<el-form-item label="Cron 表达式" prop="schedule"><el-input v-model="jobForm.schedule" placeholder="例如：*/5 * * * *" /></el-form-item>
				<el-form-item label="安全命令" prop="command"><el-input v-model="jobForm.command" placeholder="例如：logger 'health check'" /></el-form-item>
				<div class="cron-command-policy">允许命令：{{ allowedCommands.join(' · ') }}</div>
				<el-form-item label="任务状态"><el-switch v-model="jobForm.enabled" active-text="启用" inactive-text="停用" /></el-form-item>
			</el-form>
			<template #footer><el-button @click="jobDialog = false">取消</el-button><el-button type="primary" :loading="saving" @click="saveJob">保存并同步</el-button></template>
		</el-dialog>

		<el-drawer v-model="historyDrawer" class="cron-history-drawer" title="执行历史" direction="rtl" size="min(760px, 96vw)">
			<div class="cron-history">
				<el-table :data="history" class="cron-table" max-height="430" @row-click="selectedExecution = $event">
					<el-table-column prop="job_name" label="任务" min-width="140" />
					<el-table-column label="触发" width="80"><template #default="{ row }">{{ row.manual ? '手动' : '计划' }}</template></el-table-column>
					<el-table-column label="状态" width="90"><template #default="{ row }"><span class="cron-result" :class="`is-${row.status}`">{{ statusLabel(row.status) }}</span></template></el-table-column>
					<el-table-column label="开始时间" min-width="165"><template #default="{ row }">{{ formatTime(row.started_at) }}</template></el-table-column>
				</el-table>
				<div class="cron-execution-detail" v-if="selectedExecution">
					<div><span>退出码</span><strong>{{ selectedExecution.returncode ?? '—' }}</strong><span>耗时</span><strong>{{ selectedExecution.duration_ms }} ms</strong></div>
					<pre>{{ selectedExecution.stdout || selectedExecution.stderr || '无命令输出' }}</pre>
				</div>
			</div>
		</el-drawer>
	</div>
</template>

<script setup lang="ts" name="cronIndex">
import { computed, nextTick, onMounted, onUnmounted, reactive, ref } from 'vue';
import { Clock, CircleCheck, Document, Plus, Refresh, Search, Timer, WarningFilled } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';
import { storeToRefs } from 'pinia';
import { createCronJob, deleteCronJob, getCronHistory, getCronJobs, runCronJob, updateCronJob } from '/@/api/system/cron';
import type { CronExecution, CronJob } from '/@/api/system/cron';
import { getSystemCapabilities } from '/@/api/system';
import { userPermissiom } from '/@/stores/userPermissiom';
import { useThemeConfig } from '/@/stores/themeConfig';

const permissionStore = userPermissiom();
const { u_Permission } = storeToRefs(permissionStore);
const themeStore = useThemeConfig();
const { themeConfig } = storeToRefs(themeStore);
const isAdmin = computed(() => u_Permission.value === 'root');
const jobs = ref<CronJob[]>([]);
const history = ref<CronExecution[]>([]);
const allowedCommands = ref<string[]>([]);
const loading = ref(false);
const saving = ref(false);
const cronAvailable = ref(false);
const search = ref('');
const jobDialog = ref(false);
const historyDrawer = ref(false);
const editingId = ref<number | null>(null);
const selectedExecution = ref<CronExecution | null>(null);
const jobFormRef = ref<FormInstance>();
const jobForm = reactive({ name: '', schedule: '*/5 * * * *', command: 'true', enabled: true });
const jobRules = reactive<FormRules>({
	name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
	schedule: [{ required: true, message: '请输入五段 Cron 表达式', trigger: 'blur' }],
	command: [{ required: true, message: '请输入安全命令', trigger: 'blur' }],
});

const filteredJobs = computed(() => {
	const keyword = search.value.trim().toLowerCase();
	return jobs.value.filter((item) => !keyword || item.name.toLowerCase().includes(keyword) || item.command.toLowerCase().includes(keyword));
});
const latestExecution = computed(() => history.value[0]);
const summaryItems = computed(() => [
	{ label: '任务总数', value: jobs.value.length, icon: Timer, color: '#22d3ee' },
	{ label: '启用任务', value: jobs.value.filter((item) => item.enabled).length, icon: CircleCheck, color: '#10f5a0' },
	{ label: '最近结果', value: latestExecution.value ? statusLabel(latestExecution.value.status) : '暂无执行', icon: Document, color: '#a855f7' },
	{ label: '安全策略', value: `${allowedCommands.value.length} 个允许命令`, icon: WarningFilled, color: '#ffb020' },
]);

const loadData = async () => {
	loading.value = true;
	try {
		await permissionStore.refreshUserPermission();
		const [jobData, historyData, capabilities] = await Promise.all([getCronJobs(), getCronHistory(undefined, 100), getSystemCapabilities()]);
		jobs.value = jobData.items;
		allowedCommands.value = jobData.allowed_commands;
		history.value = historyData.items;
		cronAvailable.value = Boolean(capabilities.modules?.cron?.available) && !capabilities.modules?.cron?.read_only;
	} catch (error) {
		ElMessage.error('定时任务加载失败');
		console.error('load cron failed:', error);
	} finally {
		loading.value = false;
	}
};

const resetForm = () => Object.assign(jobForm, { name: '', schedule: '*/5 * * * *', command: 'true', enabled: true });
const openCreate = () => { editingId.value = null; resetForm(); jobDialog.value = true; nextTick(() => jobFormRef.value?.clearValidate()); };
const openEdit = (job: CronJob) => { editingId.value = job.id; Object.assign(jobForm, { name: job.name, schedule: job.schedule, command: job.command, enabled: job.enabled }); jobDialog.value = true; nextTick(() => jobFormRef.value?.clearValidate()); };
const saveJob = async () => {
	if (!await jobFormRef.value?.validate().catch(() => false)) return;
	await withSaving(async () => {
		if (editingId.value) await updateCronJob(editingId.value, { ...jobForm });
		else await createCronJob({ ...jobForm });
		jobDialog.value = false;
		ElMessage.success(editingId.value ? '任务已更新' : '任务已创建');
	});
};
const toggleJob = async (job: CronJob, value: string | number | boolean) => withSaving(async () => {
	await updateCronJob(job.id, { enabled: Boolean(value) });
	ElMessage.success(value ? '任务已启用' : '任务已停用');
});
const runJob = async (job: CronJob) => withSaving(async () => {
	const response = await runCronJob(job.id);
	selectedExecution.value = response.execution;
	historyDrawer.value = true;
	ElMessage.success('任务执行成功');
});
const removeJob = async (job: CronJob) => {
	await ElMessageBox.confirm(`删除任务 ${job.name}？执行历史将保留。`, '删除定时任务', { type: 'warning' });
	await withSaving(async () => { await deleteCronJob(job.id); ElMessage.success('任务已删除'); });
};
const openHistory = async (job?: CronJob) => {
	history.value = (await getCronHistory(job?.id, 100)).items;
	selectedExecution.value = history.value[0] || null;
	historyDrawer.value = true;
};
const withSaving = async (operation: () => Promise<void>) => {
	saving.value = true;
	try { await operation(); await loadData(); }
	catch (error) { if (error !== 'cancel' && error !== 'close') console.error('cron operation failed:', error); }
	finally { saving.value = false; }
};
const statusLabel = (status: CronExecution['status']) => ({ running: '运行中', success: '成功', failed: '失败', timeout: '超时' })[status];
const formatTime = (value: string) => new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' }).format(new Date(value));
const mountTechShell = () => document.documentElement.classList.add('theme-tech-dark');
const restoreTechShell = () => { if (!themeConfig.value.isTechTheme) document.documentElement.classList.remove('theme-tech-dark'); };
onMounted(() => { mountTechShell(); loadData(); });
onUnmounted(restoreTechShell);
</script>

<style lang="scss">
@use './tech-cron.scss';
</style>