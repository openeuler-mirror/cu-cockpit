<template>
    <div class="box-container">
        <el-card class="box-card">
            <template #header>
                <div class="card-header">
                    <span>系统信息</span>
                </div>
            </template>
            <el-descriptions :column="2" size="large" border>
                <el-descriptions-item v-for="item in descriptions" :key="item.key">
                    <template #label>
                        <div class="cell-item">
                            {{ item.label }}
                        </div>
                    </template>
                    {{ getStateValue(item) }}
                </el-descriptions-item>
            </el-descriptions>
        </el-card>

        <el-collapse v-model="activeNames" class="margin-top">
            <el-collapse-item title="PCI" name="pci">
                <el-tooltip content="刷新" placement="bottom" effect="light" :show-arrow="false">
                    <el-button :icon="Refresh" circle size="default" type="primary" @click="getPciInfo" />
                </el-tooltip>
                <el-table :data="pciTableData" stripe size="large" v-loading="pciLoading"
                    :header-cell-style="{ background: '#f5f7fa' }">
                    <el-table-column prop="等级" label="等级" sortable min-width="300" />
                    <el-table-column prop="型号" label="型号" sortable min-width="400" />
                    <el-table-column prop="厂商" label="厂商" sortable min-width="260" />
                    <el-table-column prop="插槽" label="插槽" sortable min-width="260" />
                </el-table>
            </el-collapse-item>
            <el-collapse-item title="内存" name="memory">
                <el-tooltip content="刷新" placement="bottom" effect="light" :show-arrow="false">
                    <el-button :icon="Refresh" circle size="default" type="primary" @click="getMemoryInfo" />
                </el-tooltip>
                <el-table :data="memoryTableData" stripe size="large" v-loading="memoryLoading"
                    :header-cell-style="{ background: '#f5f7fa' }">
                    <el-table-column prop="ID" label="ID" sortable min-width="300" />
                    <el-table-column prop="内存拓扑" label="内存拓扑" sortable min-width="300" />
                    <el-table-column prop="类型" label="类型" sortable min-width="200" />
                    <el-table-column prop="大小" label="大小" sortable min-width="200" />
                    <el-table-column prop="状态" label="状态" sortable min-width="200" />
                    <el-table-column prop="Rank" label="Rank" sortable min-width="200" />
                    <el-table-column prop="速度" label="速度" sortable min-width="200" />
                </el-table>
            </el-collapse-item>
        </el-collapse>
    </div>
</template>

<script lang="ts" setup name="hardwareIndex">
import { reactive, onMounted, ref } from 'vue';
import { hardInfo, pciInfo, memorySlot } from '/@/api/run/run';
import { Refresh } from '@element-plus/icons-vue';

type SystemInfo = {
  manufacturer: string;
  product_name: string;
  serial_number: string;
  machine_num: string;
  run_time: string;
  system_model: string;
};

/** 操作系统信息类型 */
type OsSystemInfo = {
  architecture: string;
  os_name: string;
  os_version: string;
};

/** BIOS 信息类型 */
type BiosInfo = {
  vendor: string;
  version: string;
  release_date: string;
};

/** CPU 信息类型 */
type CpuInfo = {
  model: string;
  cores: number;
  vendor: string;
  cpu_info: string;
};

interface State {
  system: SystemInfo;
  os_system: OsSystemInfo;
  bios: BiosInfo;
  cpu: CpuInfo;
}

const state = reactive<State>({
  system: {
    manufacturer: '',
    product_name: '',
    serial_number: '',
    machine_num: '',
    run_time: '',
    system_model: ''
  },
  os_system: {
    architecture: '',
    os_name: '',
    os_version: ''
  },
  bios: {
    vendor: '',
    version: '',
    release_date: ''
  },
  cpu: {
    model: '',
    cores: 0,
    vendor: '',
    cpu_info: ''
  }
});

type DescriptionsItem = 
  | { type: 'system', label: string, key: keyof SystemInfo }
  | { type: 'os_system', label: string, key: keyof OsSystemInfo }
  | { type: 'bios', label: string, key: keyof BiosInfo }
  | { type: 'cpu', label: string, key: keyof CpuInfo };

