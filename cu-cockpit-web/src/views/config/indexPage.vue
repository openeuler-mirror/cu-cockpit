<template>
    <div class="tech-config config-container">
        <header class="config-hud">
            <div class="config-identity">
                <span class="config-identity__mark"><el-icon><Setting /></el-icon></span>
                <div>
                    <h1 class="config-title">系统配置</h1>
                    <div class="config-kicker">SYSTEM CONFIGURATION · IDENTITY / TIME / SECURITY</div>
                </div>
            </div>
            <div class="config-hud__actions">
                <div v-if="!configError" class="config-status">
                    <span class="config-status__dot"></span>
                    <span>{{ configLoading ? '同步中' : '配置在线' }}</span>
                </div>
                <el-button class="config-action" :icon="Refresh" :loading="configLoading || fileLoading" @click="refreshConfig">
                    刷新
                </el-button>
            </div>
        </header>

        <section class="config-summary" aria-label="系统配置摘要">
            <div
                v-for="item in summaryItems"
                :key="item.label"
                class="config-summary__item"
                :style="{ '--summary-accent': item.color }"
            >
                <span class="config-summary__icon"><el-icon><component :is="item.icon" /></el-icon></span>
                <div class="config-summary__content">
                    <div class="config-summary__label">{{ item.label }}</div>
                    <div class="config-summary__value" :title="String(item.value)">{{ item.value }}</div>
                </div>
            </div>
        </section>

        <section v-if="configError && !configLoading" class="config-error">
            <el-icon><WarningFilled /></el-icon>
            <p>{{ configError }}</p>
            <el-button class="config-action" :icon="Refresh" @click="getConfig">重新加载</el-button>
        </section>

        <section class="config-control-panel" v-loading="configLoading">
            <div class="config-panel__head">
                <div>
                    <h2 class="config-panel__title">系统控制</h2>
                    <div class="config-panel__meta">HOST IDENTITY · CLOCK · SSH TRUST</div>
                </div>
                <span class="config-access" :class="{ 'is-admin': isAdmin }">
                    <el-icon><Lock /></el-icon>{{ isAdmin ? '管理员写入权限' : '受限访问 · 只读' }}
                </span>
            </div>
            <div class="config-control-grid">
                <article v-for="item in controlItems" :key="item.key" class="config-control-card">
                    <div class="config-control-card__top">
                        <span class="config-control-card__icon" :style="{ '--control-accent': item.color }">
                            <el-icon><component :is="item.icon" /></el-icon>
                        </span>
                        <span class="config-control-card__code">{{ item.code }}</span>
                    </div>
                    <div class="config-control-card__label">{{ item.label }}</div>
                    <div class="config-control-card__value" :title="item.value">{{ item.value }}</div>
                    <div class="config-control-card__footer">
                        <span>{{ item.detail }}</span>
                        <el-button
                            class="config-card-action"
                            :icon="item.edit ? Edit : View"
                            @click="showDetail(item.key)"
                        >
                            {{ item.edit ? '修改' : '查看' }}
                        </el-button>
                    </div>
                </article>
            </div>
        </section>

        <section class="config-file-panel">
            <div class="config-panel__head config-file-head">
                <div>
                    <h2 class="config-panel__title">配置文件工作台</h2>
                    <div class="config-panel__meta">MANAGED FILE · REVIEW BEFORE WRITE</div>
                </div>
                <span class="config-file-mode" :class="{ 'is-editing': updateFile && isAdmin }">
                    <span></span>{{ updateFile && isAdmin ? '编辑模式' : '只读模式' }}
                </span>
            </div>
            <div class="config-file-toolbar">
                <el-select
                    v-model="fileName"
                    class="config-file-select"
                    placeholder="请选择配置文件"
                    :disabled="updateFile || fileLoading || fileSaving"
                >
                    <el-option v-for="item in options" :key="item.value" :label="item.value" :value="item.value" />
                </el-select>
                <div class="config-file-actions">
                    <el-button
                        class="config-action"
                        :icon="View"
                        :loading="fileLoading"
                        :disabled="!fileName || updateFile || fileSaving"
                        @click="changeFile(false)"
                    >
                        查看文件
                    </el-button>
                    <el-button
                        class="config-action config-action--edit"
                        :icon="Edit"
                        :disabled="!fileName || updateFile || fileLoading || fileSaving"
                        @click="changeFile(true)"
                    >
                        编辑文件
                    </el-button>
                </div>
            </div>
            <div class="config-editor-shell" v-loading="fileLoading">
                <div v-if="fileError && !fileLoading" class="config-file-error">
                    <el-icon><WarningFilled /></el-icon>
                    <span>{{ fileError }}</span>
                    <el-button class="config-action" @click="getFile(fileName)">重新读取</el-button>
                </div>
                <el-input
                    v-else
                    v-model="fileContent"
                    class="config-editor"
                    :class="{ 'is-editing': updateFile && isAdmin }"
                    :rows="21"
                    type="textarea"
                    spellcheck="false"
                    :disabled="!updateFile || !isAdmin"
                    placeholder="选择配置文件后查看内容"
                />
            </div>
            <div v-if="updateFile && isAdmin" class="config-save-bar">
                <div class="config-save-note"><el-icon><WarningFilled /></el-icon>保存前请确认配置语法正确</div>
                <div>
                    <el-button class="config-action" :disabled="fileSaving" @click="cancelFile">取消编辑</el-button>
                    <el-button class="config-action config-action--save" :loading="fileSaving" @click="saveFile">保存配置</el-button>
                </div>
            </div>
        </section>

        <el-drawer v-model="hostDrawer" class="config-drawer" title="修改主机名" direction="rtl" size="min(460px, 92vw)">
            <el-form ref="hostFormRef" label-position="top" label-width="100px" :model="hostForm" :rules="hostRules"
                class="drawer-content">
                <el-form-item label="主机名" prop="hostname">
                    <el-input v-model="hostForm.hostname" placeholder="请输入主机名" clearable spellcheck="false" />
                </el-form-item>
                <el-form-item class="btn-row">
                    <el-button type="primary" @click="submitHostForm(hostFormRef)" :loading="hostSaving">保存</el-button>
                    <el-button @click="hostDrawer = false">取消</el-button>
                </el-form-item>
            </el-form>
        </el-drawer>
        <el-drawer v-model="timeDrawer" class="config-drawer" title="修改系统时间" direction="rtl" size="min(460px, 92vw)">
            <el-form ref="timeFormRef" label-position="top" label-width="100px" :model="timeForm" :rules="timeRules"
                class="drawer-content">
                <el-form-item label="时区" prop="zone">
                    <el-input v-model="timeForm.zone" disabled />
                </el-form-item>
                <el-form-item label="设置时间" prop="type">
                    <el-select v-model="timeForm.type" @change="handleType">
                        <el-option v-for="item in timeTypeOptions" :key="item.value" :label="item.label"
                            :value="item.value" />
                    </el-select>
                </el-form-item>
                <el-form-item v-if="timeForm.type === 'settime'" prop="time">
                    <el-date-picker v-model="timeForm.time" type="datetime" placeholder="请选择时间" style="width: 100%;"
                        value-format="YYYY-MM-DD HH:mm:ss" />
                </el-form-item>
                <el-form-item class="btn-row">
                    <el-button type="primary" @click="submitTimeForm(timeFormRef)" :loading="timeSaving">保存</el-button>
                    <el-button @click="timeDrawer = false">取消</el-button>
                </el-form-item>
            </el-form>
        </el-drawer>
        <el-drawer v-model="keyDrawer" class="config-drawer config-key-drawer" title="主机 SSH 密钥指纹" direction="rtl" size="min(560px, 94vw)">
            <div class="drawer-content config-key-list">
                <article v-for="item in state.sshkeys" :key="item.name" class="config-key-item">
                    <div class="config-key-item__head"><el-icon><Key /></el-icon>{{ item.name }}</div>
                    <div class="config-fingerprint"><span>MD5</span><code>{{ item.md5 }}</code></div>
                    <div class="config-fingerprint"><span>SHA256</span><code>{{ item.sha256 }}</code></div>
                </article>
                <div v-if="!state.sshkeys.length" class="config-key-empty">未检测到 SSH 主机密钥</div>
            </div>
        </el-drawer>
    </div>
