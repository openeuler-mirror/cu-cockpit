<template>
	<div class="config-management" v-loading="loading">
		<section class="config-management-panel">
			<div class="config-panel__head">
				<div>
					<h2 class="config-panel__title">时间与安全策略</h2>
					<div class="config-panel__meta">NTP SOURCES · SELINUX RUNTIME</div>
				</div>
				<el-button class="config-action" :icon="Refresh" :loading="loading" @click="loadAll">刷新</el-button>
			</div>
			<div class="config-system-grid">
				<article class="config-system-unit">
					<div class="config-system-unit__head">
						<span class="config-system-unit__icon is-ntp"><el-icon><Clock /></el-icon></span>
						<div>
							<h3>NTP 时间同步</h3>
							<span>chronyd · {{ overview.ntp.service_state || 'unknown' }}</span>
						</div>
						<span class="config-state-chip" :class="{ 'is-active': overview.ntp.service_state === 'active' }">
							{{ overview.ntp.service_state === 'active' ? '运行中' : '未运行' }}
						</span>
					</div>
					<div class="config-fact-row">
						<span>同步参考</span><strong>{{ overview.ntp.tracking.reference_id || '—' }}</strong>
					</div>
					<div class="config-source-list">
						<span v-for="source in overview.ntp.sources" :key="`${source.mode}-${source.address}`">
							{{ source.mode }} · {{ source.address }}
						</span>
						<span v-if="!overview.ntp.sources.length">未检测到 NTP 源</span>
					</div>
					<div class="config-system-unit__actions">
						<small>{{ overview.ntp.enabled ? '开机启用' : '开机禁用' }}</small>
						<el-button class="config-action" :icon="Edit" :disabled="!isAdmin" @click="openNtpDialog">管理 NTP</el-button>
					</div>
				</article>

				<article class="config-system-unit">
					<div class="config-system-unit__head">
						<span class="config-system-unit__icon is-security"><el-icon><Lock /></el-icon></span>
						<div>
							<h3>SELinux</h3>
							<span>配置 · {{ overview.selinux.configured.selinux || 'unknown' }}</span>
						</div>
						<span class="config-state-chip" :class="{ 'is-warning': overview.selinux.runtime === 'Disabled' }">
							{{ overview.selinux.runtime || 'Unavailable' }}
						</span>
					</div>
					<div class="config-selinux-state">
						<strong>{{ overview.selinux.runtime || 'Unavailable' }}</strong>
						<span>{{ selinuxDescription }}</span>
					</div>
					<div class="config-system-unit__actions">
						<small>{{ overview.selinux.configured.selinuxtype || 'targeted' }} policy</small>
						<el-button
							class="config-action"
							:disabled="!isAdmin || overview.selinux.runtime === 'Disabled'"
							@click="toggleSelinux"
						>
							切换运行态
						</el-button>
					</div>
				</article>
			</div>
		</section>

		<section class="config-management-panel">
			<div class="config-panel__head config-management-head">
				<div>
					<h2 class="config-panel__title">用户与组</h2>
					<div class="config-panel__meta">POSIX ACCOUNT · GROUP MEMBERSHIP · LOCK STATE</div>
				</div>
				<div class="config-management-tools">
					<el-input v-model="accountSearch" clearable placeholder="搜索用户或组" :prefix-icon="Search" />
					<el-switch v-model="showSystemAccounts" active-text="系统账户" />
					<el-button class="config-action" :icon="Plus" :disabled="!isAdmin" @click="userDialog = true">新建用户</el-button>
					<el-button class="config-action" :icon="Plus" :disabled="!isAdmin" @click="groupDialog = true">新建组</el-button>
				</div>
			</div>
			<el-tabs v-model="accountTab" class="config-management-tabs">
				<el-tab-pane :label="`用户 ${filteredUsers.length}`" name="users">
					<div class="config-table-wrap">
						<el-table :data="filteredUsers" class="config-management-table" max-height="430">
							<el-table-column prop="username" label="用户" min-width="150" />
							<el-table-column prop="uid" label="UID" width="90" class-name="config-col-secondary" />
							<el-table-column prop="shell" label="Shell" min-width="150" class-name="config-col-secondary" />
							<el-table-column label="状态" width="110">
								<template #default="{ row }">
									<span class="config-state-chip" :class="{ 'is-active': row.locked === false, 'is-warning': row.locked !== false }">
										{{ row.locked === false ? '可登录' : '已锁定' }}
									</span>
								</template>
							</el-table-column>
							<el-table-column label="组" min-width="220" class-name="config-col-secondary">
								<template #default="{ row }">{{ row.groups.join(', ') }}</template>
							</el-table-column>
							<el-table-column label="操作" width="190" align="right">
								<template #default="{ row }">
									<el-button link :disabled="!isAdmin || row.uid === 0" @click="toggleUserLock(row)">
										{{ row.locked === false ? '锁定' : '解锁' }}
									</el-button>
									<el-button link type="danger" :disabled="!isAdmin || row.uid === 0" @click="removeUser(row)">删除</el-button>
								</template>
							</el-table-column>
						</el-table>
					</div>
				</el-tab-pane>
				<el-tab-pane :label="`组 ${filteredGroups.length}`" name="groups">
					<div class="config-table-wrap">
						<el-table :data="filteredGroups" class="config-management-table" max-height="430">
							<el-table-column prop="name" label="组" min-width="180" />
							<el-table-column prop="gid" label="GID" width="100" />
							<el-table-column label="成员" min-width="280" class-name="config-col-secondary">
								<template #default="{ row }">{{ row.members.join(', ') || '—' }}</template>
							</el-table-column>
							<el-table-column label="操作" width="100" align="right">
								<template #default="{ row }">
									<el-button link type="danger" :disabled="!isAdmin || row.gid === 0" @click="removeGroup(row)">删除</el-button>
								</template>
							</el-table-column>
						</el-table>
					</div>
				</el-tab-pane>
			</el-tabs>
		</section>

		<section class="config-management-panel">
			<div class="config-panel__head">
				<div>
					<h2 class="config-panel__title">变更记录与快照</h2>
					<div class="config-panel__meta">AUDIT TRAIL · UNIFIED DIFF · SAFE ROLLBACK</div>
				</div>
				<span class="config-access" :class="{ 'is-admin': isAdmin }">{{ isAdmin ? '审计可见' : '需要管理员权限' }}</span>
			</div>
			<el-tabs v-model="historyTab" class="config-management-tabs">
				<el-tab-pane :label="`操作审计 ${audits.length}`" name="audits">
					<div class="config-table-wrap">
						<el-table :data="audits" class="config-management-table" max-height="390" empty-text="暂无可见审计">
							<el-table-column label="时间" min-width="170"><template #default="{ row }">{{ formatTime(row.created_at) }}</template></el-table-column>
							<el-table-column prop="actor" label="操作者" min-width="110" />
							<el-table-column prop="action" label="动作" min-width="150" />
							<el-table-column prop="target" label="目标" min-width="220" class-name="config-col-secondary" />
							<el-table-column label="结果" width="100"><template #default="{ row }"><span class="config-state-chip" :class="{ 'is-active': row.success, 'is-warning': !row.success }">{{ row.success ? '成功' : '失败' }}</span></template></el-table-column>
						</el-table>
					</div>
				</el-tab-pane>
				<el-tab-pane :label="`配置快照 ${snapshots.length}`" name="snapshots">
					<div class="config-table-wrap">
						<el-table :data="snapshots" class="config-management-table" max-height="390" empty-text="暂无配置快照">
							<el-table-column label="时间" min-width="170"><template #default="{ row }">{{ formatTime(row.created_at) }}</template></el-table-column>
							<el-table-column prop="target" label="配置目标" min-width="150" />
							<el-table-column prop="reason" label="原因" min-width="220" class-name="config-col-secondary" />
							<el-table-column prop="actor" label="操作者" min-width="110" />
							<el-table-column label="操作" width="160" align="right">
								<template #default="{ row }">
									<el-button link @click="showSnapshotDiff(row)">差异</el-button>
									<el-button link type="warning" :disabled="!isAdmin" @click="rollbackSnapshot(row)">回滚</el-button>
								</template>
							</el-table-column>
						</el-table>
					</div>
				</el-tab-pane>
			</el-tabs>
		</section>

		<el-dialog v-model="ntpDialog" title="管理 NTP" width="min(620px, 94vw)" class="config-management-dialog">
			<el-form label-position="top">
				<el-form-item label="chronyd 服务">
					<el-switch v-model="ntpForm.enabled" active-text="启用" inactive-text="停用" />
				</el-form-item>
				<div class="config-source-editor">
					<div v-for="(source, index) in ntpForm.sources" :key="index" class="config-source-editor__row">
						<el-select v-model="source.mode"><el-option label="Server" value="server" /><el-option label="Pool" value="pool" /></el-select>
						<el-input v-model="source.address" placeholder="NTP 主机或 IP" />
						<el-checkbox v-model="source.iburst">iburst</el-checkbox>
						<el-button :icon="Delete" circle :disabled="ntpForm.sources.length === 1" @click="ntpForm.sources.splice(index, 1)" />
					</div>
				</div>
				<el-button class="config-action" :icon="Plus" :disabled="ntpForm.sources.length >= 8" @click="addNtpSource">添加源</el-button>
			</el-form>
			<template #footer><el-button @click="ntpDialog = false">取消</el-button><el-button type="primary" :loading="saving" @click="saveNtp">保存并应用</el-button></template>
		</el-dialog>

		<el-dialog v-model="userDialog" title="新建系统用户" width="min(500px, 94vw)" class="config-management-dialog">
			<el-form label-position="top">
				<el-form-item label="用户名"><el-input v-model="userForm.username" placeholder="小写字母、数字、_、-" /></el-form-item>
				<el-form-item label="登录 Shell"><el-select v-model="userForm.shell"><el-option v-for="shell in accounts.shells" :key="shell" :label="shell" :value="shell" /></el-select></el-form-item>
				<el-form-item label="主组（可选）"><el-select v-model="userForm.primary_group" clearable filterable><el-option v-for="group in accounts.groups" :key="group.name" :label="group.name" :value="group.name" /></el-select></el-form-item>
			</el-form>
			<template #footer><el-button @click="userDialog = false">取消</el-button><el-button type="primary" :loading="saving" @click="submitUser">创建锁定用户</el-button></template>
		</el-dialog>

		<el-dialog v-model="groupDialog" title="新建系统组" width="min(440px, 94vw)" class="config-management-dialog">
			<el-form label-position="top"><el-form-item label="组名"><el-input v-model="groupName" placeholder="小写字母、数字、_、-" /></el-form-item></el-form>
			<template #footer><el-button @click="groupDialog = false">取消</el-button><el-button type="primary" :loading="saving" @click="submitGroup">创建组</el-button></template>
		</el-dialog>

		<el-drawer v-model="diffDrawer" class="config-drawer" title="配置差异" direction="rtl" size="min(720px, 96vw)">
			<div class="config-diff-view"><pre>{{ snapshotDiff || '当前配置与快照无差异' }}</pre></div>
		</el-drawer>
	</div>
