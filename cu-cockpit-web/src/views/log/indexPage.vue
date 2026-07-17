<script lang="ts" setup name="logs">
import { reactive, ref, computed, onMounted, h, onActivated, onUnmounted, nextTick } from 'vue';
import { ArrowDown, ArrowUp, Connection, Document, Filter, Monitor, Refresh, Search, WarningFilled } from '@element-plus/icons-vue';
import { logs, getBoot } from '/@/api/log';
import { useRouter } from 'vue-router';
import { Local } from '/@/utils/storage';
import { ElPopover, RowEventHandlerParams } from 'element-plus';
import { storeToRefs } from 'pinia';
import { useThemeConfig } from '/@/stores/themeConfig';

const router = useRouter();
const themeStore = useThemeConfig();
const { themeConfig } = storeToRefs(themeStore);

//日志每行的key
interface LogItem {
    date: string;
    time: string;
    hostname: string;
    message: string;
    service: string;
    [key: string]: string| number; // 其他可能的字段
}
//定义 boot
interface BootItem {
    value: string;
    label: string;
}

// 
const priorityOps = [
    { value: 'err', label: 'err 及更高级别' },
    { value: 'info', label: 'info 及更高级别' },
    { value: 'warning', label: 'warning 及更高级别' },
    { value: 'debug', label: 'debug 及更高级别' },
    { value: 'emerg', label: 'emerg 及更高级别' },
    { value: 'crit', label: 'crit 及更高级别' },
    { value: 'notice', label: 'notice 及更高级别' },
    { value: 'alert', label: 'alert 及更高级别' },
];
//行数静态数据
const limits = [
    { label: '10', value: 10 },
    { label: '15', value: 15 },
    { label: '20', value: 20 },
    { label: '25', value: 25 },
    { label: '50', value: 50 },
    { label: '100', value: 100 },
];
//搜索默认数据
const state = reactive({
    ruleForm: {
        since: '',
        until: '',
        priority: 'err',
        service: '',
        identifier: '',
        keyword: '',
        limit: '',
        boot: '',
        output_format: 'summary'
    },
    loading: false
});
const { ruleForm } = state;
//日志数据
const logData = ref<LogItem[]>([]);
//boot
const bootOps = ref<BootItem[]>([]);
const loadError = ref('');
const bootError = ref('');
const lastUpdated = ref('');
let activationCount = 0;
//获取DOM
const logsMiddleRef = ref();
// 添加响应式宽度变量
const containerWidth = ref(window.innerWidth);
const containeHeight = ref(window.innerHeight);
//控制展示隐藏
const showAdvancedSearch = ref(false);

const activeFilterCount = computed(() =>
    Object.entries(ruleForm).filter(([key, value]) => key !== 'output_format' && value !== '').length
);
const serviceCount = computed(() => new Set(logData.value.map((item) => item.service).filter(Boolean)).size);
const hostCount = computed(() => new Set(logData.value.map((item) => item.hostname).filter(Boolean)).size);
const summaryItems = computed(() => [
    { label: '当前结果', value: `${logData.value.length} 条`, icon: Document, color: '#22d3ee' },
    { label: '涉及服务', value: `${serviceCount.value} 项`, icon: Connection, color: '#a855f7' },
    { label: '涉及主机', value: `${hostCount.value} 台`, icon: Monitor, color: '#10f5a0' },
    { label: '启用筛选', value: `${activeFilterCount.value} 项`, icon: Filter, color: '#ffb020' },
]);
const currentPriorityLabel = computed(
    () => priorityOps.find((item) => item.value === ruleForm.priority)?.label || '全部优先级'
);
// 重置表单
const resetForm = () => {
    Object.assign(state.ruleForm, {
        since: '',
        until: '',
        priority: 'err',
        service: '',
        identifier: '',
        keyword: '',
        limit: '',
        boot: '',
        output_format: 'summary'
    });
    searchLogs();
};

// 窗口大小变化处理函数
const handleResize = () => {
    // 更新 containerWidth 值以触发响应式更新
    containerWidth.value = window.innerWidth;
    containeHeight.value = window.innerHeight;
};

