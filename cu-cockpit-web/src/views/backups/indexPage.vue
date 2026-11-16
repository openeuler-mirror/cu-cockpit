<template>
  <main class="backup-page" aria-label="备份与恢复中心" :aria-busy="loading">
    <header class="backup-head">
      <div><h1>备份与恢复</h1><p>本机归档、每日计划与维护恢复</p></div>
      <el-button :icon="Refresh" :loading="loading" :disabled="!!busy || !isAdmin" @click="refresh()">刷新</el-button>
    </header>
    <el-alert v-if="!identityLoaded && !error" type="info" title="正在确认访问权限…" :closable="false" show-icon />
    <el-alert v-if="identityLoaded && !isAdmin" type="warning" title="仅管理员可访问备份归档与恢复任务。" :closable="false" show-icon />
    <el-alert v-if="unavailable && isAdmin" type="warning" title="备份服务尚未初始化，或安装数据不可访问" :closable="false" show-icon>
      <p>原因：{{ unavailable }}。请在目标主机的独立 SSH 会话中以 root 核查并按需初始化：<code>venv/bin/python manage.py backup_center init</code>，再刷新页面。已有列表可能不是最新状态。不要在浏览器中执行。</p>
    </el-alert>
    <el-alert v-if="error" type="error" :title="error" :closable="false" show-icon role="alert" />
    <el-alert v-if="notice" type="info" :title="notice" :closable="false" show-icon role="status" />
    <template v-if="isAdmin && overview">
      <section class="backup-section" aria-labelledby="backup-archives">
        <div class="backup-section-head"><h2 id="backup-archives">本机归档 <small>{{ overview.backups.length }}</small></h2>
          <div class="backup-actions">
            <el-button :icon="Upload" :disabled="busy || loading" :loading="busy === 'import'" @click="pickFile">导入归档</el-button>
            <input ref="fileInput" class="backup-file-input" type="file" accept=".zip,application/zip" @change="onFileChange" />
            <el-button type="primary" :icon="Plus" :disabled="!overview.capabilities.create || !!busy || loading" :loading="busy === 'create'" @click="create">创建备份</el-button>
          </div>
        </div>
        <p v-if="!overview.capabilities.create" class="backup-muted">{{ overview.capabilities.create_reason || '备份源不可用，请检查数据库与已注册配置。' }}</p>
        <p class="backup-muted">单个 ZIP 文件不超过 256 MiB；导入会在服务端验证签名及兼容性。</p>
        <div class="backup-table-scroll" role="region" tabindex="0" aria-label="备份归档表">
          <table><thead><tr><th>归档 ID</th><th>大小</th><th>应用版本</th><th>创建者</th><th>操作</th></tr></thead>
            <tbody><tr v-for="archive in overview.backups" :key="archive.archive_id">
              <td class="backup-id">{{ archive.archive_id }}</td><td>{{ formatBytes(archive.size) }}</td>
              <td>{{ archive.application_version }}</td><td>{{ archive.actor }}</td>
              <td><div class="backup-actions">
                <el-tooltip content="校验归档签名与完整性"><el-button :icon="CircleCheck" :aria-label="`校验 ${archive.archive_id}`" :loading="busy === `verify:${archive.archive_id}`" :disabled="!!busy || loading" @click="verify(archive)" /></el-tooltip>
                <el-tooltip content="私密下载归档"><el-button :icon="Download" :aria-label="`下载 ${archive.archive_id}`" :loading="busy === `download:${archive.archive_id}`" :disabled="!!busy || loading" @click="download(archive)" /></el-tooltip>
                <el-button :icon="RefreshRight" :disabled="!!busy || loading" @click="openRestore(archive)">恢复预检</el-button>
              </div></td>
            </tr><tr v-if="!overview.backups.length"><td colspan="5" class="backup-empty">暂无归档</td></tr></tbody></table>
        </div>
      </section>
      <section class="backup-section" aria-labelledby="backup-schedule">
        <div class="backup-section-head"><h2 id="backup-schedule">每日备份计划</h2><span class="backup-muted">下次执行：{{ formatTime(overview.schedule.next_run) }}</span></div>
        <div class="backup-schedule">
          <label>启用 <el-switch v-model="schedule.enabled" :disabled="!!busy || loading" aria-label="启用每日备份" /></label>
          <label>执行时间 <el-time-picker v-model="schedule.time" value-format="HH:mm" format="HH:mm" :clearable="false" :disabled="!!busy || loading" aria-label="每日执行时间" /></label>
          <label>时区 <el-select v-model="schedule.timezone" :disabled="!!busy || loading" aria-label="计划时区">
            <el-option v-for="zone in timezones" :key="zone" :label="zone" :value="zone" />
          </el-select></label>
          <el-button :icon="Check" type="primary" :loading="busy === 'schedule'" :disabled="!!busy || loading" @click="saveSchedule">保存计划</el-button>
        </div>
        <p class="backup-muted">计划由主机上的备份 timer 执行；停用计划不会删除已有任务。</p>
      </section>
      <section class="backup-section" aria-labelledby="backup-tasks">
        <h2 id="backup-tasks">备份 / 恢复任务 <small>{{ overview.tasks.length }}</small></h2>
        <div class="backup-table-scroll" role="region" tabindex="0" aria-label="备份恢复任务表">
          <table><thead><tr><th>任务 ID / 类型</th><th>状态</th><th>归档</th><th>创建时间</th><th>开始 / 结束</th></tr></thead>
            <tbody><tr v-for="task in sortedTasks" :key="task.id">
              <td class="backup-id">{{ task.id }}<small>{{ task.kind === 'backup' ? '备份' : '恢复' }}</small></td>
              <td><strong :class="['backup-state', `is-${task.status}`]">{{ statusLabel(task.status) }}</strong>
                <small v-if="task.status === 'queued'">等待主机备份 worker；若未启动，请在独立 SSH/root 会话执行 README 中的 run-pending 命令或安装 timer。</small>
                <small v-if="task.status === 'awaiting_maintenance'">等待维护，尚未恢复。请在独立 SSH/root 会话中进入应用目录并加载 os.env 后执行下方命令。</small>
                <small v-if="task.status === 'manual_recovery_required' || task.requires_manual_recovery" class="backup-danger">需人工恢复；安全备份 ID：{{ task.safety_archive_id || '未提供，请检查主机任务记录' }}。请勿重复执行恢复。</small>
                <small v-if="task.status === 'failed'" class="backup-danger">{{ task.error || '任务失败，请在主机检查任务记录。' }}</small>
                <div v-if="task.status === 'awaiting_maintenance'" class="backup-command"><code>{{ maintenanceCommand(task.id) }}</code>
                  <el-tooltip content="复制维护命令"><el-button :icon="CopyDocument" :aria-label="`复制任务 ${task.id} 维护命令`" @click="copyCommand(task.id)" /></el-tooltip></div>
              </td><td class="backup-id">{{ task.archive_id || '—' }}</td><td>{{ formatTime(task.created_at) }}</td><td>{{ formatTime(task.started_at) }}<small>{{ formatTime(task.finished_at) }}</small></td>
            </tr><tr v-if="!overview.tasks.length"><td colspan="5" class="backup-empty">暂无任务</td></tr></tbody></table>
        </div>
      </section>
    </template>
    <el-dialog v-model="dialog" class="backup-dialog" width="min(640px, 94vw)" title="恢复预检" :close-on-click-modal="!busy" :close-on-press-escape="!busy" :show-close="!busy" @closed="clearPreflight">
      <p class="backup-id">归档：{{ selected?.archive_id }}</p>
      <p v-if="busy === 'preflight'" role="status">正在校验签名、归档与恢复目标…</p>
      <el-alert v-if="dialogError" type="error" :title="dialogError" :closable="false" show-icon role="alert" />
      <template v-if="preflight">
        <el-alert type="warning" title="签名和目标已通过服务端预检；确认仅登记维护任务，不会立即恢复。" :closable="false" show-icon />
        <dl class="backup-preview">
          <div><dt>任务 ID</dt><dd>{{ preflight.task_id }}</dd></div>
          <div><dt>确认有效期</dt><dd>{{ formatTime(preflight.expires_at) }}</dd></div>
          <div><dt>归档内容</dt><dd>{{ Object.keys(preflight.preview.members).join('、') }}（{{ formatBytes(preflight.preview.total_size) }}）</dd></div>
          <div><dt>影响目标</dt><dd>{{ preflight.preview.targets.join('、') }}</dd></div>
          <div><dt>需停止的服务</dt><dd>{{ preflight.preview.services.join('、') }}</dd></div>
          <div><dt>风险</dt><dd>{{ preflight.preview.risks.join('；') }}</dd></div>
        </dl>
        <el-checkbox v-model="acknowledged" :disabled="!!busy">我已了解服务中断、数据库及配置替换、会话失效等风险，且会通过独立 SSH/root 维护</el-checkbox>
        <p v-if="expired" class="backup-danger">确认已过期，请关闭窗口并重新预检该归档。</p>
      </template>
      <template #footer><el-button :disabled="!!busy" @click="dialog = false">取消</el-button>
        <el-button type="danger" :loading="busy === 'confirm'" :disabled="!preflight || !acknowledged || expired || !!busy" @click="confirm">确认并等待维护</el-button></template>
    </el-dialog>
  </main>
