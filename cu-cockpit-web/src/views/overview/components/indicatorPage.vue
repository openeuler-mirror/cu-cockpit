<template>
  <div class="card">
    <el-row :gutter="20" class="metric-row" @click="toIndicator">
      <el-col :span="8">
        <div class="metric-card" :class="{ 'is-danger': cpuUsage > 80 }"
          :style="{ '--metric': String(cpuUsage), '--metric-color': cpuUsage > 80 ? 'var(--tech-red)' : 'var(--tech-cyan)' }">
          <div class="metric-card__head">
            <i class="iconfont icon-yingjianxinxi"></i>
            <span>CPU 使用率</span>
          </div>
          <div class="ring">
            <div class="ring__inner">
              <div class="ring__num">{{ cpuUsage }}<small>%</small></div>
              <div class="ring__cap">USAGE</div>
            </div>
          </div>
          <div class="metric-card__foot">核心数：{{ cpuCores }} 核</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="metric-card" :class="{ 'is-danger': memUsage > 80 }"
          :style="{ '--metric': String(memUsage), '--metric-color': memUsage > 80 ? 'var(--tech-red)' : 'var(--tech-purple)' }">
          <div class="metric-card__head">
            <i class="iconfont icon-neicun"></i>
            <span>内存使用</span>
          </div>
          <div class="ring">
            <div class="ring__inner">
              <div class="ring__num">{{ memUsage }}<small>%</small></div>
              <div class="ring__cap">MEMORY</div>
            </div>
          </div>
          <div class="metric-card__foot">{{ memUsed }} GB / {{ memTotal }} GB</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="metric-card" :class="{ 'is-danger': diskUsage > 80 }"
          :style="{ '--metric': String(diskUsage), '--metric-color': diskUsage > 80 ? 'var(--tech-red)' : 'var(--tech-green)' }">
          <div class="metric-card__head">
            <i class="iconfont icon-04"></i>
            <span>磁盘使用率</span>
          </div>
          <div class="ring">
            <div class="ring__inner">
              <div class="ring__num">{{ diskUsage }}<small>%</small></div>
              <div class="ring__cap">DISK</div>
            </div>
          </div>
          <div class="metric-card__foot">根目录剩余 {{ diskUsed }} 可用</div>
        </div>
      </el-col>
    </el-row>
    <el-card style="margin-top: 20px;">
      <div class="echarts-title">
        <div class="echarts-text"><span class="echarts-bar"></span>网络接口流量</div>
        <div class="echarts-sift">网卡：
          <el-select v-model="optVal" placeholder="Select" style="width: 180px" @change="netChange">
            <el-option v-for="item in options" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </div>
      </div>
      <div class="echarts-div" ref="diskIoRef"></div>
    </el-card>
  </div>
</template>

<script lang="ts" setup name="indicator">
import { reactive, onMounted, ref, onUnmounted } from 'vue';
import * as echarts from 'echarts';
import { monitorStatus, hardInfo } from '/@/api/run/run';
import { useRouter } from 'vue-router';

interface NetworkInterface {
  interface_name: string;
  rx: string;
  tx: string;
}

interface CpuInfo {
  cores: number;
  total_utilization_percent: string;
}

interface MemoryInfo {
  used_mb: number;
  total_mb: number;
}

interface DiskInfo {
  used: string;
  total: string;
  free: string;
}

interface MonitorData {
  cpu: CpuInfo;
  memory: MemoryInfo;
  total_disk: DiskInfo;
  network_interfaces: NetworkInterface[];
}

interface OptionItem {
  value: string;
  label: string;
}

interface NetworkData {
  rx: number[];
  tx: number[];
}

const router = useRouter();
const toIndicator = () => {
  router.push({
    name: 'indicator',
  });
};

// 定时器
let lineTimer: number | null = null;
const REFRESH_INTERVAL = 5000;

// CPU数据
const cpuCores = ref(0);
const cpuUsage = ref(0);

// 内存数据
const memUsage = ref(0);
const memUsed = ref(0);
const memTotal = ref(0);

// 磁盘数据
const diskUsage = ref(0);
const diskUsed = ref('');

