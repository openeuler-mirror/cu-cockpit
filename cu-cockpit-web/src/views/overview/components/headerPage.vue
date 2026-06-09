<template>

    <el-card>
        <div class="box-container">
            <div class="box-item" v-for="item in descriptions" :key="item.key">
                <i class="iconfont" :class="item.icon" :style="{ color: item.color }"></i>
                {{ system[item.key as keyof System] || '' }}
                <el-divider direction="vertical" />
            </div>
            <div class="box-item">
                <el-tag type="success" effect="dark" round>运行中</el-tag>
            </div>
        </div>
    </el-card>
</template>
<script lang="ts" setup name="overviewHeader">

import { onMounted, ref } from 'vue';
import { hardInfo } from '/@/api/run/run';
import { configGet } from '/@/api/config/config';

const descriptions = [
    { key: 'host_name', icon: 'icon-diannao2', color: '#0066FF' },
    { key: 'os_name', icon: 'icon-liantong', color: '#F10033' },
    { key: 'os_version', icon: 'icon-lishibanben', color: '#FF9900' },
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
</style>
