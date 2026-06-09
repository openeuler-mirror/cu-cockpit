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
</script>
<style scoped lang="scss">
</style>