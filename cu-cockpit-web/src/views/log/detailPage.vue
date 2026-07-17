<script lang="ts" setup name="logsDetail">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue';
import { ArrowLeft, Cpu, Document, Monitor, Service, WarningFilled } from '@element-plus/icons-vue';
import { storeToRefs } from 'pinia';
import { useRouter } from 'vue-router';
import { Local } from '/@/utils/storage';
import { logs } from '/@/api/log';
import { useThemeConfig } from '/@/stores/themeConfig';

// 定义日志配置项类型
interface LogConfigItem {
    key: string;
    label?: number | string;
}

interface LogContext {
    cursor?: string;
    servicename?: string;
    priority?: string;
}

type JournalRecord = Record<string, string | number>;

// 保存日志详情数据
const router = useRouter();
const themeStore = useThemeConfig();
const { themeConfig } = storeToRefs(themeStore);
const logContext = ref<LogContext>(Local.get('logsDetail') || {});
const logRecord = ref<JournalRecord>({});
const loading = ref(false);
const loadError = ref('');

// 显示配置
const logsConfig: LogConfigItem[] = [

    {
        label: '服务名称',
        key: 'logService',
    },
    {
        key: 'MESSAGE',
    },
    {
        key: 'CODE_FILE',
    },
    {
        key: 'INVOCATION_ID',
    },
    {
        key: 'JOB_ID',
    },
    {
        key: 'JOB_RESULT',
    },
    {
        key: 'JOB_TYPE',
    },
    {
        key: 'MESSAGE_ID',
    },
    {
        key: 'PRIORITY',
    },
    {
        key: 'SYSLOG_FACILITY',
    },
    {
        key: 'SYSLOG_IDENTIFIER',
    },
    {
        key: 'SYSLOG_RAW',
    },
    {
        key: 'SYSLOG_TIMESTAMP',
    },
    {
        key: 'TID',
    },
    {
        key: '_BOOT_ID'
    },
    {
        key: '_CAP_EFFECTIVE'
    },
    {
        key: '_CMDLINE'
    },
    {
        key: '_COMM'
    },
    {
        key: '_EXE'
    },
    {
        key: '_GID'
    },
    {
        key: '_HOSTNAME'
    },
    {
        key: '_MACHINE_ID'
    },
    {
        key: '_PID'
    },
    {
        key: '_RUNTIME_SCOPE'
    },
    {
        key: '_SOURCE_REALTIME_TIMESTAMP'
    },
    {
        key: '_SYSTEMD_CGROUP'
    },
    {
        key: '_SYSTEMD_INVOCATION_ID'
    },
    {
        key: '_SYSTEMD_SLICE'
    },
    {
        key: 'SYSLOG_IDENTIFIER'
    },
    {
        key: '_TRANSPORT'
    },
    {
        key: '_UID'
    },
    {
        key: '__CURSOR',
    },
    {
        key: '__MONOTONIC_TIMESTAMP'
    },
    {
        key: '__REALTIME_TIMESTAMP'
    },
    {
        key: '__SEQNUM'
    },
    {
        key: '__SEQNUM_ID'
    },
];

const priorityLabels: Record<string, string> = {
    '0': 'EMERG',
    '1': 'ALERT',
    '2': 'CRIT',
    '3': 'ERR',
    '4': 'WARNING',
    '5': 'NOTICE',
    '6': 'INFO',
    '7': 'DEBUG',
};
const priorityLabel = computed(() => priorityLabels[String(logRecord.value.PRIORITY ?? '')] || String(logRecord.value.PRIORITY || '—'));
const summaryItems = computed(() => [
    { label: '服务名称', value: String(logRecord.value.logService || logContext.value.servicename || '—'), icon: Service, color: '#22d3ee' },
    { label: '日志优先级', value: priorityLabel.value, icon: WarningFilled, color: '#ff4d6d' },
    { label: '来源主机', value: String(logRecord.value._HOSTNAME || '—'), icon: Monitor, color: '#10f5a0' },
    { label: '进程 PID', value: String(logRecord.value._PID || '—'), icon: Cpu, color: '#ffb020' },
]);
const logMessage = computed(() => String(logRecord.value.MESSAGE || '该日志未提供 MESSAGE 字段'));
const visibleMetadata = computed(() => {
    const hiddenKeys = new Set(['logService', 'MESSAGE']);
    const seenKeys = new Set<string>();
    return logsConfig
        .filter((item) => {
            const value = logRecord.value[item.key];
            if (hiddenKeys.has(item.key) || seenKeys.has(item.key) || value === undefined || value === null || value === '') return false;
            seenKeys.add(item.key);
            return true;
        })
        .map((item) => ({
            key: item.key,
            label: String(item.label || item.key),
            value: String(logRecord.value[item.key]),
        }));
});

