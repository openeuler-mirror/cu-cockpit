<template>
    <div class="tech-indicator" v-loading="loading">
        <header class="indicator-hud">
            <div class="indicator-identity">
                <span class="indicator-identity__mark"><el-icon><DataAnalysis /></el-icon></span>
                <div>
                    <h1 class="indicator-title">实时指标</h1>
                    <div class="indicator-kicker">LIVE METRICS · CPU / MEMORY / DISK / NETWORK</div>
                </div>
            </div>
            <div class="indicator-hud__actions">
                <div class="indicator-status" :class="{ 'is-error': Boolean(loadError) }">
                    <span class="indicator-status__dot"></span>
                    <span>{{ loading ? '同步中' : loadError ? '同步异常' : '5 秒实时采样' }}</span>
                </div>
                <el-button class="indicator-action" :icon="Refresh" :loading="loading" @click="refreshMetrics">
                    刷新
                </el-button>
            </div>
        </header>

        <div v-if="loadError" class="indicator-error">
            <el-icon><WarningFilled /></el-icon>
            <span>{{ loadError }}</span>
            <el-button class="indicator-action" :icon="Refresh" @click="refreshMetrics">重试</el-button>
        </div>

        <section class="indicator-summary" aria-label="实时指标摘要">
            <div
                v-for="item in summaryItems"
                :key="item.label"
                class="indicator-summary__item"
                :style="{ '--summary-accent': item.color }"
            >
                <span class="indicator-summary__icon"><el-icon><component :is="item.icon" /></el-icon></span>
                <div>
                    <div class="indicator-summary__label">{{ item.label }}</div>
                    <div class="indicator-summary__value">
                        {{ item.value }}<span v-if="item.unit" class="indicator-summary__unit">{{ item.unit }}</span>
                    </div>
                </div>
            </div>
        </section>

        <section class="indicator-resource-grid">
            <article class="indicator-panel indicator-panel--cpu">
                <div class="indicator-panel__head">
                    <div class="indicator-panel__identity">
                        <span class="indicator-panel__mark"><el-icon><Cpu /></el-icon></span>
                        <div>
                            <h2 class="indicator-panel__title">CPU 与系统负载</h2>
                            <div class="indicator-panel__meta">PROCESSOR UTILIZATION · LOAD AVERAGE</div>
                        </div>
                    </div>
                </div>
                <div class="indicator-panel__body">
                    <div class="indicator-gauge">
                        <div ref="cpuRef" class="indicator-gauge__chart"></div>
                        <div class="indicator-gauge__caption">逻辑核心 <strong>{{ cpuCores || '—' }}</strong> 核</div>
                    </div>
                    <div class="indicator-loads">
                        <div v-for="item in loadArray" :key="item.label" class="indicator-load">
                            <span>{{ item.label }}</span><strong>{{ item.value }}</strong>
                        </div>
                    </div>
                </div>
            </article>

            <article class="indicator-panel indicator-panel--memory">
                <div class="indicator-panel__head">
                    <div class="indicator-panel__identity">
                        <span class="indicator-panel__mark"><el-icon><Memo /></el-icon></span>
                        <div>
                            <h2 class="indicator-panel__title">内存资源</h2>
                            <div class="indicator-panel__meta">RAM / SWAP AVAILABILITY</div>
                        </div>
                    </div>
                </div>
                <div class="indicator-panel__body">
                    <el-popover
                        placement="bottom"
                        :width="460"
                        popper-class="indicator-service-popper"
                        trigger="hover"
                    >
                        <el-table :data="serviceTableData" max-height="300">
                            <el-table-column prop="name" label="服务" min-width="300" />
                            <el-table-column prop="size" label="已使用" width="110" />
                        </el-table>
                        <template #reference>
                            <div class="indicator-memory-trigger">
                                <div class="indicator-memory-grid">
                                    <div class="indicator-gauge">
                                        <div ref="memoryRef" class="indicator-gauge__chart"></div>
                                        <div class="indicator-gauge__caption">可用 <strong>{{ availableGB }}</strong> GB</div>
                                    </div>
                                    <div class="indicator-gauge">
                                        <div ref="swapRef" class="indicator-gauge__chart"></div>
                                        <div class="indicator-gauge__caption">可用 <strong>{{ swapFreeGB }}</strong> GB</div>
                                    </div>
                                </div>
                            </div>
                        </template>
                    </el-popover>
                </div>
            </article>

            <article class="indicator-panel indicator-panel--disk">
                <div class="indicator-panel__head">
                    <div class="indicator-panel__identity">
                        <span class="indicator-panel__mark"><el-icon><PieChart /></el-icon></span>
                        <div>
                            <h2 class="indicator-panel__title">磁盘容量</h2>
                            <div class="indicator-panel__meta">ROOT / BOOT CAPACITY</div>
                        </div>
                    </div>
                </div>
                <div class="indicator-panel__body">
                    <div class="indicator-disk-grid">
                        <div class="indicator-disk-item">
                            <div>
                                <div class="indicator-disk-name">/</div>
                                <div class="indicator-disk-free">剩余 <strong>{{ diskInfo.total.free || '—' }}</strong> 可用</div>
                            </div>
                            <div ref="disk1" class="indicator-disk-chart"></div>
                        </div>
                        <div class="indicator-disk-item">
                            <div>
                                <div class="indicator-disk-name">/boot</div>
                                <div class="indicator-disk-free">剩余 <strong>{{ diskInfo.boot.free || '—' }}</strong> 可用</div>
                            </div>
                            <div ref="disk2" class="indicator-disk-chart"></div>
                        </div>
                    </div>
                </div>
            </article>
        </section>

        <section class="indicator-network-grid">
            <article class="indicator-panel indicator-network-panel">
                <div class="indicator-panel__head">
                    <div class="indicator-panel__identity">
                        <span class="indicator-panel__mark"><el-icon><Download /></el-icon></span>
                        <div>
                            <h2 class="indicator-panel__title">网络接收</h2>
                            <div class="indicator-panel__meta">RX RATE · LAST 20 SAMPLES</div>
                        </div>
                    </div>
                    <el-select
                        v-model="rxInterface"
                        class="indicator-network-select"
                        placeholder="选择网卡"
                        popper-class="indicator-network-popper"
                        @change="onRxInterfaceChange"
                    >
                        <el-option v-for="item in networkOptions" :key="item.value" :label="item.label" :value="item.value" />
                    </el-select>
                </div>
                <div ref="networkRxRef" class="indicator-network-chart"></div>
            </article>

            <article class="indicator-panel indicator-network-panel indicator-network-panel--tx">
                <div class="indicator-panel__head">
                    <div class="indicator-panel__identity">
                        <span class="indicator-panel__mark"><el-icon><Upload /></el-icon></span>
                        <div>
                            <h2 class="indicator-panel__title">网络发送</h2>
                            <div class="indicator-panel__meta">TX RATE · LAST 20 SAMPLES</div>
                        </div>
                    </div>
                    <el-select
                        v-model="txInterface"
                        class="indicator-network-select"
                        placeholder="选择网卡"
                        popper-class="indicator-network-popper"
                        @change="onTxInterfaceChange"
                    >
                        <el-option v-for="item in networkOptions" :key="item.value" :label="item.label" :value="item.value" />
                    </el-select>
                </div>
                <div ref="networkTxRef" class="indicator-network-chart"></div>
            </article>
        </section>
    </div>
