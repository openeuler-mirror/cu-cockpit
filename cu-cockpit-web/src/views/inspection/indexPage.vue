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

function openCreate() {
  if (disposed || !access.value.manage || state.saving) return;
  state.editor = { id: null, name: '', kind: 'daily', time: '02:00', minutes: 30,
    timezone: 'Asia/Shanghai', enabled: true,
    services: [...(state.overview?.template.default_services || [])] };
  state.formError = '';
  state.dialog = true;
}

function openEdit(plan: inspection.InspectionPlan) {
  if (disposed || !access.value.manage || state.saving) return;
  state.editor = { id: plan.id, name: plan.name, kind: plan.schedule_kind,
    time: plan.schedule_kind === 'daily' ? plan.schedule_settings.time : '02:00',
    minutes: plan.schedule_kind === 'interval' ? plan.schedule_settings.minutes : 30,
    timezone: plan.timezone, enabled: plan.enabled, services: [...plan.parameters.services] };
  state.formError = '';
  state.dialog = true;
}

async function savePlan() {
  if (disposed || state.saving) return;
  state.formError = '';
  const editor = state.editor;
  if (!access.value.manage) {
    state.formError = '当前账号没有管理巡检计划的权限。';
    return;
  }
  if (!editor.name.trim() || [...editor.name].length > 128 || /[\p{C}\p{Zl}\p{Zp}]/u.test(editor.name) ||
      !['daily', 'interval', 'manual'].includes(editor.kind) || typeof editor.enabled !== 'boolean' ||
      (editor.id !== null && (!Number.isSafeInteger(editor.id) || editor.id <= 0)) ||
      (editor.kind === 'daily' && !/^(?:[01][0-9]|2[0-3]):[0-5][0-9]$/.test(editor.time)) ||
      (editor.kind === 'interval' && ![15, 30, 60].includes(editor.minutes))) {
    state.formError = '请填写有效的计划名称、时间或执行间隔。';
    return;
  }
  if (!state.overview || editor.services.length > state.overview.template.max_services ||
      new Set(editor.services).size !== editor.services.length ||
      editor.services.some(service => !state.overview?.template.registered_services.includes(service))) {
    state.formError = '请选择数量限制内、不重复的已注册服务。';
    return;
  }
  try {
    if (!editor.timezone || editor.timezone.length > 64) throw new RangeError();
    new Intl.DateTimeFormat('zh-CN', { timeZone: editor.timezone }).format();
  } catch {
    state.formError = '请输入有效的 IANA 时区，例如 Asia/Shanghai。';
    return;
  }
  const schedule: inspection.InspectionSchedule = editor.kind === 'daily'
    ? { schedule_kind: 'daily', schedule_settings: { time: editor.time } }
    : editor.kind === 'interval'
      ? { schedule_kind: 'interval', schedule_settings: { minutes: editor.minutes } }
      : { schedule_kind: 'manual', schedule_settings: {} };
  const data: inspection.InspectionPlanInput = { ...schedule, name: editor.name.trim(),
    template_id: 'local-host', version: 'v1', timezone: editor.timezone,
    enabled: editor.enabled, parameters: { services: [...editor.services] } };
  state.saving = true;
  try {
    if (editor.id === null) await inspection.createInspectionPlan(data);
    else await inspection.updateInspectionPlan(editor.id, data);
    if (disposed) return;
    state.dialog = false;
    await loadWorkspace();
  } catch {
    if (!disposed) state.formError = '计划保存失败，请检查权限或稍后重试。';
  } finally {
    if (!disposed) state.saving = false;
  }
}

async function togglePlan(plan: inspection.InspectionPlan, enabled: boolean) {
  if (disposed || state.toggling !== null) return;
  if (!access.value.manage || typeof enabled !== 'boolean' ||
      !Number.isSafeInteger(plan.id) || plan.id <= 0) {
    state.error = '无法切换计划，请检查管理权限和计划状态。';
    return;
  }
  const previous = plan.enabled;
  state.error = '';
  state.toggling = plan.id;
  plan.enabled = enabled;
  try {
    const updated = await inspection.toggleInspectionPlan(plan.id, enabled);
    if (disposed) return;
    Object.assign(plan, updated);
    state.plans = state.plans.map(item => item.id === updated.id ? updated : item);
  } catch {
    if (!disposed) {
      plan.enabled = previous;
      state.plans = state.plans.map(item => item.id === plan.id ? { ...item, enabled: previous } : item);
      state.error = '计划状态更新失败，已恢复原状态，请稍后重试。';
    }
  } finally {
    if (!disposed) state.toggling = null;
  }
}

async function queueInspection(planId: number | null = state.selectedPlan) {
  if (disposed || state.queueing) return;
  if (!access.value.execute ||
      (planId !== null && (!Number.isSafeInteger(planId) || planId <= 0))) {
    state.error = '无法提交巡检，请检查执行权限、计划和巡检工作进程状态。';
    return;
  }
  state.error = '';
  state.queueing = true;
  try {
    const data = planId === null
      ? { parameters: { services: [...(state.overview?.template.default_services || [])] } }
      : { plan_id: planId };
    const run = await inspection.queueInspectionRun(data);
    if (disposed) return;
    state.pending = [run, ...state.pending.filter(item => item.id !== run.id)];
    state.runPage = 1;
    await loadWorkspace();
  } finally {
    if (!disposed) state.queueing = false;
  }
}
</script>