</template>

<script setup lang="ts" name="configManagementCenter">
import { computed, onMounted, reactive, ref } from 'vue';
import { Clock, Delete, Edit, Lock, Plus, Refresh, Search } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { storeToRefs } from 'pinia';
import {
	createSystemGroup,
	createSystemUser,
	deleteSystemGroup,
	deleteSystemUser,
	getConfigCenterAccounts,
	getConfigCenterOverview,
	getConfigSnapshots,
	getOperationAudits,
	getSnapshotDiff,
	rollbackConfigSnapshot,
	setSelinuxMode,
	updateNtp,
	updateSystemUser,
} from '/@/api/system/configCenter';
import type {
	AccountData,
	AuditItem,
	ConfigCenterOverview,
	NtpSource,
	SnapshotItem,
	SystemGroup,
	SystemUser,
} from '/@/api/system/configCenter';
import { userPermissiom } from '/@/stores/userPermissiom';

const permissionStore = userPermissiom();
const { u_Permission } = storeToRefs(permissionStore);
const isAdmin = computed(() => u_Permission.value === 'root');
const loading = ref(false);
const saving = ref(false);
const accountTab = ref('users');
const historyTab = ref('audits');
const accountSearch = ref('');
const showSystemAccounts = ref(false);
const ntpDialog = ref(false);
const userDialog = ref(false);
const groupDialog = ref(false);
const diffDrawer = ref(false);
const snapshotDiff = ref('');
const groupName = ref('');