// 网络图表相关
const optVal = ref('');
const options: OptionItem[] = reactive([]);
const diskIoRef = ref<HTMLElement | null>(null);
let diskIoDom: echarts.ECharts | null = null;
const diskData = new Map<string, NetworkData>();
const networkXAxis: string[] = [];

// 防抖函数
const debounce = (func, delay) => {
  let timeoutId: number;
  return (...args) => {
    window.clearTimeout(timeoutId);
    timeoutId = window.setTimeout(() => func.apply(null, args), delay);
  };
};

// 获取硬件信息
const fetchHardwareInfo = async () => {
  try {
    const res = await hardInfo('cpu');
    cpuCores.value = res.cpu.cores;
  } catch (error) {
    console.error('获取CPU信息失败:', error);
  }
};

// 格式化网络数据
const formatNetworkData = (value: string, unit: string): number => {
  return Math.round(Number((value.split(` ${unit}`))[0]) / 1024 * 100) / 100;
};

// 更新网络选项
const updateNetworkOptions = (netTmp: NetworkInterface[]) => {
  const opsTmp: OptionItem[] = [{
    value: "all",
    label: "所有"
  }];

  let tmpRx = 0;
  let tmpTx = 0;

  for (let i = 0; i < netTmp.length; i++) {
    const rx = formatNetworkData(netTmp[i].rx, 'B/S');
    const tx = formatNetworkData(netTmp[i].tx, 'B/s');
    tmpRx += rx;
    tmpTx += tx;

    if (diskData.has(netTmp[i].interface_name)) {
      const rxArray = diskData.get(netTmp[i].interface_name)!.rx;
      const txArray = diskData.get(netTmp[i].interface_name)!.tx;
      rxArray.push(rx);
      txArray.push(tx);
    } else {
      diskData.set(netTmp[i].interface_name, {
        rx: [rx],
        tx: [tx]
      });
    }

    opsTmp.push({
      value: netTmp[i].interface_name,
      label: netTmp[i].interface_name
    });
  }

  if (diskData.has('all')) {
    const allData = diskData.get('all')!;
    allData.rx.push(tmpRx);
    allData.tx.push(tmpTx);
  } else {
    diskData.set('all', {
      rx: [tmpRx],
      tx: [tmpTx]
    });
  }

  return opsTmp;
};

// 获取当前时间
const currentTime = (): string => {
  const time = new Date();
  const hour = time.getHours();
  const minute = time.getMinutes();
  const second = time.getSeconds();
  return `${hour < 10 ? '0' + hour : hour}:${minute < 10 ? '0' + minute : minute}:${second < 10 ? '0' + second : second}`;
};

// 更新图表数据
const updateChartData = () => {
  if (!diskIoDom || !diskData.has(optVal.value)) return;

  const currentData = diskData.get(optVal.value)!;

  if (currentData.rx.length > 20) {
    currentData.rx.shift();
    currentData.tx.shift();
  }

  diskIoDom.setOption({
    xAxis: { data: networkXAxis },
    series: [
      { data: currentData.rx },
      { data: currentData.tx }
    ],
  });
};

