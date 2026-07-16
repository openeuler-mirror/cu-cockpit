<template>
    <div class="tech-hardware hardware-overview">
        <header class="hardware-hud">
            <div class="hardware-identity">
                <span class="hardware-identity__mark"><el-icon><Cpu /></el-icon></span>
                <div>
                    <h1 class="hardware-title">硬件资产</h1>
                    <div class="hardware-kicker">HARDWARE INVENTORY · SYSTEM / PCI / MEMORY</div>
                </div>
            </div>
            <div class="hardware-hud__actions">
                <div class="hardware-status" :class="{ 'is-error': hasAnyError }">
                    <span class="hardware-status__dot"></span>
                    <span>{{ hardwareLoading ? '同步中' : hasAnyError ? '部分异常' : '资产在线' }}</span>
                </div>
                <el-button class="hardware-action" :icon="Refresh" :loading="hardwareLoading" @click="getAllHardwareInfo">
                    刷新
                </el-button>
            </div>
        </header>

        <section class="hardware-summary" aria-label="硬件摘要">
            <div
                v-for="item in summaryItems"
                :key="item.label"
                class="hardware-summary__item"
                :style="{ '--summary-accent': item.color }"
            >
                <span class="hardware-summary__icon"><el-icon><component :is="item.icon" /></el-icon></span>
                <div>
                    <div class="hardware-summary__label">{{ item.label }}</div>
                    <div class="hardware-summary__value">{{ item.value }}</div>
                </div>
            </div>
        </section>

        <section class="hardware-panel" style="--panel-accent: #22d3ee" v-loading="systemLoading">
            <div class="hardware-panel__head">
                <div class="hardware-panel__identity">
                    <span class="hardware-panel__mark"><el-icon><Monitor /></el-icon></span>
                    <div>
                        <h2 class="hardware-panel__title">系统身份</h2>
                        <div class="hardware-panel__meta">SYSTEM / OS / BIOS / PROCESSOR PROFILE</div>
                    </div>
                </div>
                <div class="hardware-panel__actions">
                    <span class="hardware-panel__count"><strong>{{ descriptions.length }}</strong>项事实</span>
                    <el-button
                        class="hardware-refresh"
                        :icon="Refresh"
                        :loading="systemLoading"
                        circle
                        aria-label="刷新系统信息"
                        @click="getHardInfo"
                    />
                </div>
            </div>

            <div v-if="systemError && !systemLoading" class="hardware-error">
                <el-icon><WarningFilled /></el-icon>
                <p>{{ systemError }}</p>
                <el-button class="hardware-action" :icon="Refresh" @click="getHardInfo">重新加载</el-button>
            </div>
            <div v-else class="hardware-facts">
                <div
                    v-for="item in descriptions"
                    :key="`${item.type}-${String(item.key)}`"
                    class="hardware-fact"
                    :style="{ '--fact-accent': item.color }"
                >
                    <div class="hardware-fact__label">{{ item.label }}</div>
                    <div class="hardware-fact__value">{{ getStateValue(item) }}</div>
                </div>
            </div>
        </section>

        <section class="hardware-panel" style="--panel-accent: #a855f7">
            <div class="hardware-panel__head">
                <div class="hardware-panel__identity">
                    <span class="hardware-panel__mark"><el-icon><Connection /></el-icon></span>
                    <div>
                        <h2 class="hardware-panel__title">PCI 设备清单</h2>
                        <div class="hardware-panel__meta">PCI BUS · DEVICE / VENDOR / SLOT INVENTORY</div>
                    </div>
                </div>
                <div class="hardware-panel__actions">
                    <span class="hardware-panel__count"><strong>{{ pciTableData.length }}</strong>项设备</span>
                    <el-button
                        class="hardware-refresh"
                        :icon="Refresh"
                        :loading="pciLoading"
                        circle
                        aria-label="刷新 PCI 信息"
                        @click="getPciInfo"
                    />
                </div>
            </div>

            <div v-if="pciError && !pciLoading" class="hardware-error">
                <el-icon><WarningFilled /></el-icon>
                <p>{{ pciError }}</p>
                <el-button class="hardware-action" :icon="Refresh" @click="getPciInfo">重新加载</el-button>
            </div>
            <template v-else>
                <div class="hardware-table-tools">
                    <el-select
                        v-model="pciTypeFilter"
                        class="hardware-type-filter"
                        clearable
                        placeholder="全部设备类别"
                        popper-class="hardware-filter-popper"
                    >
                        <el-option v-for="type in pciTypeOptions" :key="type" :label="type" :value="type" />
                    </el-select>
                    <span class="hardware-table-tools__result">
                        当前 <strong>{{ filteredPciData.length }}</strong> / {{ pciTableData.length }} 项
                    </span>
                </div>
                <el-table
                v-loading="pciLoading"
                :data="pagedPciData"
                class="hardware-table"
                size="large"
                empty-text="未检测到 PCI 设备"
                >
                    <el-table-column prop="等级" label="设备类别" sortable min-width="220">
                        <template #default="{ row }"><span class="pci-grade">{{ row.等级 || '未知' }}</span></template>
                    </el-table-column>
                    <el-table-column prop="型号" label="设备型号" sortable min-width="420">
                        <template #default="{ row }"><span class="pci-model">{{ row.型号 || '—' }}</span></template>
                    </el-table-column>
                    <el-table-column prop="厂商" label="厂商" sortable min-width="250">
                        <template #default="{ row }"><span class="pci-vendor">{{ row.厂商 || '—' }}</span></template>
                    </el-table-column>
                    <el-table-column prop="插槽" label="总线地址" sortable min-width="220">
                        <template #default="{ row }"><span class="pci-slot">{{ row.插槽 || '—' }}</span></template>
                    </el-table-column>
                </el-table>
                <div v-if="filteredPciData.length" class="hardware-pagination">
                    <el-pagination
                        :current-page="pciPage"
                        :page-size="pciPageSize"
                        :page-sizes="pageSizeOptions"
                        :pager-count="5"
                        :total="filteredPciData.length"
                        layout="total, sizes, prev, pager, next"
                        @size-change="onPciPageSizeChange"
                        @current-change="pciPage = $event"
                    />
                </div>
            </template>
        </section>

        <section class="hardware-panel" style="--panel-accent: #10f5a0">
            <div class="hardware-panel__head">
                <div class="hardware-panel__identity">
                    <span class="hardware-panel__mark"><el-icon><Grid /></el-icon></span>
                    <div>
                        <h2 class="hardware-panel__title">内存插槽清单</h2>
                        <div class="hardware-panel__meta">MEMORY SLOT · CAPACITY / STATE / SPEED INVENTORY</div>
                    </div>
                </div>
                <div class="hardware-panel__actions">
                    <span class="hardware-panel__count">
                        <strong>{{ installedMemorySlots }}</strong>/ {{ memoryTableData.length }} 已安装
                    </span>
                    <el-button
                        class="hardware-refresh"
                        :icon="Refresh"
                        :loading="memoryLoading"
                        circle
                        aria-label="刷新内存信息"
                        @click="getMemoryInfo"
                    />
                </div>
            </div>

            <div v-if="memoryError && !memoryLoading" class="hardware-error">
                <el-icon><WarningFilled /></el-icon>
                <p>{{ memoryError }}</p>
                <el-button class="hardware-action" :icon="Refresh" @click="getMemoryInfo">重新加载</el-button>
            </div>
            <template v-else>
                <el-table
                v-loading="memoryLoading"
                :data="pagedMemoryData"
                class="hardware-table"
                size="large"
                empty-text="未检测到内存插槽"
                >
                    <el-table-column prop="ID" label="插槽标识" sortable min-width="210">
                        <template #default="{ row }"><span class="memory-slot-id">{{ row.ID || '—' }}</span></template>
                    </el-table-column>
                    <el-table-column prop="内存拓扑" label="拓扑位置" sortable min-width="220">
                        <template #default="{ row }"><span class="memory-topology">{{ row.内存拓扑 || '—' }}</span></template>
                    </el-table-column>
                    <el-table-column prop="类型" label="类型" sortable min-width="130">
                        <template #default="{ row }"><span class="memory-type">{{ row.类型 || '未知' }}</span></template>
                    </el-table-column>
                    <el-table-column prop="大小" label="容量" sortable min-width="190">
                        <template #default="{ row }"><span class="memory-size">{{ memorySizeLabel(row) }}</span></template>
                    </el-table-column>
                    <el-table-column prop="状态" label="状态" sortable min-width="140">
                        <template #default="{ row }">
                            <span class="memory-state" :class="memoryStateClass(row)">{{ memoryStateLabel(row) }}</span>
                        </template>
                    </el-table-column>
                    <el-table-column prop="Rank" label="Rank" sortable min-width="140">
                        <template #default="{ row }"><span class="memory-rank">{{ row.Rank || '—' }}</span></template>
                    </el-table-column>
                    <el-table-column prop="速度" label="速度" sortable min-width="150">
                        <template #default="{ row }"><span class="memory-speed">{{ row.速度 || '—' }}</span></template>
                    </el-table-column>
                </el-table>
                <div v-if="memoryTableData.length" class="hardware-pagination">
                    <el-pagination
                        :current-page="memoryPage"
                        :page-size="memoryPageSize"
                        :page-sizes="pageSizeOptions"
                        :pager-count="5"
                        :total="memoryTableData.length"
                        layout="total, sizes, prev, pager, next"
                        @size-change="onMemoryPageSizeChange"
                        @current-change="memoryPage = $event"
                    />
                </div>
            </template>
        </section>
    </div>
