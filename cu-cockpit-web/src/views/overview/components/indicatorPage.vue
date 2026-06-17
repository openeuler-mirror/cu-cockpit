<template>
  <div class="card">
    <el-row :gutter="20" @click="toIndicator">
      <el-col :span="8">
        <div class="el-card cpu">
          <h3>CPU 使用率</h3>
          <i class="font32 iconfont icon-yingjianxinxi"></i>
          <div class="high-usage-text">{{ cpuUsage }}% </div>
          <div class="progress">
            <div class="progress-bar" :class="{ 'high-usage': cpuUsage > 80 }" :style="{ width: cpuUsage + '%' }">
            </div>
          </div>
          核心数：{{ cpuCores }}核
        </div>
      </el-col>
      <el-col :span="8">
        <div class="el-card memory">
          <h3>内存使用</h3>
          <i class="font32 iconfont icon-neicun"></i>
          <div class="high-usage-text">{{ memUsage }}%</div>
          <div class="progress">
            <div class="progress-bar" :class="{ 'high-usage': memUsage > 80 }" :style="{ width: memUsage + '%' }">
            </div>
          </div>
          {{ memUsed }} GB / {{ memTotal }} GB
        </div>
      </el-col>
      <el-col :span="8">
        <div class="el-card directory">
          <h3>磁盘使用率</h3>
          <i class="font32 iconfont icon-04"></i>
          <div class="high-usage-text">
            {{ diskUsage }}%
          </div>
          <div class="progress">
            <div class="progress-bar" :class="{ 'high-usage': diskUsage > 80 }" :style="{ width: diskUsage + '%' }">
            </div>
          </div>
          根目录剩余 {{ diskUsed }} 可用
        </div>
      </el-col>
    </el-row>
    <el-card style="margin-top: 20px;">
      <div class="echarts-title">
        <div class="echarts-text">网络接口流量</div>
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
        color: '#646A73',
      },
      icon: 'circle',
    },
    xAxis: {
      name: '时间',
      nameTextStyle: {
        padding: [0, 0, 0, 0]
      },
      data: networkXAxis,
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
    series: [{
      name: 'rx',
      type: 'line',
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(27, 143, 60)' },
          { offset: 1, color: 'rgba(27, 143, 60)' },
        ]),
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(0, 94, 235, .1)' },
          { offset: 1, color: 'rgba(0, 94, 235, .2)' },
        ]),
      },
      data: diskData.get(optVal.value)?.rx || [],
      // showSymbol: false,
      symbolSize: 6,
    }, {
      name: 'tx',
      type: 'line',
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(249, 199, 79)' },
          { offset: 1, color: 'rgba(249, 199, 79)' },
        ]),
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(0, 94, 235, .1)' },
          { offset: 1, color: 'rgba(0, 94, 235, .2)' },
        ]),
      },
      data: diskData.get(optVal.value)?.tx || [],
      // showSymbol: false,
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

.card-header {
  font-size: 18px;
  font-weight: bolder;
}

.cpu,
.memory,
.directory {
  border-radius: 4px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin: 0;
  font-size: 12px;

  h3 {
    margin: 0 0 12px;
    font-size: 14px;
  }

  .high-usage-text {
    font-weight: bolder;
    font-size: 30px;
  }
}

.progress {
  height: 18px;
  background: #f3f3f3;
  border-radius: 9px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-bar {
  height: 100%;
  background: #42b983;
  border-radius: 9px;
  transition: width 0.3s ease;
}

/* 使用率过高警示 */
.high-usage {
  background: #ff4d4f;
}

.echarts-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;

  .echarts-text {
    left: 0;
    font-size: 14px;
    line-height: 1.5;
  }

  .echarts-sift {
    right: 0;
  }
}

.echarts-div {
  height: 335px;
}
</style>