//获取 日志列表
const searchLogs = async () => {
    state.loading = true;
    loadError.value = '';
    try {
        const res = await logs({
            ...state.ruleForm,
        });
        logData.value = res?.logs || [];
        lastUpdated.value = new Date().toLocaleTimeString('zh-CN', { hour12: false });
    } catch (error) {
        logData.value = [];
        loadError.value = '系统日志查询失败，请检查日志服务或调整条件后重试。';
        console.error('查询系统日志失败:', error);
    } finally {
        state.loading = false;
    }
}

// 16位时间戳转换逻辑
const formatTimestamp = (timestamp: string): string => {
    if (!timestamp) return '';
    const num = parseInt(timestamp, 10);
    if (isNaN(num)) return timestamp;

    let milliseconds: number;
    if (timestamp.length === 16) {
        milliseconds = Math.floor(num / 1000);
    } else if (timestamp.length === 17) {
        milliseconds = Math.floor(num / 1000000);
    } else {
        return timestamp;
    }
    const date = new Date(milliseconds);
    if (isNaN(date.getTime())) return timestamp;

    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    const seconds = date.getSeconds().toString().padStart(2, '0');

    return `${month}月${day}日${hours}:${minutes}:${seconds}`;
};

const sinceDisabledDate = (time: Date) => {
    const now = new Date().getTime();
    if (!state.ruleForm.until) {
        return time.getTime() > now;
    }
    const untilTime = new Date(state.ruleForm.until).getTime();
    return time.getTime() > untilTime || time.getTime() > now;
};
const untilDisabledDate = (time: Date) => {
    const now = new Date().getTime();
    if (!state.ruleForm.since) {
        return time.getTime() > now;
    }
    const sinceTime = new Date(state.ruleForm.since).getTime();
    return time.getTime() < sinceTime || time.getTime() > now;
};


const toggleAdvancedSearch = () => {
    showAdvancedSearch.value = !showAdvancedSearch.value;
    nextTick(() => {
        handleResize();
    });
};
const toDetail = (row: {[key:string]:string}) => {
    Local.set('logsDetail', JSON.parse(JSON.stringify({
        "cursor": row.cursor,  //元数据
        "servicename": row.service, //服务名
        "priority": state.ruleForm.priority // 状态
    })));
    router.push({ name: 'logsDetail' });
};

// 计算表格宽度 - 依赖 containerWidth 确保响应式更新
const tableWidth = computed(() => {
    const widthRef = containerWidth.value;
    return Math.max(logsMiddleRef.value?.clientWidth || widthRef - 72, 280);
});
const tableHeightValue = computed(() => {
    const reservedHeight = showAdvancedSearch.value ? 520 : 430;
    return Math.max(440, Math.min(620, containeHeight.value - reservedHeight));
});
// 定义 el-table-v2 列配置 - 依赖 containerWidth 确保响应式更新
const tableColumns = computed(() => {
    const contentWidth = Math.max(tableWidth.value, 1040);
    return [
        {
            key: 'timestamp',
            title: '时间',
            dataKey: 'timestamp',
            width: 170,
            align: 'center',
            cellRenderer: ({ rowData }) => formatTimestamp(rowData.timestamp)
        },
        {
            key: 'service',
            title: '服务名称',
            dataKey: 'service',
            width: 230,
            class: 'overflow-ellipsis-column',
            cellRenderer: ({ rowData }) => {
                if (!rowData.service) {
                    return h('span', '');
                }
                return h(
                    ElPopover,
                    {
                        placement: 'top',
                        width: 240,
                        trigger: 'hover',
                        content: rowData.service,
                        popperClass: 'log-tech-popover',
                    },
                    {
                        reference: () => h(
                            'div',
                            {
                                class: 'overflow-ellipsis',
                            },
                            rowData.service
                        )
                    }
                );
            },
        },
        {
            key: 'hostname',
            title: '主机名称',
            dataKey: 'hostname',
            width: 160,
            align: 'center'
        },
        {
            key: 'message',
            title: '日志信息',
            dataKey: 'message',
            class: 'overflow-ellipsis-column',
            width: Math.max(340, contentWidth - 710),
            cellRenderer: ({ rowData }) => {
                // 处理空值情况
                if (!rowData.message) {
                    return h('span', '');
                }
                return h(
                    ElPopover,
                    {
                        placement: 'top',
                        width: 400,
                        trigger: 'hover',
                        content: rowData.message,
                        popperClass: 'log-tech-popover',
                    },
                    {
                        reference: () => h(
                            'div',
                            {
                                class: 'overflow-ellipsis',
                            },
                            rowData.message
                        )
                    }
                );
            },
        },
        {
            key: 'identifier',
            title: '日志标识',
            dataKey: 'identifier',
            width: 150,
            align: 'center'
        }
    ];
});
// 为 el-table-v2 创建事件处理配置
const rowEventHandlers = {
    onClick: (params: RowEventHandlerParams) => {
        toDetail(params.rowData);
    }
};

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
    bootError.value = '';
    getBoot().then(res => {
        if (!res || !Array.isArray(res.boots)) {
            bootOps.value = [];
            return;
        }
        const tmp = res.boots.map(item => ({
            value: String(item),
            label: String(item)
        }));
        bootOps.value = tmp;
    }).catch(() => {
        bootOps.value = [];
        bootError.value = 'boot 数据不可用';
    });

    // 添加窗口大小变化监听器
    window.addEventListener('resize', handleResize);
    searchLogs();
});
//组件缓存的生命周期
onActivated(() => {
    if (activationCount > 0) searchLogs();
    activationCount += 1;
});