</template>

<script lang="ts" setup name="hardwareIndex">
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue';
import { Connection, Cpu, Grid, Monitor, Refresh, WarningFilled } from '@element-plus/icons-vue';
import { storeToRefs } from 'pinia';
import { hardInfo, memorySlot, pciInfo } from '/@/api/run/run';
import { useThemeConfig } from '/@/stores/themeConfig';

interface SystemInfo {
    manufacturer: string;
    product_name: string;
    serial_number: string;
    machine_num: string;
    run_time: string;
    system_model: string;
}

interface OsSystemInfo {
    architecture: string;
    os_name: string;
    os_version: string;
}

interface BiosInfo {
    vendor: string;
    version: string;
    release_date: string;
}

interface CpuInfo {
    model: string;
    cores: number;
    vendor: string;
    cpu_info: string;
}

interface State {
    system: SystemInfo;
    os_system: OsSystemInfo;
    bios: BiosInfo;
    cpu: CpuInfo;
}

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

type DescriptionsItem =
    | { type: 'system'; label: string; key: keyof SystemInfo; color: string }
    | { type: 'os_system'; label: string; key: keyof OsSystemInfo; color: string }
    | { type: 'bios'; label: string; key: keyof BiosInfo; color: string }
    | { type: 'cpu'; label: string; key: keyof CpuInfo; color: string };

