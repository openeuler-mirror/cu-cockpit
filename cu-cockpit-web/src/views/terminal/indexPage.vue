<template>
    <div class="tech-terminal terminal-container">
        <header class="terminal-hud">
            <div class="terminal-identity">
                <span class="terminal-identity__mark"><el-icon><Operation /></el-icon></span>
                <div>
                    <h1 class="terminal-title">Web 终端</h1>
                    <div class="terminal-kicker">REMOTE SHELL · SSH SESSION / XTERM CONSOLE</div>
                </div>
            </div>
            <div class="terminal-hud__actions">
                <div class="terminal-status" :class="`is-${connectionState}`">
                    <span class="terminal-status__dot"></span>
                    <span>{{ connectionStatus.label }}</span>
                </div>
                <el-button
                    class="terminal-action terminal-action--disconnect"
                    :icon="SwitchButton"
                    :disabled="!isConnected"
                    @click="disconnectTerminal"
                >
                    断开
                </el-button>
            </div>
        </header>

        <section class="terminal-summary" aria-label="终端会话摘要">
            <div
                v-for="item in summaryItems"
                :key="item.label"
                class="terminal-summary__item"
                :style="{ '--summary-accent': item.color }"
            >
                <span class="terminal-summary__icon"><el-icon><component :is="item.icon" /></el-icon></span>
                <div>
                    <div class="terminal-summary__label">{{ item.label }}</div>
                    <div class="terminal-summary__value" :title="item.value">{{ item.value }}</div>
                </div>
            </div>
        </section>

        <section class="terminal-connect-panel">
            <div class="terminal-panel__head">
                <div>
                    <h2 class="terminal-panel__title">建立 SSH 会话</h2>
                    <div class="terminal-panel__meta">TARGET AUTHENTICATION · PASSWORD IS NEVER STORED</div>
                </div>
                <div class="terminal-connection-detail">
                    <span>{{ connectionStatus.detail }}</span>
                </div>
            </div>

            <el-form
                ref="connectFormRef"
                :model="connectForm"
                :rules="connectRules"
                class="terminal-connect-form"
                label-position="top"
                @submit.prevent="submitConnectForm(connectFormRef)"
            >
                <div class="terminal-connect-grid">
                    <el-form-item label="目标 IP / 主机名" prop="hostname">
                        <el-input
                            v-model="connectForm.hostname"
                            class="terminal-control"
                            placeholder="例如 192.168.1.10"
                            spellcheck="false"
                            :disabled="btnLoading || isConnected"
                        />
                    </el-form-item>
                    <el-form-item label="端口" prop="port">
                        <el-input-number
                            v-model="connectForm.port"
                            class="terminal-control terminal-port-control"
                            :min="1"
                            :max="65535"
                            controls-position="right"
                            :disabled="btnLoading || isConnected"
                        />
                    </el-form-item>
                    <el-form-item label="用户名" prop="username">
                        <el-input
                            v-model="connectForm.username"
                            class="terminal-control"
                            placeholder="SSH 用户名"
                            spellcheck="false"
                            :disabled="btnLoading || isConnected"
                        />
                    </el-form-item>
                    <el-form-item label="密码" prop="password">
                        <el-input
                            v-model="connectForm.password"
                            class="terminal-control"
                            :type="showPassword ? 'text' : 'password'"
                            placeholder="SSH 密码"
                            spellcheck="false"
                            autocomplete="new-password"
                            :disabled="btnLoading || isConnected"
                        >
                            <template #suffix>
                                <el-tooltip :content="showPassword ? '隐藏密码' : '显示密码'" placement="top">
                                    <el-icon class="terminal-password-toggle" @click="showPassword = !showPassword">
                                        <View v-if="showPassword" />
                                        <Hide v-else />
                                    </el-icon>
                                </el-tooltip>
                            </template>
                        </el-input>
                    </el-form-item>
                </div>

                <div class="terminal-connect-actions">
                    <div v-if="connectionState === 'failed'" class="terminal-connect-error">
                        <el-icon><WarningFilled /></el-icon>
                        <span>{{ connectionError || connectionStatus.detail }}</span>
                    </div>
                    <span v-else class="terminal-security-note">凭据仅用于本次连接，不写入浏览器存储</span>
                    <el-button
                        class="terminal-action terminal-action--primary"
                        :icon="Connection"
                        :loading="btnLoading"
                        :disabled="isConnected"
                        native-type="submit"
                    >
                        {{ connectionState === 'closed' || connectionState === 'failed' ? '重新连接' : '连接终端' }}
                    </el-button>
                </div>
            </el-form>
        </section>

        <section class="terminal-session-panel">
            <div class="terminal-panel__head">
                <div>
                    <h2 class="terminal-panel__title">交互式终端</h2>
                    <div class="terminal-panel__meta">{{ connectionTarget }} · {{ terminalGeometry }}</div>
                </div>
                <div class="terminal-session-actions">
                    <el-button class="terminal-action" :icon="Delete" :disabled="!isConnected" @click="term_clear">清屏</el-button>
                </div>
            </div>

            <div class="terminal-workspace">
                <div class="terminal-screen-shell" :class="`is-${connectionState}`">
                    <div class="terminal-screen-bar">
                        <div class="terminal-window-dots" aria-hidden="true"><span></span><span></span><span></span></div>
                        <span>{{ connectionTarget }}</span>
                        <span class="terminal-screen-bar__status">{{ connectionStatus.label }} · {{ terminalGeometry }}</span>
                    </div>
                    <div ref="terminalRef" class="terminal-box" v-resize-ob="handleResize"></div>
                </div>

                <aside class="terminal-settings">
                    <div class="terminal-settings__title"><el-icon><Setting /></el-icon>显示设置</div>
                    <el-form :model="form" label-position="top">
                        <el-form-item label="字体大小">
                            <el-select v-model="form.fontSize" class="terminal-control" placeholder="字体大小">
                                <el-option v-for="item in fontSizeOption" :key="item" :label="`${item} px`" :value="item" />
                            </el-select>
                        </el-form-item>
                        <el-form-item label="终端配色">
                            <el-select v-model="form.background" class="terminal-control" placeholder="终端配色">
                                <el-option
                                    v-for="item in backgroundOption"
                                    :key="item.background"
                                    :label="item.lable"
                                    :value="item.background"
                                >
                                    <span class="terminal-theme-option">
                                        <span class="terminal-theme-swatch" :style="{ background: item.background, color: item.foreground }">Aa</span>
                                        {{ item.lable }}
                                    </span>
                                </el-option>
                            </el-select>
                        </el-form-item>
                    </el-form>
                    <div class="terminal-settings__facts">
                        <span><small>TERM</small><strong>{{ connectForm.term }}</strong></span>
                        <span><small>编码</small><strong>UTF-8</strong></span>
                    </div>
                </aside>
            </div>
        </section>
    </div>
