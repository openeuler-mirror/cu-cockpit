<template>
	<div class="tech-terminal terminal-container">
		<header class="terminal-hud">
			<div class="terminal-identity">
				<span class="terminal-identity__mark"><el-icon><Operation /></el-icon></span>
				<div><h1 class="terminal-title">Web 终端</h1><div class="terminal-kicker">MULTI SESSION · PASSWORD / SSH KEY · XTERM CONSOLE</div></div>
			</div>
			<div class="terminal-hud__actions">
				<div class="terminal-status" :class="`is-${activeSession.state}`"><span class="terminal-status__dot"></span><span>{{ stateLabel(activeSession.state) }}</span></div>
				<el-button class="terminal-action" :icon="Plus" :disabled="sessions.length >= MAX_SESSIONS" @click="addSession()">新建标签</el-button>
				<el-button class="terminal-action terminal-action--disconnect" :icon="SwitchButton" :disabled="activeSession.state !== 'connected'" @click="activePane?.disconnect()">断开</el-button>
			</div>
		</header>

		<section class="terminal-summary" aria-label="终端会话摘要">
			<div v-for="item in summaryItems" :key="item.label" class="terminal-summary__item" :style="{ '--summary-accent': item.color }">
				<span class="terminal-summary__icon"><el-icon><component :is="item.icon" /></el-icon></span>
				<div><div class="terminal-summary__label">{{ item.label }}</div><div class="terminal-summary__value" :title="item.value">{{ item.value }}</div></div>
			</div>
		</section>

		<nav class="terminal-tabs" aria-label="终端会话标签">
			<button v-for="session in sessions" :key="session.id" :class="{ 'is-active': session.id === activeId }" @click="activateSession(session.id)">
				<span :class="`is-${session.state}`"></span><strong>{{ session.title }}</strong><small>{{ session.hostname || '未连接' }}</small>
				<el-icon v-if="sessions.length > 1" @click.stop="closeSession(session.id)"><Close /></el-icon>
			</button>
		</nav>

		<div class="terminal-control-layout">
			<section class="terminal-connect-panel">
				<div class="terminal-panel__head">
					<div><h2 class="terminal-panel__title">建立 SSH 会话</h2><div class="terminal-panel__meta">SECRETS STAY IN MEMORY · NEVER SAVED TO HISTORY</div></div>
					<div class="terminal-connect-head"><el-segmented v-model="activeSession.authType" :options="[{ label: '密码认证', value: 'password' }, { label: 'SSH 私钥', value: 'key' }]" :disabled="connectionLocked" /><span class="terminal-connection-detail">{{ activeSession.error || connectionHint }}</span></div>
				</div>
				<el-form class="terminal-connect-form" label-position="top" @submit.prevent>
				<div class="terminal-connect-grid">
					<el-form-item label="目标 IP / 主机名"><el-input v-model="activeSession.hostname" class="terminal-control" placeholder="例如 172.16.141.253" :disabled="connectionLocked" /></el-form-item>
					<el-form-item label="端口"><el-input-number v-model="activeSession.port" class="terminal-control terminal-port-control" :min="1" :max="65535" controls-position="right" :disabled="connectionLocked" /></el-form-item>
					<el-form-item label="用户名"><el-input v-model="activeSession.username" class="terminal-control" placeholder="SSH 用户名" :disabled="connectionLocked" /></el-form-item>
					<el-form-item v-if="activeSession.authType === 'password'" label="密码"><el-input v-model="activeSession.password" class="terminal-control" type="password" show-password autocomplete="new-password" :disabled="connectionLocked" /></el-form-item>
					<el-form-item v-if="activeSession.authType === 'key'" label="私钥口令（可选）"><el-input v-model="activeSession.passphrase" class="terminal-control" type="password" show-password autocomplete="new-password" :disabled="connectionLocked" /></el-form-item>
					<el-form-item v-if="activeSession.authType === 'key'" label="私钥" class="terminal-key-field"><el-input v-model="activeSession.privatekey" class="terminal-control terminal-key-input" type="textarea" :rows="4" placeholder="-----BEGIN OPENSSH PRIVATE KEY-----" :disabled="connectionLocked" /></el-form-item>
				</div>
				<div class="terminal-connect-actions"><span class="terminal-security-note">密码、私钥、口令不会写入浏览器存储或历史</span><el-button class="terminal-action terminal-action--primary" :icon="Connection" :loading="isConnecting" :disabled="!canConnect" @click="activePane?.connect()">{{ activeSession.state === 'failed' || activeSession.state === 'closed' ? '重新连接' : '连接终端' }}</el-button></div>
				</el-form>
			</section>

			<section class="terminal-history-panel">
				<div class="terminal-panel__head"><div><h2 class="terminal-panel__title">连接历史</h2><div class="terminal-panel__meta">NON-SENSITIVE PROFILE · QUICK RECONNECT</div></div><span>{{ history.length }}/20</span></div>
				<div class="terminal-history-list">
					<article v-for="item in history" :key="historyKey(item)"><span><el-icon><Clock /></el-icon></span><div><strong>{{ item.username }}@{{ item.hostname }}:{{ item.port }}</strong><small>{{ item.authType === 'key' ? 'SSH 私钥' : '密码认证' }} · {{ formatTime(item.connectedAt) }}</small></div><el-button class="terminal-action" @click="reconnectHistory(item)">快速重连</el-button><el-button :icon="Delete" circle text @click="removeHistory(item)" /></article>
					<div v-if="!history.length" class="terminal-history-empty">成功连接后将在此保存非敏感目标信息</div>
				</div>
			</section>
		</div>

		<section class="terminal-session-panel">
			<div class="terminal-panel__head"><div><h2 class="terminal-panel__title">交互式终端</h2><div class="terminal-panel__meta">{{ activeSession.title }} · {{ activeSession.cols || 0 }} COLS × {{ activeSession.rows || 0 }} ROWS</div></div><div class="terminal-session-actions"><el-button class="terminal-action" :icon="Delete" @click="activePane?.clear()">清屏</el-button></div></div>
			<div class="terminal-workspace">
				<div class="terminal-session-stack"><SessionPane v-for="session in sessions" v-show="session.id === activeId" :key="session.id" ref="paneRefs" :session="session" :font-size="appearance.fontSize" :background="appearance.background" :foreground="appearance.foreground" @connected="recordHistory" @update="updateSession" /></div>
				<aside class="terminal-settings"><div class="terminal-settings__title"><el-icon><Setting /></el-icon>显示设置</div><el-form label-position="top"><el-form-item label="字体大小"><el-select v-model="appearance.fontSize" class="terminal-control"><el-option v-for="size in fontSizes" :key="size" :label="`${size} px`" :value="size" /></el-select></el-form-item><el-form-item label="终端配色"><el-select v-model="appearance.background" class="terminal-control"><el-option v-for="theme in themes" :key="theme.background" :label="theme.label" :value="theme.background" /></el-select></el-form-item></el-form><div class="terminal-settings__facts"><span><small>会话</small><strong>{{ sessions.length }}/{{ MAX_SESSIONS }}</strong></span><span><small>编码</small><strong>UTF-8</strong></span></div></aside>
			</div>
		</section>
	</div>