const themeStore = useThemeConfig();
const { themeConfig } = storeToRefs(themeStore);
const state = reactive<State>({
    system: {
        manufacturer: '',
        product_name: '',
        serial_number: '',
        machine_num: '',
        run_time: '',
        system_model: '',
    },
    os_system: { architecture: '', os_name: '', os_version: '' },
    bios: { vendor: '', version: '', release_date: '' },
    cpu: { model: '', cores: 0, vendor: '', cpu_info: '' },
});

const descriptions: DescriptionsItem[] = [
    { type: 'system', label: '系统型号', key: 'system_model', color: '#22d3ee' },
    { type: 'system', label: '机器编号', key: 'machine_num', color: '#a855f7' },
    { type: 'system', label: '序列号', key: 'serial_number', color: '#10f5a0' },
    { type: 'cpu', label: 'CPU', key: 'cpu_info', color: '#ffb020' },
    { type: 'system', label: '运行时长（自开机以来）', key: 'run_time', color: '#10f5a0' },
    { type: 'cpu', label: 'CPU 供应商', key: 'vendor', color: '#22d3ee' },
    { type: 'os_system', label: 'OS 名称', key: 'os_name', color: '#3b82f6' },
    { type: 'bios', label: 'BIOS', key: 'vendor', color: '#a855f7' },
    { type: 'os_system', label: 'OS 架构', key: 'architecture', color: '#22d3ee' },
    { type: 'bios', label: 'BIOS 版本', key: 'version', color: '#ffb020' },
    { type: 'os_system', label: 'OS 版本号', key: 'os_version', color: '#3b82f6' },
    { type: 'bios', label: 'BIOS 日期', key: 'release_date', color: '#ff4d6d' },
];