</template>

<script lang="ts" setup name="indicatorIndex">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue';
import * as echarts from 'echarts';
import { Cpu, DataAnalysis, Download, Memo, PieChart, Refresh, Upload, WarningFilled } from '@element-plus/icons-vue';
import { storeToRefs } from 'pinia';
import { debounce } from 'lodash';
import { hardInfo, monitorStatus } from '/@/api/run/run';
import { useThemeConfig } from '/@/stores/themeConfig';

interface DiskData {
    free: string;
    used: string;
    total: string;
}

interface DiskInfo {
    total: DiskData;
    boot: DiskData;
}

interface CpuSection {
    cpu: {
        total_utilization_percent: string;
        load_average: string;
    };
}

interface MemorySection {
    memory: {
        total_mb: number;
        used_mb: number;
        available_mb: number;
        swap_total_mb: number;
        swap_used_mb: number;
        swap_free_mb: number;
    };
}

interface ServiceMemorySection {
    service_memory: Record<string, string>;
}

interface DiskSection {
    total_disk: DiskData;
    boot_disk: {
        boot_total: string;
        boot_used: string;
        boot_free: string;
    };
}

interface NetworkInterface {
    interface_name: string;
    rx: string | number;
    tx: string | number;
}

interface NetworkSection {
    network_interfaces: NetworkInterface[];
}

interface LoadItem {
    label: string;
    value: string;
}

interface ServiceMemoryItem {
    name: string;
    size: string;
}

interface NetworkOption {
    value: string;
    label: string;
}

interface NetworkSeries {
    rx: number[];
    tx: number[];
}

