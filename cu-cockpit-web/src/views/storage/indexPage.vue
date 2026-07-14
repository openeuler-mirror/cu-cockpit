<template>
    <div class="tech-storage storage-overview">
        <header class="storage-hud">
            <div class="storage-identity">
                <span class="storage-identity__mark"><i class="iconfont icon-04"></i></span>
                <div>
                    <h1 class="storage-title">存储拓扑</h1>
                    <div class="storage-kicker">STORAGE TOPOLOGY · BLOCK DEVICE INVENTORY</div>
                </div>
            </div>
            <div class="storage-hud__actions">
                <div class="storage-status" v-if="!loadError">
                    <span class="storage-status__dot"></span>
                    <span>{{ storageLoading ? '同步中' : '设备在线' }}</span>
                </div>
                <el-button class="storage-action" :icon="Refresh" :loading="storageLoading" @click="getStorageInfo">
                    刷新
                </el-button>
            </div>
        </header>

        <section class="storage-summary" aria-label="存储摘要">
            <div
                v-for="item in summaryItems"
                :key="item.label"
                class="storage-summary__item"
                :style="{ '--summary-accent': item.color }"
            >
                <span class="storage-summary__icon"><i class="iconfont" :class="item.icon"></i></span>
                <div>
                    <div class="storage-summary__label">{{ item.label }}</div>
                    <div class="storage-summary__value">{{ item.value }}</div>
                </div>
            </div>
        </section>

        <section class="storage-panel" v-loading="storageLoading">
            <div class="storage-panel__head">
                <h2 class="storage-panel__title">块设备拓扑</h2>
                <span class="storage-panel__meta">点击设备行查看完整标识与分区信息</span>
            </div>

            <div class="storage-error" v-if="loadError && !storageLoading">
                <el-icon><WarningFilled /></el-icon>
                <p>{{ loadError }}</p>
                <el-button class="storage-action" :icon="Refresh" @click="getStorageInfo">重新加载</el-button>
            </div>

            <el-table
                v-else
                :data="storageTableData"
                class="storage-table"
                row-key="name"
                default-expand-all
                :expand-row-keys="expandedRowKeys"
                size="large"
                empty-text="未检测到块设备"
                :row-class-name="storageRowClass"
                @row-click="toDetail"
            >
                <el-table-column label="设备标识" min-width="210">
                    <template #default="{ row, treeNode }">
                        <div
                            class="device-name"
                            :class="[
                                `device-name--${row.type || 'unknown'}`,
                                `device-name--level-${treeNode?.level || 0}`,
                                { 'is-root': !treeNode?.level, 'is-child': Boolean(treeNode?.level) },
                            ]"
                        >
                            <span v-if="treeNode?.level" class="device-name__branch" aria-hidden="true"></span>
                            <span class="device-name__icon"><i class="iconfont" :class="deviceIcon(row.type)"></i></span>
                            <span class="device-name__text">{{ row.name }}</span>
                        </div>
                    </template>
                </el-table-column>
                <el-table-column label="类型" width="130" class-name="storage-column--mobile-hidden">
                    <template #default="{ row }">
                        <span class="device-type">{{ typeLabel(row.type) }}</span>
                    </template>
                </el-table-column>
                <el-table-column label="挂载位置" min-width="260" class-name="storage-column--secondary">
                    <template #default="{ row }">
                        <div class="mount-state" :class="{ 'is-mounted': Boolean(row.mountpoint) }">
                            <span class="mount-state__dot"></span>
                            <span class="mount-state__path">{{ row.mountpoint || '未挂载' }}</span>
                        </div>
                    </template>
                </el-table-column>
                <el-table-column label="容量" width="130" align="right">
                    <template #default="{ row }"><span class="storage-size">{{ row.size || '—' }}</span></template>
                </el-table-column>
                <el-table-column label="" width="64" align="center" class-name="storage-column--secondary">
                    <template #default><span class="storage-detail-link"><el-icon><ArrowRight /></el-icon></span></template>
                </el-table-column>
            </el-table>
        </section>
    </div>
</template>

<script lang="ts" setup name="storageIndex">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue';
import { ArrowRight, Refresh, WarningFilled } from '@element-plus/icons-vue';
import { storeToRefs } from 'pinia';
import { useRouter } from 'vue-router';
import { hardInfo } from '/@/api/run/run';
import { useThemeConfig } from '/@/stores/themeConfig';