const pciTableData = ref<PciItem[]>([]);
const memoryTableData = ref<MemoryItem[]>([]);
const systemLoading = ref(false);
const pciLoading = ref(false);
const memoryLoading = ref(false);
const systemError = ref('');
const pciError = ref('');
const memoryError = ref('');
const pciTypeFilter = ref('');
const pciPage = ref(1);
const pciPageSize = ref(10);
const memoryPage = ref(1);
const memoryPageSize = ref(10);
const pageSizeOptions = [10, 20, 50];

const hardwareLoading = computed(() => systemLoading.value || pciLoading.value || memoryLoading.value);
const hasAnyError = computed(() => Boolean(systemError.value || pciError.value || memoryError.value));
const isInstalledMemory = (row: MemoryItem) => row.大小 !== 'No Module Installed' && row.状态 !== '空缺';
const installedMemorySlots = computed(() => memoryTableData.value.filter(isInstalledMemory).length);
const pciTypeOptions = computed(() =>
    Array.from(new Set(pciTableData.value.map((item) => item.等级).filter(Boolean))).sort((left, right) =>
        left.localeCompare(right)
    )
);
const filteredPciData = computed(() =>
    pciTypeFilter.value ? pciTableData.value.filter((item) => item.等级 === pciTypeFilter.value) : pciTableData.value
);
const pagedPciData = computed(() => {
    const start = (pciPage.value - 1) * pciPageSize.value;
    return filteredPciData.value.slice(start, start + pciPageSize.value);
});
const pagedMemoryData = computed(() => {
    const start = (memoryPage.value - 1) * memoryPageSize.value;
    return memoryTableData.value.slice(start, start + memoryPageSize.value);
});

const summaryItems = computed(() => [
    { label: 'CPU 核心', value: state.cpu.cores || '—', icon: Cpu, color: '#22d3ee' },
    { label: 'PCI 设备', value: pciTableData.value.length, icon: Connection, color: '#a855f7' },
    { label: '内存插槽', value: memoryTableData.value.length, icon: Grid, color: '#ffb020' },
    { label: '已安装插槽', value: installedMemorySlots.value, icon: Monitor, color: '#10f5a0' },
]);

const getStateValue = (item: DescriptionsItem): string => {
    let value: string | number | undefined;
    if (item.type === 'system') value = state.system[item.key];
    if (item.type === 'os_system') value = state.os_system[item.key];
    if (item.type === 'bios') value = state.bios[item.key];
    if (item.type === 'cpu') value = state.cpu[item.key];
    return value === 0 || value ? String(value) : '—';
};

const formatRunTime = (value = ''): string => {
    const [prefix, hoursText] = value.split(' ');
    const hours = Number.parseFloat(hoursText);
    if (!Number.isFinite(hours) || hours < 24) return value;
    return `${prefix} ${Math.floor(hours / 24)} 天`;
};