</template>

<script lang="ts" setup name="terminalIndex">
import { computed, onMounted, onBeforeUnmount, ref, reactive, watch, nextTick } from 'vue';
import { Connection, Delete, Hide, Monitor, Operation, Setting, SwitchButton, User, View, WarningFilled } from '@element-plus/icons-vue';
import { FormInstance, FormRules } from 'element-plus';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';
import { storeToRefs } from 'pinia';
import { Local } from '/@/utils/storage';
import websocket from '/@/utils/websocket';
import { connect, check, getToken } from '/@/api/terminal';
import { useThemeConfig } from '/@/stores/themeConfig';
import Cookies from 'js-cookie';
import { debounce } from 'lodash';

type ConnectionState = 'idle' | 'authenticating' | 'connecting' | 'connected' | 'closed' | 'failed';

interface ConnectRuleForm {
    hostname: string,
    port: number,
    username: string,
    password: string,
    term: string
}

const connectForm = reactive<ConnectRuleForm>({
    hostname: '',
    port: 22,
    username: '',
    password: '',
    term: 'xterm-256color'
})

const themeStore = useThemeConfig();
const { themeConfig } = storeToRefs(themeStore);

const connectFormRef = ref<FormInstance>();
const connectRules = reactive<FormRules<ConnectRuleForm>>({
    hostname: [
        { required: true, message: '请输入IP', trigger: 'blur' },
    ],
    port: [
        { required: true, message: '请输入端口', trigger: 'blur' },
    ],
    username: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
    ],
    password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
    ],
});
const showPassword = ref(false);
const btnLoading = ref(false);
const isConnected = ref(false);
const connectionState = ref<ConnectionState>('idle');
const connectionError = ref('');
let connectionAttempt = 0;

const connectionStateMap: Record<ConnectionState, { label: string; detail: string }> = {
    idle: { label: '等待连接', detail: '输入目标主机凭据后建立 SSH 会话' },
    authenticating: { label: '认证中', detail: '正在验证目标主机凭据' },
    connecting: { label: '建立通道', detail: '认证成功，正在打开 WebSocket 通道' },
    connected: { label: '会话在线', detail: 'SSH 通道已连接，可输入终端命令' },
    closed: { label: '会话已关闭', detail: '连接已断开，可重新建立会话' },
    failed: { label: '连接失败', detail: '请检查目标地址、端口和凭据后重试' },
};
const connectionStatus = computed(() => connectionStateMap[connectionState.value]);

