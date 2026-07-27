import request from '/@/utils/request';

export interface ProcessItem {
	pid: number;
	ppid: number;
	user: string;
	stat: string;
	status: string;
	cpu: number;
	memory: number;
	elapsed_seconds: number;
	name: string;
	command: string;
	protected: boolean;
	protected_reason: string;
}

export interface ProcessDetail extends ProcessItem {
	command_line: string;
	cwd: string;
	threads: number;
	vm_size: string;
	vm_rss: string;
	context_switches: { voluntary: string; nonvoluntary: string };
	file_descriptors: number | null;
}

export const getProcesses = (params: { search?: string; sort?: string; order?: string; limit?: number }) => request({
	url: '/system/processes',
	method: 'get',
	params,
});

export const getProcessDetail = (pid: number): Promise<{ item: ProcessDetail }> => request({
	url: `/system/processes/${pid}`,
	method: 'get',
});

export const signalProcess = (pid: number, signal: 'TERM' | 'KILL') => request({
	url: `/system/processes/${pid}/signal`,
	method: 'post',
	data: { signal, confirm_pid: pid },
});