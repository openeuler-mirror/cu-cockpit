export interface InspectionParameters {
  services: string[];
}

export type InspectionSchedule =
  | { schedule_kind: 'daily'; schedule_settings: { time: string } }
  | { schedule_kind: 'interval'; schedule_settings: { minutes: 15 | 30 | 60 } }
  | { schedule_kind: 'manual'; schedule_settings: Record<string, never> };

export type InspectionPlanInput = InspectionSchedule & {
  name: string;
  template_id: 'local-host';
  version: 'v1';
  parameters: InspectionParameters;
  timezone: string;
  enabled: boolean;
};

export type InspectionPlan = InspectionPlanInput & {
  id: number;
  revision: number;
  actor: string;
  next_run: string | null;
  cursor: string | null;
  created_at: string;
  updated_at: string;
};

export interface InspectionPage<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}

export interface InspectionOverview {
  template: {
    id: 'local-host';
    version: 'v1';
    items: string[];
    default_services: string[];
    registered_services: string[];
    max_services: number;
    warning: number;
    fail: number;
    item_timeout: number;
    run_timeout: number;
  };
  worker: {
    available: boolean;
    reason: string | null;
    poll_seconds: number;
    runs_per_trigger: number;
  };
  identity: { username: string; is_admin: boolean };
  can_manage: boolean;
}

export type InspectionHealth = 'pass' | 'warning' | 'fail' | 'error' | 'skipped';
export type InspectionValue = null | boolean | number | string | InspectionValue[] | { [key: string]: InspectionValue };

export interface InspectionItem {
  id: string;
  label: string;
  status: InspectionHealth;
  value: InspectionValue;
  unit: string | null;
  threshold: InspectionValue;
  evidence: InspectionValue;
  reason: string;
  duration: number;
  version: string;
}

export interface InspectionRun {
  id: number;
  plan_id: number | null;
  plan_snapshot: InspectionValue;
  trigger: 'manual' | 'scheduled';
  actor: string;
  template_id: string;
  version: string;
  parameters: InspectionParameters;
  phase: 'queued' | 'running' | 'finished';
  health: InspectionHealth | null;
  scheduled_slot: string | null;
  queued_at: string;
  started_at: string | null;
  finished_at: string | null;
  duration: number | null;
  items: InspectionItem[];
  error: string;
  counts: Record<InspectionHealth, number>;
}

import request from '/@/utils/request';

export const getInspectionOverview = (): Promise<InspectionOverview> => request<InspectionOverview, InspectionOverview>({
  url: '/system/inspection/overview', method: 'get', withCredentials: true,
});

export const getInspectionPlans = (page = 1, limit = 20): Promise<InspectionPage<InspectionPlan>> => request<InspectionPage<InspectionPlan>, InspectionPage<InspectionPlan>>({
  url: '/system/inspection/plans', method: 'get', params: { page, limit }, withCredentials: true,
});