const loadDetail = async () => {
    if (!logContext.value.cursor) {
        loadError.value = '缺少日志游标，无法加载详情。请返回日志列表重新选择记录。';
        return;
    }
    loading.value = true;
    loadError.value = '';
    try {
        const response = await logs({
            cursor: logContext.value.cursor,
            priority: logContext.value.priority,
            service: logContext.value.servicename,
            output_format: 'all_json',
        });
        const detail = response?.logs?.[0];
        if (!detail) throw new Error('日志详情为空');
        logRecord.value = {
            ...detail,
            logService: logContext.value.servicename || detail._SYSTEMD_UNIT || detail.UNIT || '—',
        };
    } catch (error) {
        logRecord.value = {};
        loadError.value = '日志详情加载失败，请返回列表后重试。';
        console.error('加载日志详情失败:', error);
    } finally {
        loading.value = false;
    }
};

const goBack = () => router.push({ name: 'logs' });
const mountLogTechShell = () => document.documentElement.classList.add('theme-tech-dark');
const restoreLogTechShell = () => {
    if (!themeConfig.value.isTechTheme) document.documentElement.classList.remove('theme-tech-dark');
};
const resetMainScroll = async () => {
    await nextTick();
    const scrollContainer = document.querySelector<HTMLElement>('.layout-main-scroll.el-scrollbar__wrap');
    if (scrollContainer) scrollContainer.scrollTop = 0;
};

onMounted(() => {
    mountLogTechShell();
    resetMainScroll();
    loadDetail();
});

onUnmounted(restoreLogTechShell);


</script>
<style lang="scss">
@use './tech-log.scss';
</style>
<template>
    <div class="tech-log log-detail">
        <header class="log-hud">
            <div class="log-identity">
                <span class="log-identity__mark"><el-icon><Document /></el-icon></span>
                <div>
                    <h1 class="log-title">日志详情</h1>
                    <div class="log-kicker">JOURNAL EVENT · MESSAGE / PROCESS / SYSTEM CONTEXT</div>
                </div>
            </div>
            <div class="log-hud__actions">
                <div v-if="!loadError" class="log-status">
                    <span class="log-status__dot"></span>
                    <span>{{ loading ? '解析中' : '上下文完整' }}</span>
                </div>
                <el-button class="log-back" :icon="ArrowLeft" @click="goBack">返回日志列表</el-button>
            </div>
        </header>

        <section class="log-summary" aria-label="日志详情摘要">
            <div
                v-for="item in summaryItems"
                :key="item.label"
                class="log-summary__item"
                :style="{ '--summary-accent': item.color }"
            >
                <span class="log-summary__icon"><el-icon><component :is="item.icon" /></el-icon></span>
                <div>
                    <div class="log-summary__label">{{ item.label }}</div>
                    <div class="log-summary__value" :title="item.value">{{ item.value }}</div>
                </div>
            </div>
        </section>

        <div class="log-detail-loading" v-loading="loading">
            <section v-if="loadError && !loading" class="log-detail-error">
                <el-icon><WarningFilled /></el-icon>
                <p>{{ loadError }}</p>
                <el-button class="log-action" :icon="ArrowLeft" @click="goBack">返回日志列表</el-button>
            </section>

            <template v-else-if="Object.keys(logRecord).length">
                <section class="log-message-panel">
                    <div class="log-panel__head">
                        <div>
                            <h2 class="log-panel__title">日志消息</h2>
                            <div class="log-panel__meta">PRIMARY EVENT MESSAGE</div>
                        </div>
                        <span class="log-results-meta"><span>{{ priorityLabel }}</span></span>
                    </div>
                    <div class="log-message-body"><pre class="log-message-code">{{ logMessage }}</pre></div>
                </section>

                <section class="log-metadata-panel">
                    <div class="log-panel__head">
                        <div>
                            <h2 class="log-panel__title">Journal 元数据</h2>
                            <div class="log-panel__meta">{{ visibleMetadata.length }} FIELDS · COMPLETE EVENT CONTEXT</div>
                        </div>
                    </div>
                    <div class="log-metadata-grid">
                        <div v-for="item in visibleMetadata" :key="item.key" class="log-metadata-item">
                            <div class="log-metadata-label">{{ item.label }}</div>
                            <div class="log-metadata-value">{{ item.value }}</div>
                        </div>
                    </div>
                </section>
            </template>
        </div>
    </div>
</template>