</template>

<script lang="ts" setup name="configIndex">
import { computed, nextTick, onMounted, onUnmounted, reactive, ref } from 'vue';
import { Clock, Edit, Key, Lock, Monitor, Refresh, Setting, View, WarningFilled } from '@element-plus/icons-vue';
import { configGet, hostSet, timeSet, configUpdate } from '/@/api/config/config';
import type { FormInstance, FormRules } from 'element-plus';
import { ElMessage, ElMessageBox } from 'element-plus';
import dayjs from 'dayjs';
import { storeToRefs } from 'pinia';
import { useThemeConfig } from '/@/stores/themeConfig';
import { userPermissiom } from '/@/stores/userPermissiom';

const storeUserPermissiom = userPermissiom();
const { u_Permission } = storeToRefs(storeUserPermissiom);
const themeStore = useThemeConfig();
const { themeConfig } = storeToRefs(themeStore);

const isAdmin = computed(() => u_Permission.value === 'root');

interface State {
    hostname: string;
    time: string;
    zone: string;
    type: string;
    sshkeys: Array<{ name: string, md5: string, sha256: string }>;
}
const state = reactive<State>({
    hostname: '',
    time: '',
    zone: '',
    type: '',
    sshkeys: []
});

type ControlKey = 'hostname' | 'time' | 'sshkey';

