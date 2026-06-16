<template>
    <el-card>
        <template #header>
            <div class="card-header">
                <h3>系统信息</h3>
                <el-tooltip content="详情" placement="bottom" effect="light" :show-arrow="false">
                    <el-icon @click="toHardware">
                        <Promotion />
                    </el-icon>
                </el-tooltip>
            </div>
        </template>
        <div>
            <el-card v-for="item in descriptions" :key="item.key" class="card-box">
                <div class="card-item">
                    <div class="left" :style="{ background: `var(${item.color2})` }">
                        <i class="font32 iconfont" :class="item.icon" :style="{ color: `var(${item.color})` }"></i>
                    </div>
                    <div class="right">
                        <div class="label">{{ item.label }}</div>
                        <div class="content">{{ system[item.key as keyof System] || '' }}</div>
                    </div>
                </div>
            </el-card>
        </div>
    </el-card>
</template>

<script lang="ts" setup name="overviewSystem">
import { onMounted, ref } from 'vue';
import { hardInfo } from '/@/api/run/run';
import { useRouter } from 'vue-router';

const router = useRouter();
const descriptions = [
    { label: '型号', key: 'model_number', icon: 'icon-zhizaoshang1', color: '--el-color-primary', color2: '--next-color-primary-lighter' },
    { label: 'CPU', key: 'cpu_info', icon: 'icon-chanpin', color: '--el-color-success', color2: '--next-color-success-lighter' },
    { label: '序列号', key: 'serial_number', icon: 'icon-zichanbiaoqian', color: '--el-color-danger', color2: '--next-color-danger-lighter' },
    { label: '机器编号', key: 'machine_num', icon: 'icon-bianhao1', color: '--el-color-warning', color2: '--next-color-warning-lighter' },
    { label: '运行时长（自开机以来）', key: 'run_time', icon: 'icon-shichangtongji', color: '--el-color-info', color2: '-el-color-primary-dark-2' },
];
interface System {
    manufacturer: string;
    product_name: string;
    serial_number: string;
    machine_num: string;
    run_time: string;
    model_number: string;
    cpu_info: string;
}
const system = ref<System>({
    manufacturer: '',
    product_name: '',
    serial_number: '',
    machine_num: '',
    run_time: '',
    model_number: '',
    cpu_info: '',
});
const getHardInfo = async () => {
    const [systemRes, cpuRes] = await Promise.all([
        hardInfo('system'),
        hardInfo('cpu')
    ]);
    if (systemRes && cpuRes) {
        system.value = systemRes.system;
        system.value.model_number = systemRes.system.manufacturer + ' ' + systemRes.system.product_name;
        const [prefix, hoursStr] = systemRes.system.run_time.split(' ');
        const hours = parseFloat(hoursStr) || 0;
        let displayTime;
        if (hours >= 24) {
            const days = Math.floor(hours / 24);
            displayTime = `${prefix} ${days} 天`;
        } else {
            displayTime = systemRes.system.run_time;
        }
        system.value.run_time = displayTime;
        system.value.cpu_info = cpuRes.cpu.cores + 'x ' + cpuRes.cpu.model;
    }
};

const toHardware = () => {
    router.push({
        name: 'hardware',
    });
};
onMounted(() => {
    getHardInfo();
});
</script>

<style scoped lang="scss">
.el-card {
    width: 100%;

    &:hover {
        box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.2);
        transition: all ease 0.3s;
    }

    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;

        h3 {
            color: #333333;
        }

        .el-icon {
            font-size: 20px;
            color: var(--el-color-primary);
            cursor: pointer;
        }
    }

    .card-box:not(:last-child) {
        margin-bottom: 15px;
    }

    .card-item {
        display: flex;

        .left {
            display: flex;
            justify-content: center;
            align-items: center;
            width: 50px;
            background-color: #F0F2F5;
            border-radius: 5px;
        }

        .right {
            flex: 1;
            margin-left: 20px;

            .label {
                font-size: 14px;
                font-weight: 500;
                color: #909399;
            }

            .content {
                margin-top: 10px;
                font-size: 16px;
                color: #585858;
            }
        }
    }
}
</style>
