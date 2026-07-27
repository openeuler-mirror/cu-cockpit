import request from '/@/utils/request';

export interface CronJob {
	id: number;
	name: string;
	schedule: string;
	command: string;
	enabled: boolean;
	created_by: string;
	updated_by: string;
	created_at: string;
	updated_at: string;
	last_run_at: string | null;
}

export interface CronExecution {
	id: number;
	job_id: number | null;
	job_name: string;
	actor: string;
	manual: boolean;
	status: 'running' | 'success' | 'failed' | 'timeout';
	started_at: string;
	finished_at: string | null;
	returncode: number | null;
	stdout: string;
	stderr: string;
	duration_ms: number;
}

export const getCronJobs = (): Promise<{ items: CronJob[]; allowed_commands: string[] }> => request({
	url: '/system/cron/jobs',
	method: 'get',
});

export const getCronHistory = (jobId?: number, limit = 100): Promise<{ items: CronExecution[] }> => request({
	url: '/system/cron/history',
	method: 'get',
	params: { job_id: jobId, limit },
});

export const createCronJob = (data: { name: string; schedule: string; command: string; enabled: boolean }) => request({
	url: '/system/cron/jobs/create',
	method: 'post',
	data,
});

export const updateCronJob = (id: number, data: Partial<{ name: string; schedule: string; command: string; enabled: boolean }>) => request({
	url: `/system/cron/jobs/${id}/update`,
	method: 'post',
	data,
});

export const deleteCronJob = (id: number) => request({
	url: `/system/cron/jobs/${id}/delete`,
	method: 'post',
	data: {},
});

export const runCronJob = (id: number): Promise<{ execution: CronExecution }> => request({
	url: `/system/cron/jobs/${id}/run`,
	method: 'post',
	data: {},
});