const configLoading = ref(false);
const configError = ref('');
const fileLoading = ref(false);
const fileSaving = ref(false);
const fileError = ref('');
const hostSaving = ref(false);
const timeSaving = ref(false);

const summaryItems = computed(() => [
    { label: '主机标识', value: state.hostname || '—', icon: Monitor, color: '#22d3ee' },
    { label: '时间同步', value: state.type === 'autotime' ? 'NTP 自动' : state.type === 'settime' ? '手动设置' : '—', icon: Clock, color: '#a855f7' },
    { label: 'SSH 主机密钥', value: `${state.sshkeys.length} 组`, icon: Key, color: '#10f5a0' },
    { label: '访问模式', value: isAdmin.value ? '管理员' : '受限访问', icon: Lock, color: isAdmin.value ? '#ffb020' : '#ff4d6d' },
]);

const controlItems = computed(() => [
    {
        label: '主机名',
        key: 'hostname' as ControlKey,
        code: 'HOST ID',
        value: state.hostname || '等待同步',
        detail: isAdmin.value ? '可修改系统主机标识' : '需要管理员权限',
        icon: Monitor,
        edit: true,
        color: '#22d3ee',
    },
    {
        label: '系统时间',
        key: 'time' as ControlKey,
        code: state.type === 'autotime' ? 'NTP SYNC' : 'MANUAL CLOCK',
        value: state.time || '等待同步',
        detail: state.zone || '时区未知',
        icon: Clock,
        edit: true,
        color: '#a855f7',
    },
    {
        label: 'SSH 主机密钥',
        key: 'sshkey' as ControlKey,
        code: 'TRUST KEYS',
        value: `${state.sshkeys.length} 组指纹`,
        detail: '查看 MD5 / SHA256 指纹',
        icon: Key,
        edit: false,
        color: '#10f5a0',
    },
]);

const applyTimeResponse = (response: { time: string; zone: string; ntp: string }) => {
    state.time = response.time;
    state.zone = response.zone;
    state.type = response.ntp === 'true' ? 'autotime' : 'settime';
};

const getConfig = async () => {
    configLoading.value = true;
    configError.value = '';
    try {
        const [hostname, time, sshkeys] = await Promise.all([
            configGet('gethostname'),
            configGet('time'),
            configGet('sshkey'),
        ]);
        state.hostname = hostname.trim();
        applyTimeResponse(time);
        state.sshkeys = sshkeys.map((item) => {
            const name = Object.keys(item)[0];
            return { name, ...item[name] };
        });
    } catch (error) {
        configError.value = '系统配置加载失败，请检查配置服务后重试。';
        console.error('获取系统配置失败:', error);
    } finally {
        configLoading.value = false;
    }
};

const getTime = async () => {
    try {
        applyTimeResponse(await configGet('time'));
    } catch (error) {
        console.error('刷新系统时间失败:', error);
    }
};

const options = [
    {
        value: '.bashrc',
    }
]
const fileName = ref('.bashrc');
const updateFile = ref(false);
const fileContent = ref('');

const changeFile = async (flag: boolean) => {
    if (flag && !isAdmin.value) {
        ElMessageBox.alert('被限制访问模式下不可操作，请切换到管理员模式', '提示', {
            confirmButtonText: '确定',
            callback: () => {
            }
        })
        return;
    }
    updateFile.value = flag;
    await getFile(fileName.value);
};

const getFile = async (name: string) => {
    if (!name) return;
    fileLoading.value = true;
    fileError.value = '';
    try {
        fileContent.value = await configGet('get', name);
    } catch (error) {
        fileError.value = `读取 ${name} 失败，请重试。`;
        console.error('读取配置文件失败:', error);
    } finally {
        fileLoading.value = false;
    }
};

const saveFile = async () => {
    try {
        await ElMessageBox.confirm('是否确认修改？', '温馨提示', {
            confirmButtonText: '确认',
            cancelButtonText: '取消',
            type: 'warning',
        })
        fileSaving.value = true;
        const response = await configUpdate(fileContent.value, fileName.value, '');
        ElMessage.success(response.message);
        updateFile.value = false;
        await getFile(fileName.value);
    } catch (error) {
        if (error !== 'cancel' && error !== 'close') console.error('保存配置文件失败:', error);
    } finally {
        fileSaving.value = false;
    }
};
const cancelFile = () => {
    updateFile.value = false;
    getFile(fileName.value);
};