// 移除窗口大小监听器
onUnmounted(() => {
    window.removeEventListener('resize', handleResize);
    restoreLogTechShell();
});

</script>

<style lang="scss">
@use './tech-log.scss';
</style>
<template>
    <div class="tech-log log-overview">
        <header class="log-hud">
            <div class="log-identity">
                <span class="log-identity__mark"><el-icon><Document /></el-icon></span>
                <div>
                    <h1 class="log-title">系统日志</h1>
                    <div class="log-kicker">SYSTEM JOURNAL · QUERY / TRACE / INSPECT</div>
                </div>
            </div>
            <div class="log-hud__actions">
                <div v-if="!loadError" class="log-status">
                    <span class="log-status__dot"></span>
                    <span>{{ state.loading ? '查询中' : '日志在线' }}</span>
                </div>
                <el-button class="log-action" :icon="Refresh" :loading="state.loading" @click="searchLogs">刷新</el-button>
            </div>
        </header>

        <section class="log-summary" aria-label="日志查询摘要">
            <div
                v-for="item in summaryItems"
                :key="item.label"
                class="log-summary__item"
                :style="{ '--summary-accent': item.color }"
            >
                <span class="log-summary__icon"><el-icon><component :is="item.icon" /></el-icon></span>
                <div>
                    <div class="log-summary__label">{{ item.label }}</div>
                    <div class="log-summary__value">{{ item.value }}</div>
                </div>
            </div>
        </section>

        <section class="log-filter-panel">
            <div class="log-panel__head">
                <div>
                    <h2 class="log-panel__title">日志检索</h2>
                    <div class="log-panel__meta">PRIORITY THRESHOLD · FIELD MATCH · TIME WINDOW</div>
                </div>
                <div class="log-filter-state">
                    <span>{{ currentPriorityLabel }}</span>
                    <span v-if="bootError" class="is-warning">boot 数据不可用</span>
                </div>
            </div>

            <el-form :model="state.ruleForm" class="log-filter-form" label-position="top" @submit.prevent="searchLogs">
                <div class="log-filter-grid log-filter-grid--primary">
                    <el-form-item label="日志优先级">
                        <el-select
                            v-model="ruleForm.priority"
                            class="log-control log-control--select log-control--priority"
                            placeholder="日志优先级"
                            :teleported="true"
                            popper-class="log-filter-popper log-filter-popper--priority"
                        >
                            <el-option v-for="item in priorityOps" :key="item.value" :label="item.label" :value="item.value" />
                        </el-select>
                    </el-form-item>
                    <el-form-item label="服务名称">
                        <el-input
                            v-model="ruleForm.service"
                            class="log-control log-control--search log-control--service"
                            :prefix-icon="Search"
                            placeholder="输入 systemd 服务名称"
                            clearable
                        />
                    </el-form-item>
                    <el-form-item label="关键字 / 正则">
                        <el-input
                            v-model="ruleForm.keyword"
                            class="log-control log-control--search log-control--keyword"
                            :prefix-icon="Search"
                            placeholder="匹配日志消息"
                            clearable
                        />
                    </el-form-item>
                    <el-form-item label="显示行数">
                        <el-select
                            v-model="ruleForm.limit"
                            class="log-control log-control--select log-control--limit"
                            filterable
                            allow-create
                            default-first-option
                            placeholder="默认行数"
                            popper-class="log-filter-popper log-filter-popper--limit"
                        >
                            <el-option v-for="item in limits" :key="item.value" :label="item.label" :value="item.value" />
                        </el-select>
                    </el-form-item>
                </div>

                <div v-show="showAdvancedSearch" class="log-filter-grid log-filter-grid--advanced">
                    <el-form-item label="开始时间">
                        <el-date-picker
                            v-model="ruleForm.since"
                            type="datetime"
                            placeholder="开始时间"
                            :disabled-date="sinceDisabledDate"
                            class="log-control log-control--date"
                            format="YYYY-MM-DD HH:mm:ss"
                            value-format="YYYY-MM-DD HH:mm:ss"
                        />
                    </el-form-item>
                    <el-form-item label="结束时间">
                        <el-date-picker
                            v-model="ruleForm.until"
                            type="datetime"
                            placeholder="结束时间"
                            :disabled-date="untilDisabledDate"
                            class="log-control log-control--date"
                            format="YYYY-MM-DD HH:mm:ss"
                            value-format="YYYY-MM-DD HH:mm:ss"
                        />
                    </el-form-item>
                    <el-form-item label="日志标识符">
                        <el-input
                            v-model="ruleForm.identifier"
                            class="log-control log-control--search log-control--identifier"
                            :prefix-icon="Search"
                            placeholder="例如 sshd / kernel"
                            clearable
                        />
                    </el-form-item>
                    <el-form-item label="启动批次">
                        <el-select
                            v-model="ruleForm.boot"
                            class="log-control log-control--select log-control--boot"
                            placeholder="选择 boot"
                            :teleported="true"
                            popper-class="log-filter-popper log-filter-popper--boot"
                        >
                            <el-option v-for="item in bootOps" :key="item.value" :label="item.label" :value="item.value" />
                        </el-select>
                    </el-form-item>
                </div>

                <div class="log-filter-actions">
                    <el-button class="log-action log-action--ghost" :icon="showAdvancedSearch ? ArrowUp : ArrowDown" @click="toggleAdvancedSearch">
                        {{ showAdvancedSearch ? '收起高级筛选' : '展开高级筛选' }}
                    </el-button>
                    <span class="log-filter-actions__spacer"></span>
                    <el-button class="log-action" @click="resetForm">重置条件</el-button>
                    <el-button class="log-action log-action--primary" :icon="Search" :loading="state.loading" native-type="submit">
                        查询日志
                    </el-button>
                </div>
            </el-form>
        </section>

        <section v-if="loadError && !state.loading" class="log-error">
            <el-icon><WarningFilled /></el-icon>
            <p>{{ loadError }}</p>
            <el-button class="log-action" :icon="Refresh" @click="searchLogs">重新查询</el-button>
        </section>

        <section class="log-results-panel">
            <div class="log-panel__head">
                <div>
                    <h2 class="log-panel__title">日志事件流</h2>
                    <div class="log-panel__meta">VIRTUALIZED JOURNAL VIEW · CLICK ROW FOR FULL CONTEXT</div>
                </div>
                <div class="log-results-meta">
                    <span><strong>{{ logData.length }}</strong> 条当前结果</span>
                    <span v-if="lastUpdated">更新于 {{ lastUpdated }}</span>
                </div>
            </div>

            <div ref="logsMiddleRef" class="log-table-viewport">
                <el-table-v2
                    :columns="tableColumns"
                    :data="logData"
                    :width="tableWidth"
                    :height="tableHeightValue"
                    :row-event-handlers="rowEventHandlers"
                    :estimated-row-height="68"
                    :row-height="68"
                    fixed
                    scrollbar-always-on
                    v-loading="state.loading"
                    row-class="log-table-row"
                >
                    <template #header="{ columns }">
                        <div class="log-table-header">
                            <div
                                v-for="column in columns"
                                :key="column.key"
                                class="log-table-header__cell"
                                :style="{ width: `${column.width}px` }"
                            >
                                {{ column.title }}
                            </div>
                        </div>
                    </template>
                    <template #empty>
                        <div class="log-empty">
                            <el-icon><Document /></el-icon>
                            <strong>当前条件下无匹配日志</strong>
                            <span>调整优先级、时间范围或关键字后重新查询</span>
                        </div>
                    </template>
                </el-table-v2>
            </div>
        </section>
    </div>
</template>