const formatDate = (value = ''): string => {
    if (!value) return '';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${date.getFullYear()}年${month}月${day}日`;
};

const getHardInfo = async () => {
    systemLoading.value = true;
    systemError.value = '';
    try {
        const [systemResponse, osResponse, biosResponse, cpuResponse] = await Promise.all([
            hardInfo('system'),
            hardInfo('os_system'),
            hardInfo('bios'),
            hardInfo('cpu'),
        ]);
        const system = systemResponse?.system || {};
        Object.assign(state.system, system, {
            run_time: formatRunTime(system.run_time),
            system_model: [system.manufacturer, system.product_name].filter(Boolean).join(' '),
        });
        Object.assign(state.os_system, osResponse?.os_system || {});
        Object.assign(state.bios, biosResponse || {}, { release_date: formatDate(biosResponse?.release_date) });
        const cpu = cpuResponse?.cpu || {};
        Object.assign(state.cpu, cpu, { cpu_info: cpu.cores && cpu.model ? `${cpu.cores}x ${cpu.model}` : cpu.model || '' });
    } catch (error) {
        systemError.value = '系统身份加载失败，请检查硬件采集接口后重试。';
        console.error('获取系统硬件信息失败:', error);
    } finally {
        systemLoading.value = false;
    }
};

const getPciInfo = async () => {
    pciLoading.value = true;
    pciError.value = '';
    try {
        const response = await pciInfo();
        pciTableData.value = Array.isArray(response) ? response : [];
        pciPage.value = 1;
    } catch (error) {
        pciTableData.value = [];
        pciError.value = 'PCI 设备加载失败，请检查硬件采集接口后重试。';
        console.error('获取 PCI 信息失败:', error);
    } finally {
        pciLoading.value = false;
    }
};

const getMemoryInfo = async () => {
    memoryLoading.value = true;
    memoryError.value = '';
    try {
        const response = await memorySlot();
        memoryTableData.value = Array.isArray(response) ? response : [];
        memoryPage.value = 1;
    } catch (error) {
        memoryTableData.value = [];
        memoryError.value = '内存插槽加载失败，请检查硬件采集接口后重试。';
        console.error('获取内存信息失败:', error);
    } finally {
        memoryLoading.value = false;
    }
};

const getAllHardwareInfo = () => Promise.all([getHardInfo(), getPciInfo(), getMemoryInfo()]);
const memorySizeLabel = (row: MemoryItem) => (isInstalledMemory(row) ? row.大小 || '—' : '未安装');
const memoryStateLabel = (row: MemoryItem) => (isInstalledMemory(row) ? row.状态 || '已安装' : '空插槽');
const memoryStateClass = (row: MemoryItem) => (isInstalledMemory(row) ? 'is-installed' : 'is-empty');
const onPciPageSizeChange = (size: number) => {
    pciPageSize.value = size;
    pciPage.value = 1;
};
const onMemoryPageSizeChange = (size: number) => {
    memoryPageSize.value = size;
    memoryPage.value = 1;
};

watch(pciTypeFilter, () => {
    pciPage.value = 1;
});

const mountHardwareTechShell = () => document.documentElement.classList.add('theme-tech-dark');
const restoreHardwareTechShell = () => {
    if (!themeConfig.value.isTechTheme) document.documentElement.classList.remove('theme-tech-dark');
};
const resetMainScroll = async () => {
    await nextTick();
    const scrollContainer = document.querySelector<HTMLElement>('.layout-main-scroll.el-scrollbar__wrap');
    if (scrollContainer) scrollContainer.scrollTop = 0;
};

onMounted(() => {
    mountHardwareTechShell();
    resetMainScroll();
    getAllHardwareInfo();
});

onUnmounted(restoreHardwareTechShell);
</script>

<style lang="scss">
@use './tech-hardware.scss';
</style>