</template>

<script setup lang="ts" name="terminalIndex">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import { Clock, Close, Connection, Delete, Monitor, Operation, Plus, Setting, SwitchButton, User } from '@element-plus/icons-vue';
import Cookies from 'js-cookie';
import { storeToRefs } from 'pinia';
import { getToken } from '/@/api/terminal';
import { Local } from '/@/utils/storage';
import { userPermissiom } from '/@/stores/userPermissiom';
import { useThemeConfig } from '/@/stores/themeConfig';
import SessionPane from './components/sessionPane.vue';
import type { TerminalConnectionState, TerminalHistoryItem, TerminalSessionModel } from './sessionTypes';

interface PaneExpose { sessionId: string; connect: () => Promise<void>; disconnect: () => void; clear: () => void; focus: () => void; resize: () => void; }
const MAX_SESSIONS = 8;
let sessionSequence = 0;
const makeSession = (profile?: Partial<TerminalHistoryItem>): TerminalSessionModel => ({ id: `terminal-${Date.now()}-${++sessionSequence}`, title: `终端 ${sessionSequence}`, hostname: profile?.hostname || '', port: profile?.port || 22, username: profile?.username || '', authType: profile?.authType || 'password', password: '', privatekey: '', passphrase: '', term: 'xterm-256color', state: 'idle', error: '', cols: 0, rows: 0 });
const sessions = reactive<TerminalSessionModel[]>([makeSession()]);
const activeId = ref(sessions[0].id);
const paneRefs = ref<PaneExpose[]>([]);
const history = ref<TerminalHistoryItem[]>(sanitizeHistory(Local.get('terminalConnectionHistory')));
const themeStore = useThemeConfig();
const { themeConfig } = storeToRefs(themeStore);
const permissionStore = userPermissiom();
const { u_Permission } = storeToRefs(permissionStore);
const appearance = reactive({ fontSize: Number(Local.get('terminalConfig')?.fontSize) || 20, background: Local.get('terminalConfig')?.background || '#000000', foreground: Local.get('terminalConfig')?.foreground || '#ffffff' });
const fontSizes = [10, 12, 14, 16, 18, 20, 22, 24, 28, 36];
const themes = [{ label: '黑色', background: '#000000', foreground: '#ffffff' }, { label: '暗色', background: '#002b36', foreground: '#ffffff' }, { label: '亮色', background: '#fdf6e3', foreground: '#000000' }];
const activeSession = computed(() => sessions.find((item) => item.id === activeId.value) || sessions[0]);
const activePane = computed(() => paneRefs.value.find((pane) => pane.sessionId === activeId.value));
const isConnecting = computed(() => ['authenticating', 'connecting'].includes(activeSession.value.state));
const connectionLocked = computed(() => isConnecting.value || activeSession.value.state === 'connected');
const hasSecret = computed(() => activeSession.value.authType === 'password' ? Boolean(activeSession.value.password) : Boolean(activeSession.value.privatekey));
const canConnect = computed(() => u_Permission.value === 'root' && !connectionLocked.value && Boolean(activeSession.value.hostname && activeSession.value.username && hasSecret.value));
const connectionHint = computed(() => u_Permission.value !== 'root' ? '需要服务端管理员身份' : activeSession.value.state === 'connected' ? '当前标签已连接' : '填写目标与认证材料后连接');
const summaryItems = computed(() => [{ label: '活动标签', value: `${sessions.length}/${MAX_SESSIONS}`, icon: Operation, color: '#22d3ee' }, { label: '目标地址', value: activeSession.value.hostname ? `${activeSession.value.hostname}:${activeSession.value.port}` : '未指定', icon: Monitor, color: '#10f5a0' }, { label: '会话用户', value: activeSession.value.username || '未指定', icon: User, color: '#a855f7' }, { label: '认证方式', value: activeSession.value.authType === 'key' ? 'SSH 私钥' : '密码认证', icon: Setting, color: '#ffb020' }]);
const stateLabel = (state: TerminalConnectionState) => ({ idle: '等待连接', authenticating: '认证中', connecting: '建立通道', connected: '会话在线', closed: '已关闭', failed: '连接失败' })[state];

