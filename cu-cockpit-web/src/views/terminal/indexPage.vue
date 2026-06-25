<template>

</template>
<script lang="ts" setup name="terminalIndex">

import { onMounted, onBeforeUnmount, ref, reactive, watch, nextTick } from 'vue';
import { FormInstance, FormRules } from 'element-plus';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';
import { Local } from '/@/utils/storage';
import websocket from '/@/utils/websocket';
import { connect, check, getToken } from '/@/api/terminal';
import Cookies from 'js-cookie';
import { debounce } from 'lodash';

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
const submitConnectForm = async (formEl: FormInstance | undefined) => {
    if (!formEl) return;
    await formEl.validate(async (valid) => {
        if (valid) {
            btnLoading.value = true;
            term_connecting();
            try {
                const res = await connect(connectForm);
                // 认证成功
                if (res.id) {
                    const resCheck = await check();
                    // 检查成功，开始连接
                    if (resCheck.ok === true) {
                        websocket.init(onmessage, onclose, `/api/terminal/ws?id=${res.id}`);
                        btnLoading.value = false;
                        isConnected.value = true;
                        termResized = true;
                        term_connected();
                        return;
                    }
                }
                // 认证失败或检查失败
                if (res.status || !isConnected.value) {
                    btnLoading.value = false;
                    isConnected.value = false;
                    term_fail(String(res.status) || 'check failed.');
                }
            } catch (error) {
                btnLoading.value = false;
                isConnected.value = false;
                term_fail();
                console.error('connect error: ', error);
            }
        }
    })
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

watch(() => [form.value.fontSize, form.value.background], () => {
    form.value.foreground = backgroundOption.find(v => v.background === form.value.background)?.foreground
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
let termResized = true;
let style = { width: 0, height: 0 };
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

    term.onData(data => {
        websocket.send(JSON.stringify({ 'data': data }));
    });
}

const onmessage = (msg: { data: Blob }) => {
    read_file_as_text(msg.data, term_write, decoder);
};
const onclose = () => {
    term.reset();
    term.writeln('Connection closed.');
    isConnected.value = false;
};
const term_write = (text: string | Uint8Array) => {
    if (term) {
        term.write(text);
        if (termResized) {
            resize_terminal();
            termResized = false;
        }
    }
};

// 给ws发送终端尺寸
const term_resize = (cols: number, rows: number) => {
    if (cols !== term.cols || rows !== term.rows || termResized) {
        term.resize(cols, rows);
        websocket.send(JSON.stringify({ 'resize': [cols, rows] }));
    }
};

// 获取字符宽高
const get_cell_size = () => {
    // @ts-expect-error
    style.width = term._core._renderService.dimensions.css.cell.width;
    // @ts-expect-error
    style.height = term._core._renderService.dimensions.css.cell.height;
};

// 计算终端行列数
const current_geometry = () => {
    get_cell_size();
    const box = document.querySelector('.terminal-box');
    if (!box) return { cols: 0, rows: 0 };
    let cols = Math.floor(box.getBoundingClientRect().width / style.width) - 1;
    let rows = Math.floor(box.getBoundingClientRect().height / style.height);
    return { cols, rows };
};

// 终端尺寸改变
const handleResize = debounce((style: { width: number; height: number }) => {
    if (style.width && style.height) {
        resize_terminal();
    }
}, 200);

const resize_terminal = () => {
    let geometry = current_geometry();
    term_resize(geometry.cols, geometry.rows);
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
    getCsrftoken();
    initTerm();
})

onBeforeUnmount(() => {
    websocket.close();
    term?.dispose();
})
</script>
<style scoped lang="scss">
</style>