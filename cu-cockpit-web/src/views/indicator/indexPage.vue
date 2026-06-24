<template #reference>

                                    <div class="indicator-card-disk">
                                        <div class="title">
                                            <div class="title-text"> /boot </div>
                                            <div class="capacity">/boot剩余{{ diskInfo.boot.free }}可用</div>
                                        </div>
                                        <div class="disk-echarts">
                                            <div ref='disk2' style="height: 100%;">

                                            </div>
                                        </div>
                                    </div>
                                
</template>
<script lang="ts" setup>

import { ref, reactive, onMounted, onUnmounted } from 'vue';
import * as echarts from 'echarts';
import { monitorStatus, hardInfo } from '/@/api/run/run';
import { debounce } from 'lodash';
interface DiskData {
    free: string;
    used: string;
    total: string;
}

interface DiskInfo {
    total: DiskData;
    boot: DiskData;
}

const diskInfo = ref<DiskInfo>({
    total: {
        free: '',
        used: '',
        total: ''
    },
    boot: {
        free: '',
        used: '',
        total: ''
    }
});
// DOM引用
const cpuRef = ref<HTMLDivElement>();
const memoryRef = ref<HTMLDivElement>();
const swapRef = ref<HTMLDivElement>();
const disk1 = ref<HTMLDivElement>();
const disk2 = ref<HTMLDivElement>();
const diskIoRef = ref<HTMLDivElement>();
const diskIoRefs = ref<HTMLDivElement>();

// 数据响应式变量
const loadArray: Array<string> = reactive([]);
const cpuCores = ref();
const availableGB = ref();
const swapFreeGB = ref();
const serviceTableData = reactive([]);
const networkXAxis: Array<string> = reactive([]);
const networkXAxis2: Array<string> = reactive([]);
const loading = ref(false);
const options = reactive<Array<{ value: string; label: string }>>([]);
const optVal = ref();
const optVal2 = ref();

// ECharts实例
let cpuDom:echarts.ECharts | null;
let memoryDom: echarts.ECharts | null;
let swapDom: echarts.ECharts | null;
let disk1Dom: echarts.ECharts | null;
let disk2Dom: echarts.ECharts | null;
let diskIoDom: echarts.ECharts | null;
let diskIoDom2: echarts.ECharts | null;

// 数据存储
const diskData = new Map();
 

// 定时器
const lineTimer = ref<number | null>(null);

// 生命周期钩子
onMounted(() => {
    loading.value = true;
    hardInfo('cpu').then(res => {
        cpuCores.value = res.cpu.cores;
    });
    getAllData();
    handleTimer();
    window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
    if (lineTimer.value) clearInterval(lineTimer.value);
    window.removeEventListener('resize', handleResize);
});

// 主要数据获取函数
const getAllData = () => {
    monitorStatus('all').then(res => {
        processCpuData(res[0]);
        processMemoryData(res[1]);
        processServiceMemoryData(res[2]);
        processDiskData(res[3]);
        processNetworkData(res[4]);
        loading.value = false;
    });
};

// CPU数据处理
const processCpuData = (cpuData:{cpu:{[key:string]:string}}) => {
    if (!cpuData) return;

    const cpu = cpuData.cpu;
    const cpuTitleText = parsePercentTitle(cpu.total_utilization_percent);
    const cpuPercent = parseFloat((cpu.total_utilization_percent.split("%"))[0]);
    const seriesColor = setSeriesColor(cpuPercent);

    // 负载数据处理
    const cpuTmpArray = cpu.load_average.split(" ");
    const cpuTmp: string[] = [];
    for (let index = 0; index < cpuTmpArray.length; index += 2) {
        cpuTmp.push(`最近 ${(cpuTmpArray[index].split(':'))[0]}负载:${cpuTmpArray[index + 1]}`);
    }
    Object.assign(loadArray, cpuTmp);

    if (!cpuDom) {
        cpuDom = echarts.init(cpuRef.value);
        barPolarEchart(cpuDom, 'CPU使用率', cpuPercent, cpuTitleText, seriesColor);
    } else {
        cpuDom.setOption({
            title: [{
                text: `{a|${cpuTitleText[0]}.}{b|${cpuTitleText[1] ? cpuTitleText[1] : '0%'}}`,
            }],
            series: [{
                color: seriesColor,
                data: [cpuPercent],
            }]
        });
    }
};

// 内存数据处理
const processMemoryData = (memoryDataRes:{memory: { [key: string]: number }}) => {
    if (!memoryDataRes) return;

    const memoryData = memoryDataRes.memory;

    // 内存使用率计算
    const memoryPercent = Math.round(memoryData.used_mb / memoryData.total_mb * 10000) / 100;
    const titleText = (memoryPercent + '%').split('.');
    const memorySeriesColor = setSeriesColor(memoryPercent);
    availableGB.value = Math.round(memoryData.available_mb / 1024 * 100) / 100;

    // Swap使用率计算
    const swapPercent = Math.round(memoryData.swap_used_mb / memoryData.swap_total_mb * 10000) / 100;
    const swapTitleText = (swapPercent == 0 ? "0.00%" : swapPercent + '%').split('.');
    const swapSeriesColor = setSeriesColor(swapPercent);
    swapFreeGB.value = Math.round(memoryData.swap_free_mb / 1024 * 100) / 100;

    if (!memoryDom && !swapDom) {
        memoryDom = echarts.init(memoryRef.value);
        barPolarEchart(memoryDom, 'RAM', memoryPercent, titleText, memorySeriesColor);

        swapDom = echarts.init(swapRef.value);
        barPolarEchart(swapDom, '交换空间', swapPercent, swapTitleText, swapSeriesColor);
    } else {
        memoryDom?.setOption({
            title: [{
                text: `{a|${titleText[0]}.}{b|${titleText[1] ? titleText[1] : '0%'}}`,
            }],
            series: [{
                color: memorySeriesColor,
                data: [memoryPercent],
            }]
        });

        swapDom?.setOption({
            title: [{
                text: `{a|${swapTitleText[0]}.}{b|${swapTitleText[1] ? swapTitleText[1] : '0%'}}`,
            }],
            series: [{
                color: swapSeriesColor,
                data: [swapPercent],
            }]
        });
    }
};

// 服务内存数据处理
const processServiceMemoryData = (serviceData: {service_memory: { [key: string]: string }}) => {
    if (!serviceData) return;
    const service_memory: { name: string; size: string }[] = [];
    const tmp = serviceData.service_memory;

    for (const key in tmp) {
        service_memory.push({
            "name": key,
            "size": tmp[key]
        });
    }

    Object.assign(serviceTableData, service_memory);
};

// 磁盘数据处理
</script>
<style lang="scss" scoped>
</style>