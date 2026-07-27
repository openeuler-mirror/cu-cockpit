import request from '/@/utils/request';

export interface SystemIdentity {
	username: string;
	role: 'admin' | 'viewer';
	uid: number | null;
	is_admin: boolean;
	permissions: string[];
}

export const getSystemContext = (): Promise<{ identity: SystemIdentity }> => {
	return request({
		url: '/system/context',
		method: 'get',
	});
};

export const getSystemCapabilities = () => {
	return request({
		url: '/system/capabilities',
		method: 'get',
	});
};