</template>

<script setup lang="ts" name="backupsIndex">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue';
import { Check, CircleCheck, CopyDocument, Download, Plus, Refresh, RefreshRight, Upload } from '@element-plus/icons-vue';
import { getSystemContext } from '/@/api/system';
import * as api from '/@/api/system/backups';

const identityLoaded = ref(false);
const isAdmin = ref(false);
const overview = ref<api.BackupOverview | null>(null);
const loading = ref(false);
const busy = ref('');
const error = ref('');
const notice = ref('');
const unavailable = ref('');
const dialog = ref(false);
const dialogError = ref('');
const selected = ref<api.BackupArchive | null>(null);
const preflight = ref<api.RestorePreflight | null>(null);
const acknowledged = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);
const schedule = reactive({ enabled: false, time: '02:00', timezone: 'UTC' });
const timezones = computed(() => [...new Set(['UTC', 'Asia/Shanghai', schedule.timezone])]);
const sortedTasks = computed(() => [...(overview.value?.tasks || [])].sort((a, b) => b.created_at.localeCompare(a.created_at)));
const expired = ref(true);
let disposed = false;
let pollTimer: ReturnType<typeof setTimeout> | undefined;
let expiryTimer: ReturnType<typeof setTimeout> | undefined;
let pollFailures = 0;
let trackingRestore = '';

