import request from '/@/utils/request';

export interface NtpSource {
	mode: 'server' | 'pool';
	address: string;
	iburst: boolean;
}

export interface NtpStatus {
	service_state: string;
	enabled: boolean;
	sources: NtpSource[];
	tracking: Record<string, string>;
}

export interface SelinuxStatus {
	runtime: string;
	configured: Record<string, string>;
}

export interface ConfigCenterOverview {
	ntp: NtpStatus;
	selinux: SelinuxStatus;
	account_summary: {
		users: number;
		groups: number;
		login_shell_users: number;
	};
}

export interface SystemUser {
	username: string;
	uid: number;
	gid: number;
	home: string;
	shell: string;
	gecos: string;
	locked: boolean | null;
	system: boolean;
	groups: string[];
}

export interface SystemGroup {
	name: string;
	gid: number;
	members: string[];
	system: boolean;
}

export interface AccountData {
	users: SystemUser[];
	groups: SystemGroup[];
	shells: string[];
}

export interface AuditItem {
	id: number;
	created_at: string;
	actor: string;
	module: string;
	action: string;
	target: string;
	success: boolean;
	message: string;
}

export interface SnapshotItem {
	id: number;
	created_at: string;
	actor: string;
	module: string;
	target: string;
	path: string;
	checksum: string;
	reason: string;
}

export const getConfigCenterOverview = (): Promise<ConfigCenterOverview> => request({
	url: '/system/config-center/overview',
	method: 'get',
});

export const getConfigCenterAccounts = (): Promise<AccountData> => request({
	url: '/system/config-center/accounts',
	method: 'get',
});

export const updateNtp = (data: { enabled: boolean; sources: NtpSource[] }) => request({
	url: '/system/config-center/ntp/update',
	method: 'post',
	data,
});

export const createSystemUser = (data: { username: string; shell: string; primary_group?: string }) => request({
	url: '/system/config-center/users',
	method: 'post',
	data,
});

export const updateSystemUser = (username: string, data: { locked?: boolean; shell?: string; add_groups?: string[] }) => request({
	url: `/system/config-center/users/${encodeURIComponent(username)}/update`,
	method: 'post',
	data,
});

export const deleteSystemUser = (username: string, removeHome = false) => request({
	url: `/system/config-center/users/${encodeURIComponent(username)}/delete`,
	method: 'post',
	data: { remove_home: removeHome },
});

export const createSystemGroup = (name: string) => request({
	url: '/system/config-center/groups',
	method: 'post',
	data: { name },
});

export const deleteSystemGroup = (name: string) => request({
	url: `/system/config-center/groups/${encodeURIComponent(name)}/delete`,
	method: 'post',
	data: {},
});

export const setSelinuxMode = (mode: 'enforcing' | 'permissive') => request({
	url: '/system/config-center/selinux/mode',
	method: 'post',
	data: { mode },
});

export const getOperationAudits = (module = '', limit = 100): Promise<{ items: AuditItem[] }> => request({
	url: '/system/audits',
	method: 'get',
	params: { module, limit },
});

export const getConfigSnapshots = (target = '', limit = 100): Promise<{ items: SnapshotItem[]; targets: Record<string, string> }> => request({
	url: '/system/snapshots',
	method: 'get',
	params: { target, limit },
});

export const getSnapshotDiff = (id: number): Promise<{ id: number; target: string; diff: string }> => request({
	url: `/system/snapshots/${id}/diff`,
	method: 'get',
});

export const rollbackConfigSnapshot = (id: number) => request({
	url: `/system/snapshots/${id}/rollback`,
	method: 'post',
	data: {},
});