const descriptions: DescriptionsItem[] = [
    { type: 'system', label: '系统型号', key: 'system_model' },
    { type: 'system', label: '机器编号', key: 'machine_num' },

    { type: 'system', label: '序列号', key: 'serial_number' },
    { type: 'cpu', label: 'CPU', key: 'cpu_info' },

    { type: 'system', label: '运行时长（自开机以来）', key: 'run_time' },
    { type: 'cpu', label: 'CPU 供应商', key: 'vendor' },

    { type: 'os_system', label: 'OS 名称', key: 'os_name' },
    { type: 'bios', label: 'BIOS', key: 'vendor' },

    { type: 'os_system', label: 'OS 架构', key: 'architecture' },
    { type: 'bios', label: 'BIOS 版本', key: 'version' },

    { type: 'os_system', label: 'OS 版本号', key: 'os_version' },
    { type: 'bios', label: 'BIOS 日期', key: 'release_date' },
];

const getStateValue = (item: DescriptionsItem): string => {
  let value: string | number | undefined;

  switch (item.type) {
    case 'system':
      value = state.system[item.key];
      break;
    case 'os_system':
      value = state.os_system[item.key];
      break;
    case 'bios':
      value = state.bios[item.key];
      break;
    case 'cpu':
      value = state.cpu[item.key];
      break;
    default:
      value = undefined;
  }

  return value != null ? String(value) : '';
};

const getHardInfo = () => {
    hardInfo('system').then((res) => {
        state.system = res.system;
        // 时间转换，系统已运行 0.61 小时
        const [prefix, hoursStr] = res.system.run_time.split(' ');
        const hours = parseFloat(hoursStr) || 0;
        let displayTime;
        if (hours >= 24) {
            const days = Math.floor(hours / 24);
            displayTime = `${prefix} ${days} 天`;
        } else {
            displayTime = res.system.run_time;
        }
        state.system.run_time = displayTime;
        state.system.system_model = res.system.manufacturer + ' ' + res.system.product_name;
    });
    hardInfo('os_system').then((res) => {
        state.os_system = res.os_system;
    });
    hardInfo('bios').then((res) => {
        state.bios = res as unknown as BiosInfo;
        // 处理 BIOS 日期格式 2020/7/22	转成 2020年07月22日
        state.bios.release_date = formatDate(state.bios.release_date);
    });
    hardInfo('cpu').then((res) => {
        state.cpu = res.cpu;
        state.cpu.cpu_info = res.cpu.cores + 'x ' + res.cpu.model;
    });
};
// 格式化日期函数
const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}年${month}月${day}日`;
};

const activeNames = ref(['pci', 'memory']);


interface PciItem {
  等级: string;
  型号: string;
  厂商: string;
  插槽: string;
}

interface MemoryItem {
  ID: string;
  内存拓扑: string;
  类型: string;
  大小: string;
  状态: string;
  Rank: string;
  速度: string;
}

const pciTableData = ref<PciItem[]>([]);
const pciLoading = ref(false);

const getPciInfo = () => {
    pciLoading.value = true;
    pciInfo().then((res: PciItem[]) => {
        pciTableData.value = res;
        pciLoading.value = false;
    });
};

const memoryTableData = ref<MemoryItem[]>([]);
const memoryLoading = ref(false);

const getMemoryInfo = () => {
    memoryLoading.value = true;
    memorySlot().then((res: MemoryItem[]) => {
        memoryTableData.value = res;
        memoryLoading.value = false;
    });
};

onMounted(() => {
    getHardInfo();
    getPciInfo();
    getMemoryInfo();
});
</script>

<style scoped lang="scss">
.box-container {
    padding: 15px 20px;

    .el-descriptions {
        ::v-deep .el-descriptions__cell {
            color: #606266;
        }

        ::v-deep .el-descriptions__label {
            width: 15%;
            font-weight: 500;
        }

        ::v-deep .el-descriptions__content {
            width: 35%;
        }
    }

    .margin-top {
        margin-top: 20px;
    }

    .cell-item {
        display: flex;
        align-items: center;
    }

    .el-collapse {
        box-shadow: var(--el-box-shadow-light);

        ::v-deep .el-collapse-item__title {
            font-size: 14px;
            color: #303133;
            padding-left: 20px;
        }

        ::v-deep .el-collapse-item__content {
            padding: 0 20px;
        }

        .el-button {
            float: right;
            margin-bottom: 10px;
        }
    }
}
</style>