const markConnected = (attempt: number) => {
    if (attempt !== connectionAttempt || connectionState.value === 'connected') return;
    btnLoading.value = false;
    isConnected.value = true;
    connectionState.value = 'connected';
    connectionError.value = '';
    term_connected();
    nextTick(resize_terminal);
};

const markFailed = (attempt: number, message = 'Connection failed.') => {
    if (attempt !== connectionAttempt) return;
    btnLoading.value = false;
    isConnected.value = false;
    connectionState.value = 'failed';
    connectionError.value = message;
    term_fail(message);
};

const submitConnectForm = async (formEl: FormInstance | undefined) => {
    if (!formEl) return;
    const valid = await formEl.validate().catch(() => false);
    if (!valid) return;

    connectionAttempt += 1;
    const attempt = connectionAttempt;
    websocket.close();
    btnLoading.value = true;
    isConnected.value = false;
    connectionState.value = 'authenticating';
    connectionError.value = '';
    term_connecting();

    try {
        const response = await connect(connectForm);
        if (!response.id) throw new Error(String(response.status || 'Authentication failed.'));
        const sessionCheck = await check();
        if (sessionCheck.ok !== true) throw new Error('Session check failed.');

        connectionState.value = 'connecting';
        websocket.init(onmessage, () => onclose(attempt), `/api/terminal/ws?id=${response.id}`);
        const socket = websocket.websocket;
        if (!socket) throw new Error('WebSocket initialization failed.');

        socket.addEventListener('open', () => markConnected(attempt), { once: true });
        socket.addEventListener('error', () => markFailed(attempt, 'WebSocket connection failed.'), { once: true });
        if (socket.readyState === WebSocket.OPEN) markConnected(attempt);
    } catch (error) {
        const message = error instanceof Error ? error.message : 'Connection failed.';
        markFailed(attempt, message);
        console.error('connect error: ', error);
    }
};

const disconnectTerminal = () => {
    connectionAttempt += 1;
    websocket.close();
    btnLoading.value = false;
    isConnected.value = false;
    connectionState.value = 'closed';
    connectionError.value = '';
    term.reset();
    term.writeln('Connection closed.');
};

const { fontSize, background, foreground } = Local.get('terminalConfig') || {};
const form = ref({
    fontSize: fontSize || 18,
    background: background || '#000000',
    foreground: foreground || '#ffffff'
});

const fontSizeOption = [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48];
const backgroundOption = [
    {
        lable: '黑色',
        background: '#000000',
        foreground: '#ffffff'
    },
    {
        lable: '暗色',
        background: '#002B36',
        foreground: '#ffffff'
    },
    {
        lable: '亮色',
        background: '#FDF6E3',
        foreground: '#000000'
    },
    {
        lable: '白色',
        background: '#FFFFFF',
        foreground: '#000000'
    }
];

const terminalCols = ref(0);
const terminalRows = ref(0);
const connectionTarget = computed(() =>
    connectForm.hostname ? `${connectForm.hostname}:${connectForm.port}` : `未指定目标:${connectForm.port}`
);
const terminalGeometry = computed(() =>
    terminalCols.value > 0 && terminalRows.value > 0 ? `${terminalCols.value} COLS × ${terminalRows.value} ROWS` : '等待终端尺寸'
);
const appearanceLabel = computed(
    () => backgroundOption.find((item) => item.background === form.value.background)?.lable || '自定义'
);
const summaryItems = computed(() => [
    { label: '目标地址', value: connectionTarget.value, icon: Monitor, color: '#22d3ee' },
    { label: '会话用户', value: connectForm.username || '未指定', icon: User, color: '#a855f7' },
    { label: '终端尺寸', value: terminalGeometry.value, icon: Operation, color: '#10f5a0' },
    { label: '显示配置', value: `${form.value.fontSize}px · ${appearanceLabel.value}`, icon: Setting, color: '#ffb020' },
]);

watch(() => [form.value.fontSize, form.value.background], () => {
    form.value.foreground = backgroundOption.find(v => v.background === form.value.background)?.foreground
    if (!term) return;
    term.options.theme = {
        background: form.value.background,
        foreground: form.value.foreground,
        cursor: '#00FF00',
    };
    term.options.fontSize = form.value.fontSize;
    Local.set('terminalConfig', form.value);
    nextTick(() => term.focus());
    resize_terminal();
})

const terminalRef = ref<HTMLElement>();
let term: Terminal;
let fitAddon: FitAddon;
const encoding = 'utf-8';
const decoder = window.TextDecoder ? new window.TextDecoder(encoding) : encoding;

// 清屏
const term_clear = () => {
    term.clear();
    term.focus();
};