interface StorageDevice {
    name: string;
    type: string;
    size?: string;
    mountpoint?: string | null;
    children?: StorageDevice[];
}

const router = useRouter();
const themeStore = useThemeConfig();
const { themeConfig } = storeToRefs(themeStore);
const storageTableData = ref<StorageDevice[]>([]);
const storageLoading = ref(false);
const loadError = ref('');

const flattenDevices = (devices: StorageDevice[]): StorageDevice[] => {
    const result: StorageDevice[] = [];
    devices.forEach((device) => {
        result.push(device, ...flattenDevices(device.children || []));
    });
    return result;
};

const parseCapacity = (value?: string): number => {
    const match = value?.trim().match(/^([\d.]+)\s*([KMGTP])(?:i?B)?$/i);
    if (!match) return 0;
    const unit = match[2].toUpperCase();
    const multipliers: Record<string, number> = { K: 1 / 1024 / 1024, M: 1 / 1024, G: 1, T: 1024, P: 1024 * 1024 };
    const multiplier = multipliers[unit];
    if (!multiplier) return 0;
    return Number(match[1]) * multiplier;
};

const formatCapacity = (gigabytes: number): string => {
    if (!gigabytes) return '—';
    if (gigabytes >= 1024) return `${(gigabytes / 1024).toFixed(gigabytes >= 10240 ? 0 : 1)} TB`;
    return `${gigabytes.toFixed(gigabytes >= 100 ? 0 : 1)} GB`;
};

const storageSummary = computed(() => {
    const allDevices = flattenDevices(storageTableData.value);
    return {
        devices: storageTableData.value.length,
        volumes: Math.max(allDevices.length - storageTableData.value.length, 0),
        mounted: allDevices.filter((device) => Boolean(device.mountpoint)).length,
        capacity: formatCapacity(
            storageTableData.value.reduce((total: number, device: StorageDevice) => total + parseCapacity(device.size), 0)
        ),
    };
});

const expandedRowKeys = computed(() => flattenDevices(storageTableData.value).map((device) => device.name));
const storageRowClass = ({ row }: { row: StorageDevice }) =>
    row.type === 'disk' || row.type === 'rom' ? 'storage-row--root' : '';

const summaryItems = computed(() => [
    { label: '物理设备', value: storageSummary.value.devices, icon: 'icon-04', color: '#22d3ee' },
    { label: '分区 / 逻辑卷', value: storageSummary.value.volumes, icon: 'icon-shebeileixing', color: '#a855f7' },
    { label: '已挂载节点', value: storageSummary.value.mounted, icon: 'icon-guazaidian', color: '#10f5a0' },
    { label: '顶层设备容量', value: storageSummary.value.capacity, icon: 'icon-cunchudaxiao', color: '#ffb020' },
]);

const typeLabel = (type: string) => ({ disk: '磁盘', part: '分区', lvm: '逻辑卷', rom: '光驱' })[type] || type || '未知';
const deviceIcon = (type: string) => (type === 'part' || type === 'lvm' ? 'icon-shebeileixing' : 'icon-04');

const getStorageInfo = async () => {
    storageLoading.value = true;
    loadError.value = '';
    try {
        const response = await hardInfo('storage');
        storageTableData.value = Array.isArray(response?.blockdevices) ? response.blockdevices : [];
    } catch (error) {
        storageTableData.value = [];
        loadError.value = '存储拓扑加载失败，请检查监控服务后重试。';
        console.error('获取存储信息失败:', error);
    } finally {
        storageLoading.value = false;
    }
};

const toDetail = (row: StorageDevice) => {
    router.push({ name: 'storageDetail', params: { name: row.name } });
};

const mountStorageTechShell = () => document.documentElement.classList.add('theme-tech-dark');
const restoreStorageTechShell = () => {
    if (!themeConfig.value.isTechTheme) document.documentElement.classList.remove('theme-tech-dark');
};
const resetMainScroll = async () => {
    await nextTick();
    const scrollContainer = document.querySelector<HTMLElement>('.layout-main-scroll.el-scrollbar__wrap');
    if (scrollContainer) scrollContainer.scrollTop = 0;
};

onMounted(() => {
    mountStorageTechShell();
    resetMainScroll();
    getStorageInfo();
});

onUnmounted(restoreStorageTechShell);
</script>

<style lang="scss">
@use './tech-storage.scss';
</style>