function formatBytes(bytes: number) { return `${(bytes / 1024 / 1024).toFixed(2)} MiB`; }
function formatTime(value?: string | null) {
  if (!value) return '暂无';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '时间不可用' : date.toLocaleString('zh-CN', { hour12: false });
}
function statusLabel(status: api.BackupTask['status']) {
  return ({ queued: '排队中', running: '运行中', succeeded: '已完成', failed: '失败',
    awaiting_confirmation: '待确认', awaiting_maintenance: '等待维护，尚未恢复',
    completed: '恢复完成', manual_recovery_required: '需人工恢复' } as Record<string, string>)[status] || status;
}
function maintenanceCommand(id: string) { return `venv/bin/python manage.py backup_center restore ${id} --confirm-maintenance`; }
function message(cause: unknown, fallback: string) {
  const data = (cause as { response?: { data?: { reason?: unknown; message?: unknown } } })?.response?.data;
  const detail = data?.reason ?? data?.message;
  return typeof detail === 'string' && detail.length < 200 ? `${fallback}：${detail}` : fallback;
}
function clearPreflight() {
  if (expiryTimer) clearTimeout(expiryTimer);
  preflight.value = null; expired.value = true; acknowledged.value = false; selected.value = null; dialogError.value = '';
}
function schedulePoll() {
  if (pollTimer) clearTimeout(pollTimer);
  if (disposed || !isAdmin.value || !overview.value || pollFailures >= 3) return;
  const active = overview.value.tasks.some(task => task.status === 'queued' || task.status === 'running');
  const tracking = trackingRestore && overview.value.tasks.some(task => task.id === trackingRestore && task.status === 'awaiting_maintenance');
  if (!active && !tracking) return;
  pollTimer = setTimeout(() => { void refresh(true); }, pollFailures ? 15000 : 5000);
}
async function refresh(poll = false) {
  if (disposed || !isAdmin.value || loading.value || busy.value) { if (poll && !disposed) schedulePoll(); return; }
  loading.value = true;
  if (!poll) { error.value = ''; notice.value = ''; pollFailures = 0; }
  try {
    const data = await api.getBackupOverview();
    if (disposed) return;
    overview.value = data;
    unavailable.value = '';
    Object.assign(schedule, data.schedule);
    if (trackingRestore && !data.tasks.some(task => task.id === trackingRestore && task.status === 'awaiting_maintenance')) trackingRestore = '';
    pollFailures = 0;
    error.value = '';
  } catch (cause) {
    if (disposed) return;
    const response = (cause as { response?: { status?: number; data?: { reason?: string } } })?.response;
    if (response?.status === 503 && response.data?.reason) {
      unavailable.value = response.data.reason;
      if (poll) pollFailures = 3;
    } else if (!poll) error.value = message(cause, '备份数据刷新失败，现有列表已保留');
    else pollFailures += 1;
  } finally {
    loading.value = false;
    schedulePoll();
  }
}
async function initialize() {
  try {
    const context = await getSystemContext();
    if (disposed) return;
    isAdmin.value = context.identity.role === 'admin' && context.identity.is_admin;
    identityLoaded.value = true;
    if (isAdmin.value) await refresh();
  } catch {
    if (!disposed) error.value = '无法确认当前身份，请重新登录或刷新页面。';
  }
}
async function perform(action: string, call: () => Promise<void>) {
  if (!isAdmin.value || busy.value || loading.value || !overview.value) return;
  busy.value = action;
  error.value = ''; notice.value = '';
  try { await call(); } catch (cause) { if (!disposed) error.value = message(cause, '操作失败，现有数据已保留，请刷新核对'); }
  finally { busy.value = ''; schedulePoll(); }
}
async function create() {
  await perform('create', async () => {
    if (!overview.value?.capabilities.create) return;
    const { task } = await api.createBackup();
    if (disposed || !overview.value) return;
    overview.value = { ...overview.value, tasks: [task, ...overview.value.tasks] };
    notice.value = '任务已排队，等待主机备份 worker；请在任务表确认最终状态。';
  });
}
function pickFile() { if (!busy.value && isAdmin.value) fileInput.value?.click(); }
async function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const files = input.files;
  if (!files || files.length !== 1 || files[0].size > api.MAX_BACKUP_BYTES || files[0].size === 0) {
    error.value = '请选择单个非空 ZIP 文件，大小不超过 256 MiB。'; input.value = ''; return;
  }
  const file = files[0]; input.value = '';
  await perform('import', async () => { const { backup } = await api.importBackup(file);
    if (disposed || !overview.value) return;
    overview.value = { ...overview.value, backups: [backup, ...overview.value.backups.filter(item => item.archive_id !== backup.archive_id)] };
  });
}
async function saveSchedule() {
  if (!/^(?:[01][0-9]|2[0-3]):[0-5][0-9]$/.test(schedule.time)) { error.value = '请选择有效的 HH:mm 时间。'; return; }
  await perform('schedule', async () => { const { schedule: saved } = await api.saveBackupSchedule({ ...schedule });
    if (!disposed && overview.value) { overview.value = { ...overview.value, schedule: saved }; Object.assign(schedule, saved); }
  });
}
async function verify(archive: api.BackupArchive) {
  await perform(`verify:${archive.archive_id}`, async () => {
    const result = await api.verifyBackup(archive.archive_id);
    if (!disposed) notice.value = `归档 ${result.archive_id} 已通过签名与完整性校验（${formatBytes(result.total_size)}）。`;
  });
}
async function download(archive: api.BackupArchive) {
  await perform(`download:${archive.archive_id}`, async () => {
    const blob = await api.downloadBackup(archive.archive_id);
    if (disposed) return;
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    try { link.href = url; link.download = `${archive.archive_id}.zip`; document.body.appendChild(link); link.click(); }
    finally { link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
  });
}
async function openRestore(archive: api.BackupArchive) {
  if (!isAdmin.value || busy.value || loading.value) return;
  clearPreflight(); selected.value = archive; dialog.value = true; busy.value = 'preflight';
  try { const result = await api.preflightRestore(archive.archive_id);
    if (!disposed && dialog.value && selected.value?.archive_id === archive.archive_id) {
      preflight.value = result;
      const remaining = Date.parse(result.expires_at) - Date.now();
      expired.value = !Number.isFinite(remaining) || remaining <= 0;
      if (!expired.value) expiryTimer = setTimeout(() => { expired.value = true; }, remaining);
    }
  } catch (cause) { if (!disposed) dialogError.value = message(cause, '预检未通过，请核对归档和目标状态'); }
  finally { busy.value = ''; schedulePoll(); }
}
async function confirm() {
  if (!isAdmin.value || busy.value || !preflight.value || !acknowledged.value ||
      expired.value || Date.parse(preflight.value.expires_at) <= Date.now()) return;
  const { task_id, token } = preflight.value;
  busy.value = 'confirm'; dialogError.value = '';
  try {
    const { task } = await api.confirmRestore(task_id, token);
    if (disposed) return;
    if (task.status !== 'awaiting_maintenance') throw new Error('Unexpected restore state');
    trackingRestore = task.id;
    if (overview.value) overview.value = { ...overview.value, tasks: [
      { id: task.id, kind: 'restore', status: 'awaiting_maintenance', archive_id: selected.value?.archive_id,
        created_at: new Date().toISOString() }, ...overview.value.tasks.filter(item => item.id !== task.id),
    ] };
    dialog.value = false; clearPreflight();
    await refreshAfterMutation();
  } catch (cause) { if (!disposed) {
    dialogError.value = message(cause, '确认结果未能核实，请关闭并重新预检，不要复用确认信息');
    preflight.value = null; acknowledged.value = false; expired.value = true;
    if (expiryTimer) clearTimeout(expiryTimer);
  } }
  finally { busy.value = ''; schedulePoll(); }
}
async function refreshAfterMutation() {
  try { const data = await api.getBackupOverview();
    if (!disposed) { overview.value = data; Object.assign(schedule, data.schedule); }
  } catch { if (!disposed) error.value = '确认已提交，但任务列表刷新失败；请刷新核对任务状态后再执行维护命令。'; }
}
async function copyCommand(id: string) {
  try { await navigator.clipboard.writeText(maintenanceCommand(id)); }
  catch { error.value = '复制失败，请从任务表手动复制维护命令。'; }
}
onMounted(() => { void initialize(); });
onBeforeUnmount(() => { disposed = true; if (pollTimer) clearTimeout(pollTimer); clearPreflight(); });
</script>

<style lang="scss" scoped src="./backup-page.scss"></style>