const overview = reactive<ConfigCenterOverview>({
	ntp: { service_state: '', enabled: false, sources: [], tracking: {} },
	selinux: { runtime: '', configured: {} },
	account_summary: { users: 0, groups: 0, login_shell_users: 0 },
});
const accounts = reactive<AccountData>({ users: [], groups: [], shells: [] });
const audits = ref<AuditItem[]>([]);
const snapshots = ref<SnapshotItem[]>([]);
const ntpForm = reactive<{ enabled: boolean; sources: NtpSource[] }>({ enabled: false, sources: [] });
const userForm = reactive({ username: '', shell: '/bin/bash', primary_group: '' });

const selinuxDescription = computed(() => {
	if (overview.selinux.runtime === 'Disabled') return '启动配置已禁用，运行时无法切换';
	return overview.selinux.runtime === 'Enforcing' ? '策略正在强制执行' : '策略仅记录不拦截';
});

const filteredUsers = computed(() => {
	const keyword = accountSearch.value.trim().toLowerCase();
	return accounts.users.filter((item) => (showSystemAccounts.value || !item.system)
		&& (!keyword || item.username.toLowerCase().includes(keyword) || item.groups.some((group) => group.toLowerCase().includes(keyword))));
});

const filteredGroups = computed(() => {
	const keyword = accountSearch.value.trim().toLowerCase();
	return accounts.groups.filter((item) => (showSystemAccounts.value || !item.system)
		&& (!keyword || item.name.toLowerCase().includes(keyword) || item.members.some((member) => member.toLowerCase().includes(keyword))));
});

