<template>

</template>
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
<style>
</style>