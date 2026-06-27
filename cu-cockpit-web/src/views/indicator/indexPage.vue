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
const processDiskData = (diskDataRes: {[key: string]:{[key: string]:string}}) => {
    if (!diskDataRes) return;

    // 根目录数据
    const total_used = parseFloat((diskDataRes.total_disk.used.split("G"))[0]);
    const total_total = parseFloat((diskDataRes.total_disk.total.split("G"))[0]);
    const total_percent = Math.round(total_used / total_total * 10000) / 100;
    const total_percent_array = (total_percent + '%').split(".");

    diskInfo.value.total.free = diskDataRes?.total_disk?.free ?? '';
    diskInfo.value.total.used = diskDataRes?.total_disk?.used ?? '';
    diskInfo.value.total.total = diskDataRes?.total_disk?.total ?? '';

    // Boot分区数据
    const boot_used = parseFloat((diskDataRes.boot_disk.boot_used.split("M"))[0]);
    const boot_total = parseFloat((diskDataRes.boot_disk.boot_total.split("M"))[0]);
    const boot_percent = Math.round(boot_used / boot_total * 10000) / 100;
    const bootl_percent_array = (boot_percent + '%').split(".");
    diskInfo.value.boot.free = diskDataRes?.boot_disk?.boot_free ?? '';
    diskInfo.value.boot.used = diskDataRes?.boot_disk?.boot_used ?? '';
    diskInfo.value.boot.total = diskDataRes?.boot_disk?.boot_total ?? '';

    if (!disk1Dom && !disk2Dom) {
        disk1Dom = echarts.init(disk1.value);
        disk2Dom = echarts.init(disk2.value);
        diskEchart(disk1Dom, total_percent, total_percent_array);
        diskEchart(disk2Dom, boot_percent, bootl_percent_array);
    } else {
        disk1Dom?.setOption({
            title: [{
                text: `{a|${total_percent_array[0]}.}{b|${total_percent_array[1] ? total_percent_array[1] : '0%'}}`,
            }],
            series: [{
                data: [total_percent],
            }]
        });

        disk2Dom?.setOption({
            title: [{
                text: `{a|${bootl_percent_array[0]}.}{b|${bootl_percent_array[1] ? bootl_percent_array[1] : '0%'}}`,
            }],
            series: [{
                data: [boot_percent],
            }]
        });
    }
};

// 网络数据处理
const processNetworkData = (networkDataRes:{network_interfaces: Array<{interface_name: string, rx: string|number, tx: string|number}>}) => {
    if (!networkDataRes) return;

    const network_interfaces = networkDataRes.network_interfaces;
    const opsTmp = [{
        value: "all",
        label: "所有"
    }];

    let tmpRx = 0;
    let tmpTx = 0;

    for (let i = 0; i < network_interfaces.length; i++) {
        const rx = Math.round(parseFloat((network_interfaces[i].rx?.split(' B/S'))[0]) / 1024 * 100) / 100;
        const tx = Math.round(parseFloat((network_interfaces[i].tx?.split(' B/s'))[0]) / 1024 * 100) / 100;

        tmpRx += Number(rx);
        tmpTx += Number(tx);

        if (diskData.has(network_interfaces[i].interface_name)) {
            const rxArray = diskData.get(network_interfaces[i].interface_name)['rx'];
            const txArray = diskData.get(network_interfaces[i].interface_name)['tx'];
            rxArray.push(rx);
            txArray.push(tx);
        } else {
            diskData.set(network_interfaces[i].interface_name, {
                rx: [rx],
                tx: [tx]
            });
        }

        opsTmp.push({
            value: network_interfaces[i].interface_name,
            label: network_interfaces[i].interface_name
        });
    }

    if (diskData.has('all')) {
        const rx = diskData.get('all')['rx'];
        const tx = diskData.get('all')['tx'];
        rx.push(tmpRx);
        tx.push(tmpTx);
    } else {
        diskData.set('all', {
            rx: [tmpRx],
            tx: [tmpTx]
        });
    }

    networkXAxis2.push(currentTime());
    networkXAxis.push(currentTime());

    if (networkXAxis.length > 20) {
        networkXAxis.shift();
    }

    if (networkXAxis2.length > 20) {
        networkXAxis2.shift();
    }

    if (!diskIoDom) {
        Object.assign(options, opsTmp);
        optVal.value = options[0].value;
        optVal2.value = options[0].value;
        diskIoDom = echarts.init(diskIoRef.value);
        diskIoDom2 = echarts.init(diskIoRefs.value);

        const seriesRx = createSeriesData('rx', diskData.get(optVal.value)['rx']);
        const seriesTx = createSeriesData('tx', diskData.get(optVal2.value)['tx']);

        diskIoEchart(diskIoDom2, networkXAxis2, seriesTx);
        diskIoEchart(diskIoDom, networkXAxis, seriesRx);
    } else {
        if (diskData.get(optVal.value)['rx'].length > 20) {
            diskData.get(optVal.value)['rx'].shift();
        }

        if (diskData.get(optVal2.value)['tx'].length > 20) {
            diskData.get(optVal2.value)['tx'].shift();
        }

        diskIoDom.setOption({
            xAxis: { data: networkXAxis },
            series: [{
                data: diskData.get(optVal.value)['rx']
            }],
        });

        diskIoDom2?.setOption({
            xAxis: { data: networkXAxis2 },
            series: [{
                data: diskData.get(optVal2.value)['tx']
            }],
        });
    }
};