const themeStore = useThemeConfig();
const { themeConfig } = storeToRefs(themeStore);
const cpuRef = ref<HTMLDivElement>();
const memoryRef = ref<HTMLDivElement>();
const swapRef = ref<HTMLDivElement>();
const disk1 = ref<HTMLDivElement>();
const disk2 = ref<HTMLDivElement>();
const networkRxRef = ref<HTMLDivElement>();
const networkTxRef = ref<HTMLDivElement>();
const loading = ref(false);
const loadError = ref('');
const cpuCores = ref(0);
const cpuPercent = ref(0);
const availableGB = ref(0);
const swapFreeGB = ref(0);
const networkInterfaceCount = ref(0);
const loadArray = ref<LoadItem[]>([]);
const serviceTableData = ref<ServiceMemoryItem[]>([]);
const networkOptions = ref<NetworkOption[]>([{ value: 'all', label: '所有网卡' }]);
const rxInterface = ref('all');
const txInterface = ref('all');
const rxTimes = ref<string[]>([]);
const txTimes = ref<string[]>([]);
const diskInfo = ref<DiskInfo>({
    total: { free: '', used: '', total: '' },
    boot: { free: '', used: '', total: '' },
});
const networkData = new Map<string, NetworkSeries>();
let timer: number | null = null;
let requestPending = false;
let cpuChart: echarts.ECharts | null = null;
let memoryChart: echarts.ECharts | null = null;
let swapChart: echarts.ECharts | null = null;
let rootDiskChart: echarts.ECharts | null = null;
let bootDiskChart: echarts.ECharts | null = null;
let rxChart: echarts.ECharts | null = null;
let txChart: echarts.ECharts | null = null;

const summaryItems = computed(() => [
    { label: 'CPU 使用率', value: cpuPercent.value.toFixed(1), unit: '%', icon: Cpu, color: metricColor(cpuPercent.value) },
    { label: 'RAM 可用', value: availableGB.value.toFixed(2), unit: 'GB', icon: Memo, color: '#a855f7' },
    { label: '根目录可用', value: diskInfo.value.total.free || '—', unit: '', icon: PieChart, color: '#10f5a0' },
    { label: '网络接口', value: networkInterfaceCount.value, unit: '个', icon: DataAnalysis, color: '#22d3ee' },
]);

const metricColor = (value: number) => {
    if (value >= 80) return '#ff4d6d';
    if (value >= 50) return '#ffb020';
    return '#22d3ee';
};

const percent = (used: number, total: number) => (total > 0 ? Math.round((used / total) * 1000) / 10 : 0);
const parseNumber = (value: string | number) => Number.parseFloat(String(value).replace(/[^\d.]/g, '')) || 0;
const currentTime = () => new Date().toLocaleTimeString('zh-CN', { hour12: false });

const gaugeOption = (label: string, value: number, color: string) => ({
    title: {
        text: `${value.toFixed(1)}%`,
        subtext: label,
        left: 'center',
        top: '34%',
        textStyle: { color: '#e8f2ff', fontSize: 23, fontWeight: 800 },
        subtextStyle: { color: '#8fa2c2', fontSize: 11, lineHeight: 22 },
    },
    polar: { radius: ['69%', '82%'], center: ['50%', '50%'] },
    angleAxis: { max: 100, show: false },
    radiusAxis: { type: 'category', show: false },
    series: [
        {
            type: 'bar',
            coordinateSystem: 'polar',
            roundCap: true,
            barWidth: 18,
            showBackground: true,
            backgroundStyle: { color: 'rgba(90, 165, 255, 0.09)' },
            itemStyle: { color, shadowColor: color, shadowBlur: 12 },
            data: [value],
        },
    ],
});