// 连接中
const term_connecting = () => {
    term.reset();
    term.writeln('Connecting...');
};

// 已连接
const term_connected = () => {
    term.reset();
    term.focus();
};

// 连接失败
const term_fail = (msg = 'Connection failed.') => {
    term.reset();
    term.writeln(msg);
};

const initTerm = () => {
    if (!terminalRef.value) return;

    term = new Terminal({
        cursorBlink: true,
        convertEol: true,
        cursorStyle: 'block',
        cursorInactiveStyle: 'underline',
        fontSize: form.value.fontSize,
        fontFamily: 'Menlo, Monaco, Consolas, Courier New, monospace',
        theme: {
            background: form.value.background,
            foreground: form.value.foreground,
            cursor: '#00FF00',
        },
    });

    fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.open(terminalRef.value);
    fitAddon.fit();
    terminalCols.value = term.cols;
    terminalRows.value = term.rows;

    term.onData(data => {
        if (isConnected.value) websocket.send(JSON.stringify({ 'data': data }));
    });
}

const onmessage = (msg: { data: Blob }) => {
    read_file_as_text(msg.data, term_write, decoder);
};
const onclose = (attempt = connectionAttempt) => {
    if (attempt !== connectionAttempt) return;
    btnLoading.value = false;
    term.reset();
    term.writeln('Connection closed.');
    isConnected.value = false;
    if (connectionState.value !== 'failed') connectionState.value = 'closed';
};
const term_write = (text: string | Uint8Array) => {
    if (term) {
        term.write(text);
    }
};

// 终端尺寸改变
const handleResize = debounce((size: { width: number; height: number }) => {
    if (size.width && size.height) {
        resize_terminal();
    }
}, 200);

const resize_terminal = () => {
    if (!term || !fitAddon || !terminalRef.value) return;
    fitAddon.fit();
    terminalCols.value = Math.max(term.cols, 1);
    terminalRows.value = Math.max(term.rows, 1);
    if (isConnected.value) {
        websocket.send(JSON.stringify({ 'resize': [terminalCols.value, terminalRows.value] }));
    }
};

// eslint-disable-next-line no-unused-vars
type TermWriteCallback = (_text: string | Uint8Array) => void;

const read_as_text_with_decoder = (file: Blob, callback: TermWriteCallback, decoder: TextDecoder) => {
    let reader = new window.FileReader();

    if (decoder === undefined) {
        decoder = new window.TextDecoder('utf-8', { 'fatal': true });
    }

    reader.onload = () => {
        let text: string | Uint8Array = '';
        try {
            if (reader.result instanceof ArrayBuffer) {
                text = decoder.decode(reader.result);
            } else {
                console.warn('Expected ArrayBuffer, got:', typeof reader.result);
            }
        } catch (error) {
            console.log('Decoding error happened.');
        } finally {
            if (callback) {
                callback(text);
            }
        }
    };

    reader.onerror = (e) => {
        console.error('reader decoder error: ', e);
    };

    reader.readAsArrayBuffer(file);
}

const read_as_text_with_encoding = (file: Blob, callback: TermWriteCallback, encoding: string) => {
    let reader = new window.FileReader();

    if (encoding === undefined) {
        encoding = 'utf-8';
    }

    reader.onload = () => {
        if (callback) {
            callback(reader.result as string | Uint8Array);
        }
    };

    reader.onerror = (e) => {
        console.error('reader encoding error: ', e);
    };

    reader.readAsText(file, encoding);
}

const read_file_as_text = (file: Blob, callback: TermWriteCallback, decoder: TextDecoder | string) => {
    if (!window.TextDecoder) {
        read_as_text_with_encoding(file, callback, decoder as string);
    } else {
        read_as_text_with_decoder(file, callback, decoder as TextDecoder);
    }
}
const getCsrftoken = () => {
    getToken().then(token => {
        Cookies.set('csrftoken', token.csrftoken);
    }).catch(error => {
        console.log('setToken error: ', error);
    })
}

onMounted(() => {
    document.documentElement.classList.add('theme-tech-dark');
    getCsrftoken();
    initTerm();
    nextTick(() => {
        const scrollContainer = document.querySelector<HTMLElement>('.layout-main-scroll.el-scrollbar__wrap');
        if (scrollContainer) scrollContainer.scrollTop = 0;
        resize_terminal();
    });
})

onBeforeUnmount(() => {
    connectionAttempt += 1;
    websocket.close();
    handleResize.cancel();
    term?.dispose();
    if (!themeConfig.value.isTechTheme) document.documentElement.classList.remove('theme-tech-dark');
})
</script>
<style lang="scss">
@use './tech-terminal.scss';
</style>