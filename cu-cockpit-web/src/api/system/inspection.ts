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