// 初始化图表
const initChart = () => {
  if (!diskIoRef.value) return;

  diskIoDom = echarts.init(diskIoRef.value);

  const option = {
    title: [{
      left: 'center',
      text: ' ',
      show: true,
    }],
    zlevel: 1,
    z: 1,
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(10, 18, 34, 0.92)',
      borderColor: 'rgba(34, 211, 238, 0.35)',
      borderWidth: 1,
      textStyle: { color: '#c7d2e5' },
      formatter: params => {
        let res = params[0].name + '<br/>';
        for (const item of params) {
          res += item.marker + ' ' + item.seriesName + ' : ' + item.data + 'KB<br/>';
        }
        return res;
      },
    },
    grid: { left: '6%', right: '6%', bottom: '20%', top: '18%' },
    legend: {
      top: '5%',
      right: '4%',
      itemWidth: 16,
      textStyle: {
        color: '#8fa2c2',
      },
      icon: 'circle',
    },
    xAxis: {
      name: '时间',
      nameTextStyle: {
        color: '#74849f',
        padding: [0, 0, 0, 0]
      },
      axisLine: { lineStyle: { color: 'rgba(90, 165, 255, 0.2)' } },
      axisLabel: { color: '#8fa2c2' },
      data: networkXAxis,
      boundaryGap: false
    },
    yAxis: {
      name: '速率(kB/S)',
      nameTextStyle: { color: '#74849f' },
      axisLabel: { color: '#8fa2c2' },
      axisLine: { show: false },
      splitLine: {
        lineStyle: {
          type: 'dashed',
          color: 'rgba(90, 165, 255, 0.1)',
          opacity: 1,
        },
      },
    },
    series: [{
      name: 'rx',
      type: 'line',
      smooth: true,
      lineStyle: {
        width: 2.5,
        color: '#22d3ee',
        shadowColor: 'rgba(34, 211, 238, 0.6)',
        shadowBlur: 12,
      },
      itemStyle: {
        color: '#22d3ee',
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(34, 211, 238, 0.35)' },
          { offset: 1, color: 'rgba(34, 211, 238, 0.02)' },
        ]),
      },
      data: diskData.get(optVal.value)?.rx || [],
      showSymbol: false,
      symbolSize: 6,
    }, {
      name: 'tx',
      type: 'line',
      smooth: true,
      lineStyle: {
        width: 2.5,
        color: '#a855f7',
        shadowColor: 'rgba(168, 85, 247, 0.6)',
        shadowBlur: 12,
      },
      itemStyle: {
        color: '#a855f7',
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(168, 85, 247, 0.3)' },
          { offset: 1, color: 'rgba(168, 85, 247, 0.02)' },
        ]),
      },
      data: diskData.get(optVal.value)?.tx || [],
      showSymbol: false,
      symbolSize: 6,
    }],
    dataZoom: [{ startValue: 0, show: true }],
  };

  diskIoDom.setOption(option);
};

// 处理监控数据
const processMonitorData = (res: MonitorData[]) => {
  // CPU数据处理
  const cpu = res[0].cpu;
  cpuUsage.value = Number(cpu.total_utilization_percent.split('%')[0]);

  // 内存数据处理
  const memory = res[1].memory;
  memUsage.value = Math.round(memory.used_mb / memory.total_mb * 10000) / 100;
  memTotal.value = Math.round(memory.total_mb / 1024 * 100) / 100;
  memUsed.value = Math.round(memory.used_mb / 1024 * 100) / 100;

  // 磁盘数据处理
  const disk = res[3].total_disk;
  diskUsage.value = Math.round(
    Number(disk.used.split("G")[0]) / Number(disk.total.split("G")[0]) * 10000
  ) / 100;
  diskUsed.value = disk.free;

  // 网络数据处理
  const netTmp = res[4].network_interfaces;
  const opsTmp = updateNetworkOptions(netTmp);

  networkXAxis.push(currentTime());
  if (networkXAxis.length > 20) {
    networkXAxis.shift();
  }

  // 初始化或更新图表
  if (!diskIoDom) {
    Object.assign(options, opsTmp);
    optVal.value = options[0]?.value || '';
    initChart();
  } else {
    updateChartData();
  }
};

// 获取所有监控数据
const getAllData = async () => {
  try {
    const res = await monitorStatus('all');
    processMonitorData(res);
  } catch (error) {
    console.error('获取监控数据失败:', error);
  }
};

// 网络选项变更处理
const netChange = () => {
  getAllData();
};

// 定时任务处理
const handleTimer = () => {
  // const fetchData = async () => {
  //   await getAllData();
  //   lineTimer = window.setTimeout(fetchData, REFRESH_INTERVAL);
  // };

  // lineTimer = window.setTimeout(fetchData, REFRESH_INTERVAL);
  lineTimer = setInterval(async() => {
    await getAllData();
  }, REFRESH_INTERVAL);
};

// 清理定时器
const clearTimer = () => {
  if (lineTimer) {
    // window.clearTimeout(lineTimer);
    clearInterval(lineTimer);
    lineTimer = null;
  }
};

// 清理图表实例
const disposeChart = () => {
  if (diskIoDom) {
    diskIoDom.dispose();
    diskIoDom = null;
  }
};

onMounted(() => {
  fetchHardwareInfo();
  getAllData();
  handleTimer();

  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  clearTimer();
  disposeChart();

  // 移除事件监听器
  window.removeEventListener('resize', handleResize);
});

