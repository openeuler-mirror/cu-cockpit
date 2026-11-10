<template>
  <main class="inspection-page" aria-label="巡检中心"></main>
</template>

<script setup lang="ts" name="inspectionIndex">
type PlanEditor = {
  id: number | null;
  name: string;
  kind: 'daily' | 'interval' | 'manual';
  time: string;
  minutes: 15 | 30 | 60;
  timezone: string;
  enabled: boolean;
  services: string[];
};

import { reactive } from 'vue';
import * as inspection from '/@/api/system/inspection';

const state = reactive({
  overview: null as inspection.InspectionOverview | null,
  loading: false,
  error: '',
  plans: [] as inspection.InspectionPlan[],
  planPage: 1,
  planTotal: 0,
  runs: [] as inspection.InspectionRun[],
  runPage: 1,
  runTotal: 0,
  pending: [] as inspection.InspectionRun[],
  selectedPlan: null as number | null,
  selected: null as inspection.InspectionRun | null,
  detailOpen: false,
  detailLoading: false,
  detailError: '',
  dialog: false,
  formError: '',
  saving: false,
  queueing: false,
  toggling: null as number | null,
  downloading: '' as '' | 'json' | 'html',
  editor: { id: null, name: '', kind: 'daily', time: '02:00', minutes: 30,
    timezone: 'Asia/Shanghai', enabled: true, services: [] } as PlanEditor,
});
let disposed = false;
let polling = false;
let pollTimer: ReturnType<typeof setInterval> | undefined;

import { computed } from 'vue';

const access = computed(() => ({
  manage: Boolean(state.overview?.can_manage && state.overview.identity.is_admin),
  execute: Boolean(state.overview?.can_manage && state.overview.identity.is_admin && state.overview.worker.available),
}));

function statusLabel(status: inspection.InspectionHealth | inspection.InspectionRun['phase'] | null) {
  return status ? ({ queued: '排队中', running: '运行中', finished: '已结束', pass: '通过',
    warning: '警告', fail: '异常', error: '错误', skipped: '跳过' }[status]) : '待生成';
}

function formatTime(value: string | null) {
  if (!value) return '暂无';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('zh-CN', { hour12: false });
}

function formatValue(value: inspection.InspectionValue) {
  return value === null ? '-' : typeof value === 'string' ? value : JSON.stringify(value, null, 2);
}

async function loadWorkspace() {
  if (disposed || state.loading) return;
  state.loading = true;
  state.error = '';
  try {
    const [overview, plans, runs] = await Promise.all([
      inspection.getInspectionOverview(),
      inspection.getInspectionPlans(state.planPage),
      inspection.getInspectionRuns(state.runPage),
    ]);
    if (disposed) return;
    Object.assign(state, { overview, plans: plans.items, planTotal: plans.total,
      planPage: plans.page, runs: runs.items, runTotal: runs.total, runPage: runs.page });
  } catch {
    if (!disposed) state.error = '巡检数据加载失败，请稍后重试。';
  } finally {
    if (!disposed) state.loading = false;
  }
}
</script>