// 创建图表系列数据
const createSeriesData = (name: string, data:Array<number|string>) => {
    const colors = {
        rx: {
            areaStart: 'rgba(0, 94, 235, .1)',
            areaEnd: 'rgba(0, 94, 235, .2)',
            lineStart: 'rgba(27, 143, 60)',
            lineEnd: 'rgba(27, 143, 60)'
        },
        tx: {
            areaStart: 'rgba(0, 94, 235, .1)',
            areaEnd: 'rgba(0, 94, 235, .2)',
            lineStart: 'rgba(249, 199, 79)',
            lineEnd: 'rgba(249, 199, 79)'
        }
    };

    return {
        name: name,
        type: 'line',
        itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: colors[name as keyof typeof colors].lineStart },
                { offset: 1, color: colors[name as keyof typeof colors].lineEnd },
            ]),
        },
        areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: colors[name as keyof typeof colors].areaStart },
                { offset: 1, color: colors[name as keyof typeof colors].areaEnd },
            ]),
        },
        data: data,
        // showSymbol: false,
         symbolSize: 6,
    };
};

// ECharts配置函数
const barPolarEchart = (dom: echarts.ECharts | null, subtext: string, data: number, titleArray: string[], seriesColor?: object|null) => {
    const option = {
        title: [
            {
                text: `{a|${titleArray[0]}.}{b|${titleArray[1] ? titleArray[1] : '0%'}}`,
                textStyle: {
                    rich: {
                        a: { fontSize: '22' },
                        b: { fontSize: '14', padding: [5, 0, 0, 0] },
                    },
                    color: '#06c',
                    lineHeight: 25,
                    fontWeight: 500,
                },
                left: '49%',
                top: '32%',
                subtext,
                subtextStyle: {
                    color: '#BBBFC4',
                    fontSize: 12,
                },
                textAlign: 'center',
            },
        ],
        polar: {
            radius: ['68%', '80%'],
            center: ['50%', '50%'],
        },
        angleAxis: {
            max: 100,
            show: false,
        },
        radiusAxis: {
            type: 'category',
            show: true,
            axisLabel: { show: false },
            axisLine: { show: false },
            axisTick: { show: false },
        },
        series: [
            {
                type: 'bar',
                roundCap: true,
                barWidth: 30,
                showBackground: true,
                coordinateSystem: 'polar',
                backgroundStyle: {
                    color: 'rgb(242 245 249)',
                },
                color: seriesColor || [
                    new echarts.graphic.LinearGradient(0, 1, 0, 0, [
                        { offset: 0, color: '#06c' },
                        { offset: 1, color: '#06c' },
                    ]),
                ],
                label: { show: false },
                data: [data],
            },
        ],
    };
    dom?.setOption(option);
};

const diskEchart = (diskDom:echarts.ECharts | null, data: number, titleArray: Array<string>) => {
    const option = {
        title: [
            {
                text: `{a|${titleArray[0]}.}{b|${titleArray[1] ? titleArray[1] : '0%'}}`,
                textStyle: {
                    rich: {
                        a: { fontSize: '22', fontWeight: 900 },
                        b: { fontSize: '16', padding: [5, 0, 0, 0] },
                    },
                    color: '#06c',
                    lineHeight: 25,
                    fontWeight: 900,
                },
                subtext: '磁盘使用率',
                subtextStyle: {
                    color: '#BBBFC4',
                    fontSize: 12,
                },
                left: '49%',
                top: '30%',
                textAlign: 'center',
            },
        ],
        polar: {
            radius: ['84%', '96%'],
            center: ['50%', '50%'],
        },
        angleAxis: {
            max: 100,
            show: false,
        },
        radiusAxis: {
            type: 'category',
            show: true,
            axisLabel: { show: false },
            axisLine: { show: false },
            axisTick: { show: false },
        },
        series: [
            {
                type: 'bar',
                roundCap: true,
                barWidth: 30,
                showBackground: true,
                coordinateSystem: 'polar',
                backgroundStyle: {
                    color: 'rgb(242 245 249)',
                },
                color: [
                    new echarts.graphic.LinearGradient(0, 1, 0, 0, [
                        { offset: 0, color: '#06c' },
                        { offset: 1, color: '#06c' },
                    ]),
                ],
                label: { show: false },
                data: [data],
            },
        ],
    };
    diskDom?.setOption(option);
};