const handleResize = debounce(() => {
  if (diskIoDom) {
    diskIoDom.resize();
  }
}, 300);
</script>

<style scoped lang="scss">
.card {
  width: 100%;
}

.metric-row {
  cursor: pointer;
}

/* 指标卡片：玻璃面板 + 顶部霓虹描边 */
.metric-card {
  --metric: 0;
  --metric-color: var(--tech-cyan, #22d3ee);
  position: relative;
  padding: 20px 18px 18px;
  border-radius: 14px;
  background: rgba(17, 27, 48, 0.55);
  border: 1px solid var(--tech-border, rgba(90, 165, 255, 0.16));
  backdrop-filter: blur(14px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04), 0 10px 30px rgba(0, 0, 0, 0.4);
  text-align: center;
  overflow: hidden;
  transition: border-color 0.3s ease, box-shadow 0.3s ease, transform 0.3s ease;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--metric-color), transparent);
    opacity: 0.9;
  }

  &:hover {
    transform: translateY(-3px);
    border-color: var(--metric-color);
    box-shadow: 0 0 26px -6px var(--metric-color), 0 14px 34px rgba(0, 0, 0, 0.45);
  }

  &.is-danger {
    animation: metric-alert 1.4s ease-in-out infinite;
  }

  &__head {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.5px;
    color: #e8f2ff;

    .iconfont {
      font-size: 18px;
      color: var(--metric-color);
    }
  }

  &__foot {
    margin-top: 14px;
    font-size: 12px;
    color: var(--tech-text-dim, #74849f);
    letter-spacing: 0.3px;
  }
}

@keyframes metric-alert {
  0%, 100% { box-shadow: 0 0 0 0 rgba(255, 77, 109, 0); }
  50% { box-shadow: 0 0 24px -4px rgba(255, 77, 109, 0.65); }
}

/* 环形仪表：conic-gradient 进度 + 中空数字 */
.ring {
  --size: 132px;
  position: relative;
  width: var(--size);
  height: var(--size);
  margin: 16px auto 4px;
  border-radius: 50%;
  background:
    conic-gradient(var(--metric-color) calc(var(--metric) * 1%), rgba(255, 255, 255, 0.06) 0);
  filter: drop-shadow(0 0 10px color-mix(in srgb, var(--metric-color) 45%, transparent));
  transition: background 0.6s ease;

  /* 内圈遮罩，形成圆环 */
  &::before {
    content: '';
    position: absolute;
    inset: 12px;
    border-radius: 50%;
    background: radial-gradient(circle at 50% 35%, #101a2f 0%, #0a1120 100%);
    box-shadow: inset 0 0 18px rgba(0, 0, 0, 0.6);
  }

  /* 起点高亮小点 */
  &::after {
    content: '';
    position: absolute;
    top: 4px;
    left: 50%;
    width: 6px;
    height: 6px;
    margin-left: -3px;
    border-radius: 50%;
    background: var(--metric-color);
    box-shadow: 0 0 10px var(--metric-color);
  }

  &__inner {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 1;
  }

  &__num {
    font-size: 30px;
    font-weight: 700;
    line-height: 1;
    color: #fff;
    font-variant-numeric: tabular-nums;
    text-shadow: 0 0 16px color-mix(in srgb, var(--metric-color) 65%, transparent);

    small {
      font-size: 14px;
      font-weight: 600;
      margin-left: 2px;
      color: var(--metric-color);
    }
  }

  &__cap {
    margin-top: 6px;
    font-size: 11px;
    letter-spacing: 2px;
    color: var(--tech-text-dim, #74849f);
  }
}

.echarts-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;

  .echarts-text {
    display: flex;
    align-items: center;
    left: 0;
    font-size: 15px;
    font-weight: 600;
    color: #e8f2ff;
    line-height: 1.5;

    .echarts-bar {
      width: 4px;
      height: 15px;
      margin-right: 8px;
      border-radius: 2px;
      background: linear-gradient(180deg, var(--tech-cyan, #22d3ee), var(--tech-purple, #a855f7));
      box-shadow: 0 0 10px rgba(34, 211, 238, 0.5);
    }
  }

  .echarts-sift {
    right: 0;
    color: var(--tech-text, #c7d2e5);
  }
}

.echarts-div {
  height: 335px;
}
</style>