const networkOption = (name: string, color: string, times: string[], values: number[]) => ({
    animationDuration: 360,
    tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(10, 18, 34, 0.94)',
        borderColor: `${color}66`,
        textStyle: { color: '#dce9fa' },
        valueFormatter: (value: number) => `${value} kB/s`,
    },
    grid: { left: 64, right: 28, top: 32, bottom: 58 },
    xAxis: {
        type: 'category',
        data: times,
        boundaryGap: false,
        axisLabel: { color: '#74849f', hideOverlap: true },
        axisLine: { lineStyle: { color: 'rgba(90, 165, 255, 0.18)' } },
        axisTick: { show: false },
    },
    yAxis: {
        type: 'value',
        name: 'kB/s',
        nameTextStyle: { color: '#74849f' },
        axisLabel: { color: '#8fa2c2' },
        splitLine: { lineStyle: { type: 'dashed', color: 'rgba(90, 165, 255, 0.1)' } },
    },
    dataZoom: [
        {
            type: 'inside',
            start: Math.max(0, 100 - (20 / Math.max(times.length, 20)) * 100),
            end: 100,
        },
        {
            height: 15,
            bottom: 14,
            borderColor: 'rgba(90, 165, 255, 0.13)',
            backgroundColor: 'rgba(10, 18, 34, 0.5)',
            fillerColor: `${color}26`,
            handleStyle: { color },
            textStyle: { color: '#74849f' },
        },
    ],
    series: [
        {
            name,
            type: 'line',
            smooth: true,
            showSymbol: false,
            lineStyle: { width: 2.5, color, shadowColor: color, shadowBlur: 10 },
            itemStyle: { color },
            areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: `${color}50` },
                    { offset: 1, color: `${color}05` },
                ]),
            },
            data: values,
        },
    ],
});

const diskOption = (value: number, color: string) => ({
    ...gaugeOption('使用率', value, color),
    polar: { radius: ['72%', '86%'], center: ['50%', '50%'] },
});

const ensureCharts = () => {
    if (cpuRef.value && !cpuChart) cpuChart = echarts.init(cpuRef.value);
    if (memoryRef.value && !memoryChart) memoryChart = echarts.init(memoryRef.value);
    if (swapRef.value && !swapChart) swapChart = echarts.init(swapRef.value);
    if (disk1.value && !rootDiskChart) rootDiskChart = echarts.init(disk1.value);
    if (disk2.value && !bootDiskChart) bootDiskChart = echarts.init(disk2.value);
    if (networkRxRef.value && !rxChart) rxChart = echarts.init(networkRxRef.value);
    if (networkTxRef.value && !txChart) txChart = echarts.init(networkTxRef.value);
};

const processCpu = (section: CpuSection) => {
    const cpu = section?.cpu;
    if (!cpu) return;
    cpuPercent.value = parseNumber(cpu.total_utilization_percent);
    const loads: LoadItem[] = [];
    const loadPattern = /([^:]+):\s*([\d.]+)/g;
    let loadMatch = loadPattern.exec(cpu.load_average);
    while (loadMatch) {
        loads.push({ label: loadMatch[1].trim(), value: loadMatch[2] });
        loadMatch = loadPattern.exec(cpu.load_average);
    }
    loadArray.value = loads;
    cpuChart?.setOption(gaugeOption('CPU 使用率', cpuPercent.value, metricColor(cpuPercent.value)), true);
};

const processMemory = (section: MemorySection) => {
    const memory = section?.memory;
    if (!memory) return;
    const ramPercent = percent(memory.used_mb, memory.total_mb);
    const swapPercent = percent(memory.swap_used_mb, memory.swap_total_mb);
    availableGB.value = Math.round((memory.available_mb / 1024) * 100) / 100;
    swapFreeGB.value = Math.round((memory.swap_free_mb / 1024) * 100) / 100;
    memoryChart?.setOption(gaugeOption('RAM', ramPercent, '#a855f7'), true);
    swapChart?.setOption(gaugeOption('交换空间', swapPercent, '#3b82f6'), true);
};

const processServiceMemory = (section: ServiceMemorySection) => {
    serviceTableData.value = Object.entries(section?.service_memory || {}).map(([name, size]) => ({ name, size }));
};

const processDisk = (section: DiskSection) => {
    if (!section?.total_disk || !section?.boot_disk) return;
    diskInfo.value.total = { ...section.total_disk };
    diskInfo.value.boot = {
        total: section.boot_disk.boot_total,
        used: section.boot_disk.boot_used,
        free: section.boot_disk.boot_free,
    };
    const rootPercent = percent(parseNumber(section.total_disk.used), parseNumber(section.total_disk.total));
    const bootPercent = percent(parseNumber(section.boot_disk.boot_used), parseNumber(section.boot_disk.boot_total));
    rootDiskChart?.setOption(diskOption(rootPercent, metricColor(rootPercent)), true);
    bootDiskChart?.setOption(diskOption(bootPercent, metricColor(bootPercent)), true);
};

const appendNetworkPoint = (name: string, rx: number, tx: number) => {
    const series = networkData.get(name) || { rx: [], tx: [] };
    series.rx.push(rx);
    series.tx.push(tx);
    if (series.rx.length > 20) series.rx.shift();
    if (series.tx.length > 20) series.tx.shift();
    networkData.set(name, series);
};