const diskIoEchart = (diskIoDom: echarts.ECharts | null, xAxis: string[], seriesData: object) => { 
    const option = {
        title: [{ left: 'center', text: ' ', show: true }],
        zlevel: 1,
        z: 1,
        tooltip: {
            trigger: 'axis',
            formatter: params => {
                let res = params[0]?.name + '<br/>';
                for (const item of params) {
                    res += item.marker + ' ' + item.seriesName + ' : ' + item.data + '<br/>';
                }
                return res;
            },
        },
        grid: { left: '7%', right: '7%', bottom: '20%', top: '20%' },
        legend: {
            top: '5%',
            right: '4%',
            itemWidth: 16,
            textStyle: { color: '#646A73' },
            icon: 'circle',
        },
        xAxis: {
            name: '时间',
            data: xAxis,
            boundaryGap: false
        },
        yAxis: {
            name: '速率(kB/S)',
            splitLine: {
                lineStyle: {
                    type: 'dashed',
                    opacity: 1,
                },
            },
        },
        series: [seriesData],
        dataZoom: [{ startValue: 0, show: true }],
    };
    diskIoDom?.setOption(option);
};

// 工具函数
const parsePercentTitle = (percentStr: string): string[] => {
    let title = percentStr.split(".");
    if (title.length == 1) {
        title = [(title[0].split("%"))[0]];
    }
    return title;
};


const handleTimer = () => {
    lineTimer.value = window.setInterval(() => {
        getAllData();
    }, 5000);
};

const setSeriesColor = (percent: number) => {
    if (percent > 50 && percent < 80) {
        return [new echarts.graphic.LinearGradient(0, 1, 0, 0, [
            { offset: 0, color: '#ffe927' },
            { offset: 1, color: '#ffe927' },
        ])];
    } else if (percent > 80) {
        return [new echarts.graphic.LinearGradient(0, 1, 0, 0, [
            { offset: 0, color: 'red' },
            { offset: 1, color: 'red' },
        ])];
    }
    return null;
};

const currentTime = () => {
    const time = new Date();
    const hour = time.getHours();
    const minute = time.getMinutes();
    const second = time.getSeconds();
    return (hour < 10 ? '0' + hour : hour) + ':' +
        (minute < 10 ? '0' + minute : minute) + ':' +
        (second < 10 ? '0' + second : second);
};

const netChange = async (value: string | number) => {
    if (lineTimer.value) clearInterval(lineTimer.value);
    diskData.get(value)['rx'] = [];
    networkXAxis.splice(0, networkXAxis.length);
    getAllData();
    handleTimer();
};

const netChange2 = async (value: string | number) => { 
    if (lineTimer.value) clearInterval(lineTimer.value);
    diskData.get(value)['tx'] = [];
    networkXAxis2.splice(0, networkXAxis2.length);
    getAllData();
    handleTimer();
};

const handleResize = debounce(() => {
    cpuDom?.resize();
    memoryDom?.resize();
    swapDom?.resize();
    disk1Dom?.resize();
    disk2Dom?.resize();
    diskIoDom?.resize();
    diskIoDom2?.resize();
}, 300);
</script>
<style lang="scss" scoped>

.indicator {
    padding: 10px;
    min-height: calc(100vh - 105px);
}

.indicator-card {
    width: 100%;
    background: var(--el-color-white);
    color: var(--el-text-color-primary);
    border-radius: 8px;
    // box-shadow: 2px 2px 7px 1px #f0f0f0;
    box-shadow: var(--el-box-shadow-light);

    .indicator-card-title {
        padding-left: 20px;
        padding-top: 12px;
        font-size: 14px;
        line-height: 1.5;
        position: relative;
    }
}

.cpu,
.load,
.memory,
.swap {
    text-align: center;
    padding-bottom: 8px;
    font-size: 12px;

    .echarts-div {
        height: 140px;
    }
}


.indicator-card-disk {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 165px;

    .disk-echarts {
        margin-top: 22px;
        width: 50%;
        height: 120px;
    }

    .title {
        width: 50%;
        color: #06c;
        font-size: 18px;

        .title-text,
        .capacity {
            padding-left: 20px;
            word-wrap: break-word;
            word-break: normal;
        }

        .capacity {
            font-size: 12px;
            margin-top: 4px;
            color: #303133
        }
    }
}

.network-card {
    margin-top: 20px;
}

.monitor-title {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-right: 20px;
}
</style>