const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createRequire } = require('node:module');
const test = require('node:test');
const vm = require('node:vm');

const web = path.resolve(__dirname, '../../cu-cockpit-web');
const webRequire = createRequire(path.join(web, 'package.json'));
const ts = webRequire('typescript');
const { parse, compileScript } = webRequire('@vue/compiler-sfc');
const source = fs.readFileSync(path.join(web, 'src/views/backups/indexPage.vue'), 'utf8');
const descriptor = parse(source, { filename: 'indexPage.vue' }).descriptor;
const compiled = compileScript(descriptor, { id: 'backup-workspace' });

function load(sourceCode, imports) {
  const code = ts.transpileModule(sourceCode, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const module = { exports: {} };
  vm.runInNewContext(code, { module, exports: module.exports,
    require: name => imports[name] || (name === 'vue' ? webRequire('vue') : {}),
    setTimeout, clearTimeout, Date, URL }, { filename: 'backup-workspace.js' });
  return module.exports;
}

function scheduleBody() {
  const apiSource = fs.readFileSync(path.join(web, 'src/api/system/backups.ts'), 'utf8');
  let body;
  const api = load(apiSource, { 'js-cookie': { default: { get: () => 'csrf' } },
    '/@/utils/request': { default: config => { body = config.data; return Promise.resolve({ schedule: config.data }); } } });
  return api.saveBackupSchedule({ enabled: true, time: '02:30', timezone: 'UTC',
    next_run: '2026-11-07T02:30:00Z' }).then(() => body);
}

if (process.argv[2] === '--schedule-body') {
  scheduleBody().then(body => process.stdout.write(JSON.stringify(body)));
} else {
test('compiled backup workspace sorts actual restore tasks and sends editable schedule fields only', async () => {
  const requests = [];
  const apiSource = fs.readFileSync(path.join(web, 'src/api/system/backups.ts'), 'utf8');
  const request = async config => {
    requests.push(config);
    return { schedule: { ...config.data, next_run: '2026-11-07T02:00:00Z' } };
  };
  const api = load(apiSource, { 'js-cookie': { default: { get: () => 'csrf' } },
    '/@/utils/request': { default: request } });
  const tasks = [
    { id: 'b'.repeat(32), kind: 'backup', status: 'succeeded', created_at: '2026-11-05T10:00:00Z' },
    { id: '1'.repeat(32), kind: 'restore', status: 'awaiting_confirmation', expires_at: '2026-11-07T10:00:00Z' },
    { id: '3'.repeat(32), kind: 'restore', status: 'awaiting_maintenance', confirmed_at: '2026-11-06T10:00:00Z' },
    { id: '2'.repeat(32), kind: 'restore', status: 'completed', started_at: '2026-11-06T08:00:00Z', finished_at: '2026-11-06T09:00:00Z' },
  ];
  const overview = { available: true, backups: [], tasks, schedule: {
    enabled: true, time: '02:00', timezone: 'UTC', next_run: '2026-11-07T02:00:00Z',
  }, capabilities: { create: false, verify: true, schedule: true, create_reason: null } };
  api.getBackupOverview = async () => overview;
  const mounted = [];
  const unmounted = [];
  const vue = { defineComponent: options => options, ref: value => ({ value }), reactive: value => value,
    computed: getter => ({ get value() { return getter(); } }),
    onMounted: callback => mounted.push(callback), onBeforeUnmount: callback => unmounted.push(callback) };
  const page = load(compiled.content, {
    vue, '/@/api/system': { getSystemContext: async () => ({ identity: { role: 'admin', is_admin: true } }) },
    '/@/api/system/backups': api,
  }).default.setup({}, { expose: () => {} });
  mounted[0]();
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(Array.from(page.sortedTasks.value, task => task.id),
    ['2'.repeat(32), 'b'.repeat(32), '3'.repeat(32), '1'.repeat(32)]);
  assert.equal(page.formatTime(tasks[1].created_at), '暂无');
  assert.deepEqual(Object.keys(page.schedule).sort(), ['enabled', 'time', 'timezone']);
  await page.saveSchedule();
  assert.deepEqual(Object.keys(requests[0].data).sort(), ['enabled', 'time', 'timezone']);
  assert.equal(requests[0].url, '/system/backups/schedule');
  assert.equal(page.overview.value.schedule.next_run, '2026-11-07T02:00:00Z');
  await api.saveBackupSchedule({ ...overview.schedule });
  assert.deepEqual(Object.keys(requests[1].data).sort(), ['enabled', 'time', 'timezone']);
  unmounted[0]();
});

test('cancel preflight, preflight again, confirm and refresh keep both real restore tasks sortable', async () => {
  const tasks = [{ id: 'b'.repeat(32), kind: 'backup', status: 'succeeded',
    created_at: '2026-11-05T10:00:00Z' }];
  const archive = { archive_id: 'a'.repeat(32), application_version: '1', actor: 'admin', size: 1024 };
  const overview = { available: true, backups: [archive], tasks, schedule: {
    enabled: false, time: '02:00', timezone: 'UTC', next_run: null,
  }, capabilities: { create: false, verify: true, schedule: true, create_reason: null } };
  const expiresAt = new Date(Date.now() + 60000).toISOString();
  const api = {
    getBackupOverview: async () => overview,
    preflightRestore: async () => {
      const id = String(tasks.length).repeat(32);
      tasks.push({ id, kind: 'restore', status: 'awaiting_confirmation',
        expires_at: expiresAt });
      return { task_id: id, token: 'token', expires_at: expiresAt,
        preview: { members: {}, total_size: 0, targets: [], services: [], requires_maintenance: true, risks: [] } };
    },
    confirmRestore: async id => {
      tasks.find(task => task.id === id).status = 'awaiting_maintenance';
      return { task: { id, status: 'awaiting_maintenance' } };
    },
  };
  const mounted = [];
  const unmounted = [];
  const vue = { defineComponent: options => options, ref: value => ({ value }), reactive: value => value,
    computed: getter => ({ get value() { return getter(); } }),
    onMounted: callback => mounted.push(callback), onBeforeUnmount: callback => unmounted.push(callback) };
  const page = load(compiled.content, {
    vue, '/@/api/system': { getSystemContext: async () => ({ identity: { role: 'admin', is_admin: true } }) },
    '/@/api/system/backups': api,
  }).default.setup({}, { expose: () => {} });
  mounted[0]();
  await new Promise(resolve => setImmediate(resolve));
  await page.openRestore(archive);
  page.dialog.value = false;
  page.clearPreflight();
  await page.openRestore(archive);
  page.acknowledged.value = true;
  await page.confirm();
  await page.refresh();
  assert.equal(page.overview.value.tasks.filter(task => task.kind === 'restore').length, 2);
  assert.deepEqual(Array.from(page.sortedTasks.value, task => task.id),
    ['b'.repeat(32), '2'.repeat(32), '1'.repeat(32)]);
  assert.equal(page.formatTime(page.sortedTasks.value[1].created_at), '暂无');
  unmounted[0]();
});
}