const processNetwork = (section: NetworkSection) => {
    const interfaces = section?.network_interfaces || [];
    networkInterfaceCount.value = interfaces.length;
    let allRx = 0;
    let allTx = 0;
    interfaces.forEach((item) => {
        const rx = Math.round((parseNumber(item.rx) / 1024) * 100) / 100;
        const tx = Math.round((parseNumber(item.tx) / 1024) * 100) / 100;
        allRx += rx;
        allTx += tx;
        appendNetworkPoint(item.interface_name, rx, tx);
    });
    appendNetworkPoint('all', Math.round(allRx * 100) / 100, Math.round(allTx * 100) / 100);
    networkOptions.value = [
        { value: 'all', label: '所有网卡' },
        ...interfaces.map((item) => ({ value: item.interface_name, label: item.interface_name })),
    ];
    if (!networkData.has(rxInterface.value)) rxInterface.value = 'all';
    if (!networkData.has(txInterface.value)) txInterface.value = 'all';
    const sampledAt = currentTime();
    rxTimes.value.push(sampledAt);
    txTimes.value.push(sampledAt);
    if (rxTimes.value.length > 20) rxTimes.value.shift();
    if (txTimes.value.length > 20) txTimes.value.shift();
    updateNetworkCharts();
};

const updateNetworkCharts = () => {
    const rxValues = networkData.get(rxInterface.value)?.rx || [];
    const txValues = networkData.get(txInterface.value)?.tx || [];
    rxChart?.setOption(networkOption('接收', '#22d3ee', rxTimes.value, rxValues), true);
    txChart?.setOption(networkOption('发送', '#a855f7', txTimes.value, txValues), true);
};

const getAllData = async () => {
    if (requestPending) return;
    requestPending = true;
    if (!cpuChart) loading.value = true;
    loadError.value = '';
    try {
        const response = await monitorStatus('all');
        ensureCharts();
        processCpu(response?.[0]);
        processMemory(response?.[1]);
        processServiceMemory(response?.[2]);
        processDisk(response?.[3]);
        processNetwork(response?.[4]);
    } catch (error) {
        loadError.value = '实时指标同步失败，已保留上次成功数据。';
        console.error('获取实时指标失败:', error);
    } finally {
        loading.value = false;
        requestPending = false;
    }
};

const getCpuCores = async () => {
    try {
        const response = await hardInfo('cpu');
        cpuCores.value = Number(response?.cpu?.cores) || 0;
    } catch (error) {
        console.error('获取 CPU 核心数失败:', error);
    }
};

const restartTimer = () => {
    if (timer) window.clearInterval(timer);
    timer = window.setInterval(getAllData, 5000);
};

const refreshMetrics = async () => {
    await getAllData();
    restartTimer();
};

const onRxInterfaceChange = () => {
    const series = networkData.get(rxInterface.value);
    if (series) series.rx = [];
    rxTimes.value = [];
    updateNetworkCharts();
    restartTimer();
};

const onTxInterfaceChange = () => {
    const series = networkData.get(txInterface.value);
    if (series) series.tx = [];
    txTimes.value = [];
    updateNetworkCharts();
    restartTimer();
};

const resizeCharts = debounce(() => {
    [cpuChart, memoryChart, swapChart, rootDiskChart, bootDiskChart, rxChart, txChart].forEach((chart) => chart?.resize());
}, 250);

const mountIndicatorTechShell = () => document.documentElement.classList.add('theme-tech-dark');
const restoreIndicatorTechShell = () => {
    if (!themeConfig.value.isTechTheme) document.documentElement.classList.remove('theme-tech-dark');
};
const resetMainScroll = async () => {
    await nextTick();
    const scrollContainer = document.querySelector<HTMLElement>('.layout-main-scroll.el-scrollbar__wrap');
    if (scrollContainer) scrollContainer.scrollTop = 0;
};

onMounted(async () => {
    mountIndicatorTechShell();
    await resetMainScroll();
    window.addEventListener('resize', resizeCharts);
    await nextTick();
    ensureCharts();
    await Promise.all([getCpuCores(), getAllData()]);
    restartTimer();
});

onUnmounted(() => {
    if (timer) window.clearInterval(timer);
    window.removeEventListener('resize', resizeCharts);
    resizeCharts.cancel();
    [cpuChart, memoryChart, swapChart, rootDiskChart, bootDiskChart, rxChart, txChart].forEach((chart) => chart?.dispose());
    restoreIndicatorTechShell();
});
</script>

<style lang="scss">
@use './tech-indicator.scss';
</style>