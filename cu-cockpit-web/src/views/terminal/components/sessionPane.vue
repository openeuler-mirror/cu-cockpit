<template>
	<div class="terminal-screen-shell" :class="`is-${currentState}`">
		<div class="terminal-screen-bar">
			<div class="terminal-window-dots" aria-hidden="true"><span></span><span></span><span></span></div>
			<span>{{ targetLabel }}</span>
			<span class="terminal-screen-bar__status">{{ stateLabel }} · {{ geometry }}</span>
		</div>
		<div ref="terminalRef" class="terminal-box"></div>
	</div>
</template>

<script setup lang="ts" name="terminalSessionPane">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';
import { connect as requestConnection } from '/@/api/terminal';
import type { TerminalSessionModel } from '../sessionTypes';

const props = defineProps<{ session: TerminalSessionModel; fontSize: number; background: string; foreground: string }>();
const emit = defineEmits<{
	connected: [session: TerminalSessionModel];
	state: [session: TerminalSessionModel];
	update: [sessionId: string, patch: Partial<TerminalSessionModel>];
}>();
const terminalRef = ref<HTMLElement>();
let terminal: Terminal | null = null;
let fitAddon: FitAddon | null = null;
let socket: WebSocket | null = null;
let resizeObserver: ResizeObserver | null = null;
let manualClose = false;
const currentState = ref<TerminalSessionModel['state']>(props.session.state);
const currentCols = ref(props.session.cols);
const currentRows = ref(props.session.rows);
const stateLabels = { idle: '等待连接', authenticating: '认证中', connecting: '建立通道', connected: '会话在线', closed: '会话已关闭', failed: '连接失败' };
const stateLabel = computed(() => stateLabels[currentState.value]);
const targetLabel = computed(() => props.session.hostname ? `${props.session.username || 'user'}@${props.session.hostname}:${props.session.port}` : '未指定目标');
const geometry = computed(() => currentCols.value && currentRows.value ? `${currentCols.value} COLS × ${currentRows.value} ROWS` : '等待尺寸');
const patchedSession = (patch: Partial<TerminalSessionModel>) => ({ ...props.session, ...patch });
const setState = (state: TerminalSessionModel['state'], error = '') => {
	currentState.value = state;
	emit('update', props.session.id, { state, error });
	emit('state', patchedSession({ state, error }));
};
const socketUrl = (workerId: string) => `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/api/terminal/ws?id=${encodeURIComponent(workerId)}`;
const resizeTerminal = () => {
	if (!terminal || !fitAddon || !terminalRef.value) return;
	fitAddon.fit();
	currentCols.value = Math.max(terminal.cols, 1);
	currentRows.value = Math.max(terminal.rows, 1);
	emit('update', props.session.id, { cols: currentCols.value, rows: currentRows.value });
	if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ resize: [currentCols.value, currentRows.value] }));
};
const disconnect = (showMessage = true) => { manualClose = true; if (socket && socket.readyState < WebSocket.CLOSING) socket.close(); socket = null; if (showMessage) { setState('closed'); terminal?.reset(); terminal?.writeln('Connection closed.'); } };
const connect = async () => {
	disconnect(false); manualClose = false; setState('authenticating'); terminal?.reset(); terminal?.writeln('Connecting...');
	try {
		const response = await requestConnection({ hostname: props.session.hostname, port: props.session.port, username: props.session.username, term: props.session.term, password: props.session.authType === 'password' ? props.session.password : undefined, privatekey: props.session.authType === 'key' ? props.session.privatekey : undefined, passphrase: props.session.authType === 'key' ? props.session.passphrase : undefined });
		if (!response.id) throw new Error(String(response.status || 'Authentication failed.'));
		setState('connecting'); socket = new WebSocket(socketUrl(response.id)); socket.binaryType = 'arraybuffer';
		socket.onopen = () => { setState('connected'); terminal?.reset(); terminal?.focus(); nextTick(resizeTerminal); emit('connected', patchedSession({ state: 'connected', error: '' })); };
		socket.onmessage = async (event) => { if (!terminal) return; if (event.data instanceof ArrayBuffer) terminal.write(new Uint8Array(event.data)); else if (event.data instanceof Blob) terminal.write(new Uint8Array(await event.data.arrayBuffer())); else terminal.write(String(event.data)); };
		socket.onerror = () => setState('failed', 'WebSocket connection failed.');
		socket.onclose = () => { if (!manualClose && currentState.value !== 'failed') setState('closed'); socket = null; };
	} catch (error) { const message = error instanceof Error ? error.message : 'Connection failed.'; setState('failed', message); terminal?.reset(); terminal?.writeln(message); }
};
const clear = () => { terminal?.clear(); terminal?.focus(); };
const focus = () => { terminal?.focus(); nextTick(resizeTerminal); };
onMounted(() => {
	if (!terminalRef.value) return;
	terminal = new Terminal({ cursorBlink: true, convertEol: true, cursorStyle: 'block', fontSize: props.fontSize, fontFamily: 'Menlo, Monaco, Consolas, Courier New, monospace', fontWeight: '500', fontWeightBold: '700', lineHeight: 1.1, theme: { background: props.background, foreground: props.foreground, cursor: '#00ff99' } });
	fitAddon = new FitAddon(); terminal.loadAddon(fitAddon); terminal.open(terminalRef.value); terminal.writeln('Session ready. Enter connection details above.');
	terminal.onData((data) => { if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ data })); });
	resizeObserver = new ResizeObserver(resizeTerminal); resizeObserver.observe(terminalRef.value); nextTick(resizeTerminal);
});
watch(() => [props.fontSize, props.background, props.foreground], () => { if (!terminal) return; terminal.options.fontSize = props.fontSize; terminal.options.theme = { background: props.background, foreground: props.foreground, cursor: '#00ff99' }; nextTick(resizeTerminal); });
onBeforeUnmount(() => { disconnect(false); resizeObserver?.disconnect(); terminal?.dispose(); terminal = null; });
defineExpose({ sessionId: props.session.id, connect, disconnect, clear, focus, resize: resizeTerminal });
</script>