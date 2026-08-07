import request from '/@/utils/request';


export interface AssistantProvider {
	available: boolean;
	model: string;
	reason: string;
}

export interface AssistantToolCall {
	tool: string;
	arguments: Record<string, unknown>;
}

export interface AssistantPlan {
	id: number;
	intent: string;
	summary: string;
	risk: string;
	status: string;
	tool_calls: AssistantToolCall[];
	result?: unknown;
}

export interface MetricSample {
	[key: string]: unknown;
	collected_at: string;
	cpu_percent: number | null;
	memory_percent: number | null;
	root_percent: number | null;
	inode_percent: number | null;
}

export interface AlertRule {
	id: number;
	name: string;
	metric: string;
	operator: string;
	threshold: number;
	consecutive_hits: number;
	enabled: boolean;
}

export interface AlertEvent {
	id: number;
	status: string;
	started_at: string;
	trigger_value: number;
	last_value: number;
	acknowledged_at?: string;
	acknowledged_by?: string;
	rule: { id: number; name: string; metric: string };
}

export interface RunbookStep {
	id: number;
	position: number;
	title: string;
	risk: string;
	status: string;
	tool_call: AssistantToolCall;
	output: Record<string, unknown>;
	error: string;
}

export interface Runbook {
	id: number;
	title: string;
	status: string;
	current_step: number;
	created_at: string;
	steps: RunbookStep[];
}

export interface AnalysisResult {
	truncated?: boolean;
	analysis?: unknown;
	answer?: unknown;
	matches?: Array<{ source: string; score: number }>;
}

export type CommandRisk = 'readonly' | 'change' | 'dangerous';

export interface CommandRiskAssessment {
	risk: CommandRisk;
	reasons: string[];
	commands: string[];
	operators: string[];
	wrappers: string[];
	requires_admin_review: boolean;
}

export interface CommandReviewAnalysis {
	explanation: string;
	arguments: string[];
	effects: string[];
	risks: string[];
	safer_alternative: string;
	verification: string[];
}

export interface CommandReviewResult {
	assessment: CommandRiskAssessment;
	analysis: CommandReviewAnalysis;
	truncated: boolean;
}

export interface AssistantStatusResponse {
	provider: AssistantProvider;
	tools: AssistantToolCall[];
}

export interface AssistantItemsResponse<T> {
	items: T[];
}

export interface AssistantPlanResponse {
	plan: AssistantPlan;
}

export interface RunbookResponse {
	runbook: Runbook;
}

export interface AdvanceRunbookResponse {
	action: string;
	confirmation_token?: string;
}

export const assistantRequest = <T = unknown>(
	url: string,
	method: 'get' | 'post' = 'get',
	data?: Record<string, unknown>,
	params?: Record<string, unknown>,
): Promise<T> => request({ url, method, data, params });