const refreshConfig = async () => {
    await getConfig();
    if (fileName.value) await getFile(fileName.value);
};

const hostDrawer = ref(false);
const timeDrawer = ref(false);
const keyDrawer = ref(false);

const showDetail = (key: ControlKey) => {
    if (key === 'hostname') {
        if (!isAdmin.value) {
            ElMessageBox.alert('被限制访问模式下不可操作，请切换到管理员模式', '提示', {
                confirmButtonText: '确定',
                callback: () => {
                }
            })
            return;
        }
        hostDrawer.value = true;
        hostForm.hostname = state.hostname;
        // 重置表单校验状态
        if (hostFormRef.value) {
            hostFormRef.value.clearValidate();
        }
    } else if (key === 'time') {
        if (!isAdmin.value) {
            ElMessageBox.alert('被限制访问模式下不可操作，请切换到管理员模式', '提示', {
                confirmButtonText: '确定',
                callback: () => {
                }
            })
            return;
        }
        timeDrawer.value = true;
        timeForm.time = dayjs().format('YYYY-MM-DD HH:mm:ss');
        timeForm.zone = state.zone;
        timeForm.type = state.type;

        // 重置表单校验状态
        if (timeFormRef.value) {
            timeFormRef.value.clearValidate();
        }
    } else if (key === 'sshkey') {
        keyDrawer.value = true;
    }
};

interface HostRuleForm {
    hostname: string
}
const hostForm = reactive<HostRuleForm>({
    hostname: '',
})
const hostFormRef = ref<FormInstance>()
const hostRules = reactive<FormRules<HostRuleForm>>({
    hostname: [
        { required: true, message: '请输入主机名', trigger: 'blur' },
    ],
});
const submitHostForm = async (formEl: FormInstance | undefined) => {
    if (!formEl) return;
    const valid = await formEl.validate().catch(() => false);
    if (!valid) return;
    hostSaving.value = true;
    try {
        const response = await hostSet(hostForm);
        ElMessage.success(response.message);
        hostDrawer.value = false;
        await getConfig();
    } catch (error) {
        console.error('修改主机名失败:', error);
    } finally {
        hostSaving.value = false;
    }
};

const timeTypeOptions = [
    { value: 'settime', label: '手动的' },
    { value: 'autotime', label: '自动使用NTP' },
]

interface TimeRuleForm {
    zone: string,
    type: string,
    time: string,
}
const timeForm = reactive<TimeRuleForm>({
    zone: '',
    type: '',
    time: '',
})
const timeFormRef = ref<FormInstance>()
const timeRules = reactive<FormRules<TimeRuleForm>>({
    zone: [
        { required: true, message: '请输入时区', trigger: 'blur' },
    ],
    type: [
        { required: true, message: '请选择时间类型', trigger: 'change' },
    ],
    time: [
        { required: true, message: '请选择时间', trigger: 'change' },
    ],
});
const submitTimeForm = async (formEl: FormInstance | undefined) => {
    if (!formEl) return;
    const valid = await formEl.validate().catch(() => false);
    if (!valid) return;
    timeSaving.value = true;
    try {
        const response = await timeSet({
            type: timeForm.type,
            time: `${timeForm.time} +0800`,
        });
        ElMessage.success(response.message);
        timeDrawer.value = false;
        await getConfig();
        postTimeRefreshTimer = window.setTimeout(getConfig, 7000);
    } catch (error) {
        console.error('修改系统时间失败:', error);
    } finally {
        timeSaving.value = false;
    }
};

const handleType = (value: string) => {
    if (value === 'settime') {
        timeForm.time = dayjs().format('YYYY-MM-DD HH:mm:ss');
    }
};

const mountConfigTechShell = () => document.documentElement.classList.add('theme-tech-dark');
const restoreConfigTechShell = () => {
    if (!themeConfig.value.isTechTheme) document.documentElement.classList.remove('theme-tech-dark');
};
const resetMainScroll = async () => {
    await nextTick();
    const scrollContainer = document.querySelector<HTMLElement>('.layout-main-scroll.el-scrollbar__wrap');
    if (scrollContainer) scrollContainer.scrollTop = 0;
};

let timer: number | undefined;
let postTimeRefreshTimer: number | undefined;
onMounted(() => {
    mountConfigTechShell();
    resetMainScroll();
    getConfig();
    getFile(fileName.value);
    timer = window.setInterval(getTime, 30000);
});
onUnmounted(() => {
    window.clearInterval(timer);
    window.clearTimeout(postTimeRefreshTimer);
    restoreConfigTechShell();
});
</script>

<style lang="scss">
@use './tech-config.scss';
</style>
