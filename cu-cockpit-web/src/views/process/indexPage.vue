<template>
	<div class="tech-process">
		<header class="process-hud">
			<div class="process-identity"><span class="process-identity__mark"><el-icon><Cpu /></el-icon></span><div><h1>进程管理</h1><p>PROCESS INSPECTOR · CONTROLLED SIGNALS</p></div></div>
			<div class="process-hud__actions"><span class="process-live"><span></span>实时进程表</span><el-button class="process-action" :icon="Refresh" :loading="loading" @click="loadProcesses()">刷新</el-button></div>
		</header>
		<section class="process-summary">
			<div v-for="item in summaryItems" :key="item.label" class="process-summary__item" :style="{ '--summary-accent': item.color }"><span><el-icon><component :is="item.icon" /></el-icon></span><div><small>{{ item.label }}</small><strong>{{ item.value }}</strong></div></div>
		</section>
		<section class="process-panel" v-loading="loading">
			<div class="process-panel__head">
				<div><h2>进程列表</h2><span>信号操作会重新检查 PID 与保护状态</span></div>
				<div class="process-toolbar">
					<el-input v-model="search" :prefix-icon="Search" clearable placeholder="PID / 用户 / 名称 / 命令" @keyup.enter="queryProcesses" />
					<el-select v-model="sort" @change="queryProcesses"><el-option label="CPU" value="cpu" /><el-option label="内存" value="memory" /><el-option label="PID" value="pid" /><el-option label="运行时间" value="elapsed" /><el-option label="名称" value="name" /></el-select>
					<el-button class="process-action" @click="toggleOrder">{{ order === 'desc' ? '降序' : '升序' }}</el-button>
					<el-button class="process-action process-action--primary" :icon="Search" @click="queryProcesses">查询</el-button>
				</div>
			</div>
			<div class="process-table-wrap">
				<el-table :data="pagedItems" class="process-table" empty-text="未找到匹配进程" @row-dblclick="openDetail">
					<el-table-column prop="pid" label="PID" width="90"><template #default="{ row }"><code>{{ row.pid }}</code></template></el-table-column>
					<el-table-column label="进程" min-width="190"><template #default="{ row }"><div class="process-name"><span :class="{ 'is-protected': row.protected }"><el-icon><Lock v-if="row.protected" /><Operation v-else /></el-icon></span><div><strong>{{ row.name }}</strong><small>{{ row.user }} · PPID {{ row.ppid }}</small></div></div></template></el-table-column>
					<el-table-column label="状态" width="110"><template #default="{ row }"><span class="process-state" :class="`is-${row.status}`">{{ statusLabel(row.status) }}</span></template></el-table-column>
					<el-table-column label="CPU" width="100" align="right"><template #default="{ row }"><strong class="process-metric">{{ row.cpu.toFixed(1) }}%</strong></template></el-table-column>
					<el-table-column label="内存" width="100" align="right"><template #default="{ row }"><strong class="process-metric is-memory">{{ row.memory.toFixed(1) }}%</strong></template></el-table-column>
					<el-table-column label="运行时间" min-width="130" class-name="process-col-secondary"><template #default="{ row }">{{ formatElapsed(row.elapsed_seconds) }}</template></el-table-column>
					<el-table-column prop="command" label="命令" min-width="260" show-overflow-tooltip class-name="process-col-secondary"><template #default="{ row }"><code class="process-command">{{ row.command }}</code></template></el-table-column>
					<el-table-column label="操作" width="180" align="right"><template #default="{ row }"><el-button link @click="openDetail(row)">详情</el-button><el-button link type="warning" :disabled="!isAdmin || row.protected" @click="sendSignal(row, 'TERM')">TERM</el-button><el-button link type="danger" :disabled="!isAdmin || row.protected" @click="sendSignal(row, 'KILL')">KILL</el-button></template></el-table-column>
				</el-table>
			</div>
			<div v-if="items.length" class="process-pagination">
				<el-pagination
					:current-page="processPage"
					:page-size="processPageSize"
					:page-sizes="processPageSizeOptions"
					:pager-count="5"
					:total="items.length"
					layout="total, sizes, prev, pager, next"
					@size-change="onProcessPageSizeChange"
					@current-change="processPage = $event"
				/>
				<span class="process-pagination__page">{{ processPage }} / {{ Math.ceil(items.length / processPageSize) }}</span>
			</div>
		</section>
		<el-drawer v-model="detailDrawer" class="process-detail-drawer" title="进程详情" direction="rtl" size="min(680px, 96vw)">
			<div class="process-detail" v-loading="detailLoading" v-if="detail">
				<div class="process-detail__identity"><span><el-icon><Operation /></el-icon></span><div><h3>{{ detail.name }}</h3><p>PID {{ detail.pid }} · {{ detail.user }} · {{ statusLabel(detail.status) }}</p></div><span class="process-state" :class="`is-${detail.status}`">{{ detail.stat }}</span></div>
				<div class="process-detail-grid"><div v-for="fact in detailFacts" :key="fact.label"><small>{{ fact.label }}</small><strong>{{ fact.value || '—' }}</strong></div></div>
				<div class="process-detail-block"><span>完整命令</span><code>{{ detail.command_line || detail.command }}</code></div>
				<div class="process-detail-block"><span>工作目录</span><code>{{ detail.cwd || '不可读取' }}</code></div>
				<div class="process-detail__actions"><small v-if="detail.protected">{{ detail.protected_reason }}</small><el-button class="process-action" type="warning" :disabled="!isAdmin || detail.protected" @click="sendSignal(detail, 'TERM')">发送 TERM</el-button><el-button class="process-action" type="danger" :disabled="!isAdmin || detail.protected" @click="sendSignal(detail, 'KILL')">发送 KILL</el-button></div>
			</div>
		</el-drawer>
	</div>
