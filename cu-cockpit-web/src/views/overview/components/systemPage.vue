<template>
    <el-card>
        <template #header>
            <div class="card-header">
                <h3><span class="title-bar"></span>系统信息</h3>
                <el-tooltip content="详情" placement="bottom" effect="light" :show-arrow="false">
                    <el-icon @click="toHardware">
                        <Promotion />
                    </el-icon>
                </el-tooltip>
            </div>
        </template>
        <div>
            <div v-for="item in descriptions" :key="item.key" class="card-box">
                <div class="card-item">
                    <div class="left" :style="{ '--accent': item.color }">
                        <i class="font32 iconfont" :class="item.icon"></i>
                    </div>
                    <div class="right">
                        <div class="label">{{ item.label }}</div>
                        <div class="content">{{ system[item.key as keyof System] || '—' }}</div>
                    </div>
                </div>
            </div>
        </div>
    </el-card>
</template>

<script lang="ts" setup name="overviewSystem">
import { onMounted, ref } from 'vue';
import { hardInfo } from '/@/api/run/run';
import { useRouter } from 'vue-router';

const router = useRouter();
const descriptions = [
    { label: '型号', key: 'model_number', icon: 'icon-zhizaoshang1', color: '#22d3ee' },
    { label: 'CPU', key: 'cpu_info', icon: 'icon-chanpin', color: '#10f5a0' },
    { label: '序列号', key: 'serial_number', icon: 'icon-zichanbiaoqian', color: '#ff4d6d' },
    { label: '机器编号', key: 'machine_num', icon: 'icon-bianhao1', color: '#ffb020' },
    { label: '运行时长（自开机以来）', key: 'run_time', icon: 'icon-shichangtongji', color: '#a855f7' },
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

    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;

        h3 {
            display: flex;
            align-items: center;
            margin: 0;
            color: #e8f2ff;
            letter-spacing: 0.5px;

            .title-bar {
                width: 4px;
                height: 15px;
                margin-right: 8px;
                border-radius: 2px;
                background: linear-gradient(180deg, var(--tech-cyan, #22d3ee), var(--tech-purple, #a855f7));
                box-shadow: 0 0 10px rgba(34, 211, 238, 0.5);
            }
        }

        .el-icon {
            font-size: 20px;
            color: var(--tech-cyan, #22d3ee);
            cursor: pointer;
            transition: transform 0.3s ease, filter 0.3s ease;

            &:hover {
                transform: translateX(3px);
                filter: drop-shadow(0 0 6px var(--tech-cyan, #22d3ee));
            }
        }
    }

    .card-box {
        padding: 12px 14px;
        border-radius: 12px;
        background: rgba(10, 18, 34, 0.5);
        border: 1px solid var(--tech-border, rgba(90, 165, 255, 0.16));
        transition: border-color 0.3s ease, background 0.3s ease, transform 0.3s ease;

        &:not(:last-child) {
            margin-bottom: 14px;
        }

        &:hover {
            transform: translateX(4px);
            border-color: rgba(34, 211, 238, 0.4);
            background: rgba(16, 26, 45, 0.7);
        }
    }

    .card-item {
        display: flex;
        align-items: center;

        .left {
            --accent: #22d3ee;
            display: flex;
            justify-content: center;
            align-items: center;
            width: 48px;
            height: 48px;
            flex: none;
            border-radius: 11px;
            background: rgba(90, 165, 255, 0.08);
            box-shadow: inset 0 0 0 1px rgba(90, 165, 255, 0.12), 0 0 16px -6px var(--accent);

            .iconfont {
                color: var(--accent);
                filter: drop-shadow(0 0 6px var(--accent));
            }
        }

        .right {
            flex: 1;
            margin-left: 18px;
            min-width: 0;

            .label {
                position: relative;
                display: inline-flex;
                align-items: center;
                width: fit-content;
                min-height: 24px;
                padding: 3px 10px 3px 22px;
                border: 1px solid rgba(34, 211, 238, 0.26);
                border-radius: 999px;
                background: linear-gradient(90deg, rgba(34, 211, 238, 0.12), rgba(168, 85, 247, 0.06));
                color: #aeefff;
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 1.5px;
                line-height: 1;
                text-shadow: 0 0 10px rgba(34, 211, 238, 0.55);

                &::before {
                    content: '';
                    position: absolute;
                    left: 9px;
                    width: 6px;
                    height: 6px;
                    border-radius: 50%;
                    background: var(--tech-cyan, #22d3ee);
                    box-shadow: 0 0 10px var(--tech-cyan, #22d3ee);
                }
            }

            .content {
                margin-top: 10px;
                padding-left: 2px;
                color: #edf7ff;
                font-size: 16px;
                font-weight: 600;
                letter-spacing: 0.2px;
                line-height: 1.45;
                text-shadow: 0 0 14px rgba(90, 165, 255, 0.18);
                word-break: break-all;
            }
        }
    }
}
</style>
