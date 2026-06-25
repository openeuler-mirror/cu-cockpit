<script lang="ts" setup name="logs">
import { reactive, ref, computed, onMounted, h, onActivated, onUnmounted, nextTick, watch } from 'vue';
import inputSelect from '/@/components/inputSelect/index.vue';
import { logs, getBoot } from '/@/api/log';
import { useRouter } from 'vue-router';
import { Local } from '/@/utils/storage';
import { ElPopover, RowEventHandlerParams } from 'element-plus';

const router = useRouter();

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
    [key: string]: string| number;
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
//获取DOM
const logsMiddleRef = ref();
const logsHeadRef = ref();
const logsContentRef = ref();
// 添加响应式宽度变量
const containerWidth = ref(window.innerWidth);
const containeHeight = ref(window.innerHeight);
// 添加头部高度响应式变量
const headHeight = ref(60);
//控制展示隐藏
const showAdvancedSearch = ref(false);
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
    try {
        const res = await logs({
            ...state.ruleForm,
        });
        logData.value = res?.logs || [];
    } catch (error) {
        logData.value = [];
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
        updateHeadHeight();
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

// 更新头部高度的函数
const updateHeadHeight = () => {
    if (logsHeadRef.value) {
        headHeight.value = logsHeadRef.value.clientHeight;
    }
};
// 计算表格宽度 - 依赖 containerWidth 确保响应式更新
const tableWidth = computed(() => {
    const widthRef = containerWidth.value;
    return (logsMiddleRef.value?.clientWidth || 1200 )+ (widthRef*0);
});
const tableHeightValue = computed(() => {
    if (!logsContentRef.value) return 600;
    const Tableheight= containeHeight.value
    const contentHeight = logsContentRef.value.clientHeight;
    return contentHeight - headHeight.value - 4 + (Tableheight * 0);
});
// 定义 el-table-v2 列配置 - 依赖 containerWidth 确保响应式更新
const tableColumns = computed(() => {
    const widthRef = containerWidth.value;
    return [
        {
            key: 'timestamp',
            title: '时间',
            dataKey: 'timestamp',
            width: 160,
            align: 'center',
            cellRenderer: ({ rowData }) => formatTimestamp(rowData.timestamp)
        },
        {
            key: 'service',
            title: '服务名称',
            dataKey: 'service',
            width: 240,
            align: 'center',
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
                        popperClass: 'text-center-popover',
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
            width: 120,
            align: 'center'
        },
        {
            key: 'message',
            title: '日志信息',
            dataKey: 'message',
            class: 'overflow-ellipsis-column',
            width: (logsMiddleRef.value?.clientWidth || 1200) - 670 + (widthRef*0),
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
                        popperClass: 'text-center-popover',
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

onMounted(() => {
    getBoot().then(res => {
        if (!res || !Array.isArray(res.boots)) {
            bootOps.value = [];
            return;
        }
        const tmp = res.boots.map(item => ({
            value: item,
            label: item
        }));
        bootOps.value = tmp;
    }).catch(() => {
        bootOps.value = [];
    });

    // 添加窗口大小变化监听器
    window.addEventListener('resize', handleResize);
    searchLogs();
});
//组件缓存的生命周期
onActivated(() => {
    searchLogs();
});

// 移除窗口大小监听器
onUnmounted(() => {
    window.removeEventListener('resize', handleResize);
});

// 监听 showAdvancedSearch 变化，更新头部高度
watch(showAdvancedSearch, () => {
    nextTick(() => {
        updateHeadHeight();
    });
});

// 监听窗口大小变化，更新头部高度
watch(containerWidth, () => {
    nextTick(() => {
        updateHeadHeight();
    });
});
</script>

<style scoped lang="scss">
.logs-box {
    padding: 15px 20px;

    .logs-content {
        height: calc(100vh - 115px);
        overflow: auto;
        background-color: #fff;
        border-radius: 8px;
        box-shadow: var(--el-box-shadow-light);

        .logs-head {
            background-color: #fff;
            display: flex;
            align-items: flex-start;
        }
    }
}

.logs-head-l {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    width: calc(100% - 240px);
    background-color: #fff;
    height: 60px;
    font-size: 16px;
    padding-top: 15px;
    transition: height 0.3s ease;

    .time {
        :deep(.el-input__prefix) {
            display: none;
        }
    }

    :deep(.el-form-item__label) {
        font-weight: 700;
    }

    .logs-head-l-item {
        width: 264px;
    }
}

.logs-head-show {
    height: auto;
}

.logs-head-r {
    display: flex;
    align-items: center;
    min-width: 220px;
}

.logs-middle {
    :deep(.table_row .cell) {
        padding-left: 0 !important;
        padding-right: 0 !important;
    }

    :deep(.el-table--fit .el-table__inner-wrapper:before) {
        width: 0%;
    }

    // 添加 el-table-v2 表头样式
    :deep(.table-v2-header) {
        display: flex;
        background-color: #f5f7fa;

        .table-v2-header-cell {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 12px 0;
            font-weight: bold;
            color: #606266;
            box-sizing: border-box;
        }
    }

    // 优化 description 样式
    :deep(.description) {
        word-wrap: break-word;
        white-space: pre-wrap;
    }

    :deep(.table_row_class .cell) {
        cursor: default;
    }

    :deep(.overflow-ellipsis-column) {
        height: 48px;
        line-height: 48px;
        word-break: break-all;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 1;
        -webkit-box-orient: vertical;
    }

    :deep(.table_v_row_class) {
        padding: 12px 0;
    }
}

.form_content {
    display: flex;
    align-items: center;
    width: 100%
}

@media (max-width: 1820px) {
    .logs-head-l {
        .logs-head-l-item {
            width: 258px;
        }
    }
}

@media (max-width: 1798px) {
    .logs-head-l {
        .logs-head-l-item {
            width: 240px;
        }
    }
}

@media (max-width: 1710px) {
    .logs-head-l {
        .logs-head-l-item {
            width: 280px;
        }
    }
}

@media (max-width: 1630px) {
    .logs-head-l {
        .logs-head-l-item {
            width: 250px;
        }
    }
}

@media (max-width: 1508px) {
    .logs-head-l {
        .logs-head-l-item {
            width: 250px;
        }
    }
}

.overflow-ellipsis {
    height: 48px;
    line-height: 48px;
    word-break: break-all;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
}
</style>
<style>
.text-center-popover {
    text-align: center;
}
</style>
<template>
    <div class="logs-box">
        <div class="logs-content" ref="logsContentRef">
            <div class="logs-head" ref="logsHeadRef">
                <el-form :model="state.ruleForm" label-width="auto" class="form_content">
                    <div class="logs-head-l" :class="{ 'logs-head-show': showAdvancedSearch }">
                        <el-form-item label="开始时间" class="logs-head-l-item time">
                            <el-date-picker v-model="ruleForm.since" type="datetime" placeholder="开始时间"
                                :disabled-date="sinceDisabledDate" class="logs-comm-item" format="YYYY-MM-DD HH:mm:ss"
                                value-format="YYYY-MM-DD HH:mm:ss">
                            </el-date-picker>
                        </el-form-item>
                        <el-form-item label="结束时间" class="logs-head-l-item time">
                            <el-date-picker v-model="ruleForm.until" type="datetime" placeholder="结束时间"
                                :disabled-date="untilDisabledDate" class="logs-comm-item" format="YYYY-MM-DD HH:mm:ss"
                                value-format="YYYY-MM-DD HH:mm:ss">
                            </el-date-picker>
                        </el-form-item>
                        <el-form-item label="&nbsp;&nbsp;&nbsp;日志优先级" class="logs-head-l-item logs-h-priority">
                            <el-select v-model="ruleForm.priority" placeholder="日志优先级" clearable class="logs-comm-item">
                                <el-option v-for="item in priorityOps" :key="item.value" :label="item.label"
                                    :value="item.value" />
                            </el-select>
                        </el-form-item>
                        <el-form-item label="服务名称" class="logs-head-l-item">
                            <el-input v-model="ruleForm.service" placeholder="服务名称" clearable class="logs-comm-item" />
                        </el-form-item>
                        <el-form-item label="标识符 " class="logs-head-l-item logs-head-">
                            <el-input v-model="ruleForm.identifier" placeholder="标识符" clearable
                                class="logs-comm-item" />
                        </el-form-item>
                        <el-form-item label="关键字 " class="logs-head-l-item">
                            <el-input v-model="ruleForm.keyword" placeholder="关键字或正则表达式" clearable
                                class="logs-comm-item" />
                        </el-form-item>
                        <el-form-item label="显示行数" class="logs-head-l-item">
                            <inputSelect v-model:value="ruleForm.limit" :options="limits" filterable
                                placeholder="显示的行数"></inputSelect>
                        </el-form-item>
                        <el-form-item label="boot" class="logs-head-l-item">
                            <el-select v-model="ruleForm.boot" placeholder="boot" clearable class="logs-comm-item">
                                <el-option v-for="item in bootOps" :key="item.value" :label="item.label"
                                    :value="item.value" />
                            </el-select>
                        </el-form-item>
                    </div>
                    <div class="logs-head-r">
                        <el-button type="primary" @click="searchLogs" class="btn btn_one">搜索</el-button>
                        <el-button @click="resetForm" class="btn">重置</el-button>
                        <el-button class="btn" @click="toggleAdvancedSearch">
                            {{ showAdvancedSearch ? '收起' : '更多' }}
                        </el-button>
                    </div>
                </el-form>
            </div>
            <div class="logs-middle" ref="logsMiddleRef">
                <el-table-v2 :columns="tableColumns" :data="logData" :width="tableWidth" :height="tableHeightValue"
                    fixed :row-event-handlers="rowEventHandlers" :estimated-row-height="73" :row-height="73"
                    scrollbar-always-on v-loading="state.loading" row-class="table_v_row_class">
                    <template #header="{ columns }">
                        <div class="table-v2-header">
                            <div v-for="column in columns" :key="column.key" class="table-v2-header-cell"
                                :style="{ width: column.width + 'px' }">
                                {{ column.title }}
                            </div>
                        </div>
                    </template>
                </el-table-v2>
            </div>
        </div>
    </div>
</template>