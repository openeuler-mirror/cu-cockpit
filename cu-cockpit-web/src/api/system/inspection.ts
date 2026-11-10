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