const loadAll = async () => {
	loading.value = true;
	try {
		const [overviewData, accountData] = await Promise.all([getConfigCenterOverview(), getConfigCenterAccounts()]);
		Object.assign(overview, overviewData);
		Object.assign(accounts, accountData);
		if (isAdmin.value) {
			const [auditData, snapshotData] = await Promise.all([getOperationAudits('', 100), getConfigSnapshots('', 100)]);
			audits.value = auditData.items.filter((item) => ['config_center', 'config', 'foundation'].includes(item.module));
			snapshots.value = snapshotData.items;
		} else {
			audits.value = [];
			snapshots.value = [];
		}
	} catch (error) {
		ElMessage.error('配置中心数据加载失败');
		console.error('load config center failed:', error);
	} finally {
		loading.value = false;
	}
};

const openNtpDialog = () => {
	ntpForm.enabled = overview.ntp.enabled;
	ntpForm.sources = overview.ntp.sources.map((item) => ({ ...item }));
	if (!ntpForm.sources.length) ntpForm.sources.push({ mode: 'server', address: '', iburst: true });
	ntpDialog.value = true;
};
const addNtpSource = () => ntpForm.sources.push({ mode: 'server', address: '', iburst: true });
const saveNtp = async () => runSaving(async () => {
	await updateNtp({ enabled: ntpForm.enabled, sources: ntpForm.sources });
	ntpDialog.value = false;
	ElMessage.success('NTP 配置已应用');
});

const toggleSelinux = async () => {
	const nextMode = overview.selinux.runtime === 'Enforcing' ? 'permissive' : 'enforcing';
	await ElMessageBox.confirm(`确认切换为 ${nextMode}？`, 'SELinux 运行态', { type: 'warning' });
	await runSaving(async () => {
		await setSelinuxMode(nextMode);
		ElMessage.success('SELinux 运行态已更新');
	});
};

const submitUser = async () => runSaving(async () => {
	await createSystemUser({ ...userForm, primary_group: userForm.primary_group || undefined });
	userDialog.value = false;
	userForm.username = '';
	ElMessage.success('锁定用户已创建');
});

const toggleUserLock = async (user: SystemUser) => runSaving(async () => {
	await updateSystemUser(user.username, { locked: user.locked === false });
	ElMessage.success(user.locked === false ? '用户已锁定' : '用户已解锁');
});

const removeUser = async (user: SystemUser) => {
	await ElMessageBox.confirm(`删除用户 ${user.username} 及其主目录？`, '删除系统用户', { type: 'warning' });
	await runSaving(async () => {
		await deleteSystemUser(user.username, true);
		ElMessage.success('用户已删除');
	});
};

const submitGroup = async () => runSaving(async () => {
	await createSystemGroup(groupName.value);
	groupDialog.value = false;
	groupName.value = '';
	ElMessage.success('组已创建');
});

const removeGroup = async (group: SystemGroup) => {
	await ElMessageBox.confirm(`删除组 ${group.name}？`, '删除系统组', { type: 'warning' });
	await runSaving(async () => {
		await deleteSystemGroup(group.name);
		ElMessage.success('组已删除');
	});
};

const showSnapshotDiff = async (snapshot: SnapshotItem) => {
	const response = await getSnapshotDiff(snapshot.id);
	snapshotDiff.value = response.diff;
	diffDrawer.value = true;
};

const rollbackSnapshot = async (snapshot: SnapshotItem) => {
	await ElMessageBox.confirm(`确认回滚 ${snapshot.target} 到所选快照？`, '配置回滚', { type: 'warning' });
	await runSaving(async () => {
		await rollbackConfigSnapshot(snapshot.id);
		ElMessage.success('配置已回滚');
	});
};

const runSaving = async (operation: () => Promise<void>) => {
	saving.value = true;
	try {
		await operation();
		await loadAll();
	} catch (error) {
		if (error !== 'cancel' && error !== 'close') console.error('config center operation failed:', error);
	} finally {
		saving.value = false;
	}
};

const formatTime = (value: string) => new Intl.DateTimeFormat('zh-CN', {
	year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit',
}).format(new Date(value));

onMounted(async () => {
	await permissionStore.refreshUserPermission();
	await loadAll();
});
</script>