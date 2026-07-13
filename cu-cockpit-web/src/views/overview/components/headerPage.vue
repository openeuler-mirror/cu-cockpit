<template>
    <el-card class="hud-card">
        <div class="box-container">
            <div class="box-item" v-for="item in descriptions" :key="item.key">
                <span class="box-item__icon" :style="{ color: item.color, '--dot': item.color }">
                    <i class="iconfont" :class="item.icon"></i>
                </span>
                <span class="box-item__val">{{ system[item.key as keyof System] || '—' }}</span>
                <el-divider direction="vertical" />
            </div>
            <div class="box-item box-item--status">
                <span class="status-dot"></span>
                <span class="status-text">运行中</span>
            </div>
        </div>
    </el-card>
</template>

<script lang="ts" setup name="overviewHeader">
import { onMounted, ref } from 'vue';
import { hardInfo } from '/@/api/run/run';
import { configGet } from '/@/api/config/config';

const descriptions = [
    { key: 'host_name', icon: 'icon-diannao2', color: '#22d3ee' },
    { key: 'os_name', icon: 'icon-liantong', color: '#a855f7' },
    { key: 'os_version', icon: 'icon-lishibanben', color: '#ffb020' },
];
interface System {
    host_name: string;
    os_name: string;
    os_version: string;
}
const system = ref<System>({
    host_name: '',
    os_name: '',
    os_version: '',
});
const getHardInfo = () => {
    hardInfo('os_system').then((res) => {
        system.value.os_name = res.os_system.os_name;
        system.value.os_version = res.os_system.os_version;
    });
    configGet('gethostname').then((res) => {
        system.value.host_name = res;
    });
};

onMounted(() => {
    getHardInfo();
});
</script>

<style scoped lang="scss">
.hud-card {
    :deep(.el-card__body) {
        padding: 14px 20px;
    }
}

.box-container {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px 0;

    .box-item {
        display: flex;
        align-items: center;
        font-size: 15px;
        color: var(--tech-text, #c7d2e5);

        &__icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 30px;
            height: 30px;
            margin-right: 10px;
            border-radius: 8px;
            background: rgba(90, 165, 255, 0.1);
            box-shadow: 0 0 12px -2px var(--dot);

            .iconfont {
                font-size: 17px;
            }
        }

        &__val {
            font-weight: 500;
            letter-spacing: 0.3px;
            text-shadow: 0 0 10px rgba(90, 165, 255, 0.15);
        }
    }

    .box-item--status {
        margin-left: auto;

        .status-dot {
            width: 9px;
            height: 9px;
            border-radius: 50%;
            margin-right: 8px;
            background: var(--tech-green, #10f5a0);
            box-shadow: 0 0 10px var(--tech-green, #10f5a0);
            animation: hud-pulse 1.6s ease-in-out infinite;
        }

        .status-text {
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 1px;
            color: var(--tech-green, #10f5a0);
        }
    }
}

@keyframes hud-pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.45; transform: scale(0.8); }
}
</style>
