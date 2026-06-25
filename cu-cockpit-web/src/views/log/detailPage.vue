<script lang="ts" setup>
import { onMounted, ref } from 'vue';
import { Local } from '/@/utils/storage';
import { logs } from '/@/api/log';
// 定义日志配置项类型
interface LogConfigItem {
    key: string;
    span?: number | string;
    label?: number | string;
}


// 保存日志详情数据
const logsDetail = ref(Local.get("logsDetail") || {}); 
// 显示配置
const logsConfig = ref<LogConfigItem[]>([

    {
        label: '服务名称',
        key: 'logService',
        span: 2,
    },
    {
        key: 'MESSAGE',
        span: 2,
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
]);
onMounted(() => {
     logs({
        cursor: logsDetail.value.cursor,
        priority: logsDetail.value.priority,
        service:'cu-cockpit',
        output_format:'all_json'
    }).then(res => {
        let tmp = res.logs[0];
        tmp.logService = logsDetail.value.servicename;
        logsDetail.value = tmp;
    })
});


</script>
<style scoped lang="scss">
.box-container {
    padding: 15px 20px;

    ::v-deep .el-descriptions__label {
        width: 15%;
        font-weight: 500;
    }

    // 添加描述项内容换行样式
    :deep(.el-descriptions__content) {
        width: 35%;
        word-wrap: break-word;
        word-break: break-all;
        white-space: pre-wrap;
    }
}
.log-header .log-url{
    :deep(.el-breadcrumb__inner.is-link){
        color: #06c;
    }
}
</style>
<template>
    <div class="box-container">
        <el-card class="box-card">
            <template #header>
                <div class="card-header log-header">
                    <el-breadcrumb separator="/">
                        <el-breadcrumb-item :to="{ path: '/log' }" class="log-url">日志</el-breadcrumb-item>
                        <el-breadcrumb-item >日志详情</el-breadcrumb-item>
                    </el-breadcrumb>
                </div>
            </template>
            <el-descriptions size="large" border :column="2">
                <template v-for="item in logsConfig" :key="item.key">
                    <el-descriptions-item v-if="logsDetail[item.key]"
                        :label="item.label || item.key" :span="item.span ?? 1">
                        {{ logsDetail[item.key] }}
                    </el-descriptions-item>

                </template>


            </el-descriptions>
        </el-card>
    </div>
</template>