</template>

<script setup lang="ts" name="processIndex">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { CircleCheck, Cpu, Lock, Operation, Refresh, Search, Timer, WarningFilled } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { storeToRefs } from 'pinia';
import { getProcessDetail, getProcesses, signalProcess } from '/@/api/system/processes';
import type { ProcessDetail, ProcessItem } from '/@/api/system/processes';
import { userPermissiom } from '/@/stores/userPermissiom';
import { useThemeConfig } from '/@/stores/themeConfig';

const permissionStore = userPermissiom();
const { u_Permission } = storeToRefs(permissionStore);
const themeStore = useThemeConfig();
const { themeConfig } = storeToRefs(themeStore);
const isAdmin = computed(() => u_Permission.value === 'root');
const items = ref<ProcessItem[]>([]);
const summary = ref({ total: 0, running: 0, sleeping: 0, zombie: 0 });
const search = ref('');
const sort = ref('cpu');
const order = ref('desc');
const processPage = ref(1);
const processPageSize = ref(10);
const processPageSizeOptions = [10, 20, 50];
const loading = ref(false);
const detailLoading = ref(false);
const detailDrawer = ref(false);
const detail = ref<ProcessDetail | null>(null);
const summaryItems = computed(() => [
	{ label: '匹配进程', value: summary.value.total, icon: Operation, color: '#22d3ee' },
	{ label: '运行中', value: summary.value.running, icon: CircleCheck, color: '#10f5a0' },
	{ label: '休眠 / 空闲', value: summary.value.sleeping, icon: Timer, color: '#a855f7' },
	{ label: '僵尸进程', value: summary.value.zombie, icon: WarningFilled, color: summary.value.zombie ? '#ff4d6d' : '#ffb020' },
]);
const detailFacts = computed(() => detail.value ? [
	{ label: 'CPU', value: `${detail.value.cpu.toFixed(1)}%` }, { label: '内存', value: `${detail.value.memory.toFixed(1)}%` },
	{ label: 'RSS', value: detail.value.vm_rss }, { label: '虚拟内存', value: detail.value.vm_size },
	{ label: '线程', value: detail.value.threads }, { label: '文件描述符', value: detail.value.file_descriptors },
	{ label: '运行时间', value: formatElapsed(detail.value.elapsed_seconds) }, { label: '父进程', value: detail.value.ppid },
] : []);
const pagedItems = computed(() => { const start = (processPage.value - 1) * processPageSize.value; return items.value.slice(start, start + processPageSize.value); });
const loadProcesses = async () => { loading.value = true; try { await permissionStore.refreshUserPermission(); const response = await getProcesses({ search: search.value, sort: sort.value, order: order.value, limit: 1000 }); items.value = response.items; summary.value = response.summary; processPage.value = Math.min(processPage.value, Math.max(1, Math.ceil(items.value.length / processPageSize.value))); } catch (error) { ElMessage.error('进程列表加载失败'); console.error(error); } finally { loading.value = false; } };
const queryProcesses = () => { processPage.value = 1; return loadProcesses(); };
const onProcessPageSizeChange = (size: number) => { processPageSize.value = size; processPage.value = 1; };
const toggleOrder = () => { order.value = order.value === 'desc' ? 'asc' : 'desc'; queryProcesses(); };
const openDetail = async (item: ProcessItem) => { detailDrawer.value = true; detailLoading.value = true; try { detail.value = (await getProcessDetail(item.pid)).item; } catch (error) { detailDrawer.value = false; ElMessage.warning('进程已经退出或无法读取'); } finally { detailLoading.value = false; } };
const sendSignal = async (item: ProcessItem, signal: 'TERM' | 'KILL') => {
	const effect = signal === 'KILL' ? '立即强制终止，进程无法清理资源' : '请求进程正常退出并清理资源';
	await ElMessageBox.confirm(`向 ${item.name}（PID ${item.pid}）发送 ${signal}？${effect}。`, `${signal} 进程`, { type: signal === 'KILL' ? 'error' : 'warning', confirmButtonText: `发送 ${signal}` });
	await signalProcess(item.pid, signal); ElMessage.success(`已发送 ${signal}`); detailDrawer.value = false; await loadProcesses();
};
const statusLabel = (status: string) => ({ running: '运行', sleeping: '休眠', idle: '空闲', zombie: '僵尸', stopped: '停止', uninterruptible: '不可中断', tracing: '跟踪', dead: '结束', unknown: '未知' })[status] || status;
const formatElapsed = (seconds: number) => { const days = Math.floor(seconds / 86400); const hours = Math.floor(seconds % 86400 / 3600); const minutes = Math.floor(seconds % 3600 / 60); return days ? `${days}天 ${hours}时` : hours ? `${hours}时 ${minutes}分` : `${minutes}分 ${seconds % 60}秒`; };
const mountTechShell = () => document.documentElement.classList.add('theme-tech-dark');
const restoreTechShell = () => { if (!themeConfig.value.isTechTheme) document.documentElement.classList.remove('theme-tech-dark'); };
onMounted(() => { mountTechShell(); loadProcesses(); });
onUnmounted(restoreTechShell);
</script>

<style lang="scss">
@use './tech-process.scss';
</style>