function sanitizeHistory(value: unknown): TerminalHistoryItem[] {
	if (!Array.isArray(value)) return [];
	return value.filter((item) => item && typeof item === 'object').map((item) => item as Record<string, unknown>).filter((item) => typeof item.hostname === 'string' && typeof item.username === 'string' && (item.authType === 'password' || item.authType === 'key')).slice(0, 20).map((item) => ({ hostname: String(item.hostname), port: Number(item.port) || 22, username: String(item.username), authType: item.authType as TerminalHistoryItem['authType'], connectedAt: typeof item.connectedAt === 'string' ? item.connectedAt : new Date().toISOString() }));
}
const historyKey = (item: TerminalHistoryItem) => `${item.username}@${item.hostname}:${item.port}:${item.authType}`;
const saveHistory = () => Local.set('terminalConnectionHistory', history.value.map(({ hostname, port, username, authType, connectedAt }) => ({ hostname, port, username, authType, connectedAt })));
const recordHistory = (session: TerminalSessionModel) => { const item = { hostname: session.hostname, port: session.port, username: session.username, authType: session.authType, connectedAt: new Date().toISOString() }; history.value = [item, ...history.value.filter((entry) => historyKey(entry) !== historyKey(item))].slice(0, 20); saveHistory(); };
const removeHistory = (item: TerminalHistoryItem) => { history.value = history.value.filter((entry) => historyKey(entry) !== historyKey(item)); saveHistory(); };
const addSession = (profile?: Partial<TerminalHistoryItem>) => { if (sessions.length >= MAX_SESSIONS) return; const session = makeSession(profile); sessions.push(session); activeId.value = session.id; nextTick(() => activePane.value?.focus()); };
const reconnectHistory = (item: TerminalHistoryItem) => addSession(item);
const activateSession = (id: string) => { activeId.value = id; nextTick(() => activePane.value?.focus()); };
const closeSession = (id: string) => { const index = sessions.findIndex((item) => item.id === id); if (index < 0 || sessions.length === 1) return; sessions.splice(index, 1); if (activeId.value === id) activeId.value = sessions[Math.max(0, index - 1)].id; };
const updateSession = (id: string, patch: Partial<TerminalSessionModel>) => { const session = sessions.find((item) => item.id === id); if (session) Object.assign(session, patch); };
const formatTime = (value: string) => new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date(value));
watch(() => appearance.background, () => { const theme = themes.find((item) => item.background === appearance.background); if (theme) appearance.foreground = theme.foreground; });
watch(appearance, () => Local.set('terminalConfig', { ...appearance }), { deep: true });
onMounted(async () => { document.documentElement.classList.add('theme-tech-dark'); await permissionStore.refreshUserPermission(); const token = await getToken(); Cookies.set('csrftoken', token.csrftoken); nextTick(() => { const scroll = document.querySelector<HTMLElement>('.layout-main-scroll.el-scrollbar__wrap'); if (scroll) scroll.scrollTop = 0; activePane.value?.focus(); }); });
onBeforeUnmount(() => { paneRefs.value.forEach((pane) => pane.disconnect()); if (!themeConfig.value.isTechTheme) document.documentElement.classList.remove('theme-tech-dark'); });
</script>

<style lang="scss">
@use './tech-terminal.scss';
</style>
